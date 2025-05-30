# Import libraries
import base58
import base64
import json
import logging
import os
import struct

# Import packages
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from typing import Any
from typing import Final

# Import local packages
from core.pubkeys import SystemAddresses
from handler.base import TokenInfo

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'LogsProcessor'
class LogsProcessor:
    """ Class description """

    # Define 'CREATE_DISCRIMINATOR'
    CREATE_DISCRIMINATOR: Final[int] = 8530921459188068891

    # Class initialization
    def __init__(self, pump_program: Pubkey):
        """ Initializer description """
        self.pump_program = pump_program

    # Function 'process_program_logs'
    def process_program_logs(self, logs: list[str], signature: str) -> TokenInfo | None:
        """ Function description """
        if not any("Program log: Instruction: Create" in log for log in logs):
            return None

        if any("Program log: Instruction: CreateTokenAccount" in log for log in logs):
            return None

        for log in logs:
            if "Program data:" in log:
                try:
                    encoded_data = log.split(": ")[1]
                    decoded_data = base64.b64decode(encoded_data)
                    parsed_data = self._parse_create_instruction(decoded_data)

                    if parsed_data and "name" in parsed_data:
                        mint = Pubkey.from_string(parsed_data["mint"])
                        boundingcurve = Pubkey.from_string(parsed_data["bondingCurve"])
                        associated_curve = self._find_associated_bonding_curve(
                            mint, boundingcurve
                        )

                        return TokenInfo(
                            name=parsed_data["name"],
                            symbol=parsed_data["symbol"],
                            uri=parsed_data["uri"],
                            mint=mint,
                            boundingcurve=boundingcurve,
                            basecurve=associated_curve,
                            user=Pubkey.from_string(parsed_data["user"]),
                        )
                except Exception as e:
                    logger.error(f"Failed to process log data: {e}")

        return None

    # Function '_parse_create_instruction'
    def _parse_create_instruction(self, data: bytes) -> dict | None:
        """ Function description """
        if len(data) < 8:
            return None

        discriminator = struct.unpack("<Q", data[:8])[0]
        if discriminator != self.CREATE_DISCRIMINATOR:
            logger.info(f"Skipping non-Create instruction with discriminator: {discriminator}")
            return None

        offset = 8
        parsed_data = {}

        fields = [
            ("name", "string"),
            ("symbol", "string"),
            ("uri", "string"),
            ("mint", "publicKey"),
            ("bondingCurve", "publicKey"),
            ("user", "publicKey"),
        ]

        try:
            for field_name, field_type in fields:
                value = None
                if field_type == "string":
                    length = struct.unpack("<I", data[offset: offset + 4])[0]
                    offset += 4
                    value = data[offset: offset + length].decode("utf-8")
                    offset += length
                elif field_type == "publicKey":
                    value = base58.b58encode(data[offset: offset + 32]).decode("utf-8")
                    offset += 32

                parsed_data[field_name] = value

            return parsed_data
        except Exception as e:
            logger.error(f"Failed to parse create instruction: {e}")
            return None

    # Function '_find_associated_bonding_curve'
    @staticmethod
    def _find_associated_bonding_curve(mint: Pubkey, boundingcurve: Pubkey) -> Pubkey:
        """ Function description """
        derived_address, _ = Pubkey.find_program_address(
            [
                bytes(boundingcurve),
                bytes(SystemAddresses.TOKEN_PROGRAM),
                bytes(mint),
            ],
            SystemAddresses.ASSOCIATED_TOKEN_PROGRAM,
        )
        return derived_address


# Class 'PumpProcessor'
class PumpProcessor:
    """ Class description """

    # Define 'CREATE_DISCRIMINATOR'
    CREATE_DISCRIMINATOR = 8576854823835016728

    # Class initialization
    def __init__(self, pump_program: Pubkey):
        """ Initializer description """
        self.pump_program = pump_program
        self._idl = self._load_idl()

    # Function '_load_idl'
    @staticmethod
    def _load_idl() -> dict[str, Any]:
        """ Function description """
        try:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            idl_path = os.path.join(root_dir, "global", "pumpswap.json")
            with open(idl_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load IDL: {str(e)}")
            return {
                "instructions": [
                    {
                        "name": "create",
                        "args": [
                            {"name": "name", "type": "string"},
                            {"name": "symbol", "type": "string"},
                            {"name": "uri", "type": "string"},
                        ],
                    }
                ]
            }

    # Function 'process_transaction'
    def process_transaction(self, tx_data: str) -> TokenInfo | None:
        """ Function description """
        try:
            tx_data_decoded = base64.b64decode(tx_data)
            transaction = VersionedTransaction.from_bytes(tx_data_decoded)

            for ix in transaction.message.instructions:
                program_id_index = ix.program_id_index
                if program_id_index >= len(transaction.message.account_keys):
                    continue

                program_id = transaction.message.account_keys[program_id_index]

                if str(program_id) != str(self.pump_program):
                    continue

                ix_data = bytes(ix.data)
                if len(ix_data) < 8:
                    continue

                discriminator = struct.unpack("<Q", ix_data[:8])[0]
                if discriminator != self.CREATE_DISCRIMINATOR:
                    continue

                create_ix = next(
                    (
                        instr
                        for instr in self._idl["instructions"]
                        if instr["name"] == "create"
                    ),
                    None,
                )
                if not create_ix:
                    continue

                account_keys = [
                    transaction.message.account_keys[index] for index in ix.accounts
                ]

                decoded_args = self._decode_create_instruction(
                    ix_data, create_ix, account_keys
                )

                return TokenInfo(
                    name=decoded_args["name"],
                    symbol=decoded_args["symbol"],
                    uri=decoded_args["uri"],
                    mint=Pubkey.from_string(decoded_args["mint"]),
                    boundingcurve=Pubkey.from_string(decoded_args["bondingCurve"]),
                    basecurve=Pubkey.from_string(
                        decoded_args["associatedBondingCurve"]
                    ),
                    user=Pubkey.from_string(decoded_args["user"]),
                )

        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
        return None

    # Function '_decode_create_instruction'
    @staticmethod
    def _decode_create_instruction(ix_data: bytes, ix_def: dict[str, Any], accounts: list[Pubkey]) -> dict[str, Any]:
        """ Function description """
        args = {}
        offset = 8

        for arg in ix_def["args"]:
            if arg["type"] == "string":
                length = struct.unpack_from("<I", ix_data, offset)[0]
                offset += 4
                value = ix_data[offset: offset + length].decode("utf-8")
                offset += length
            elif arg["type"] == "publicKey":
                value = base64.b64encode(ix_data[offset: offset + 32]).decode("utf-8")
                offset += 32
            else:
                logger.warning(f"Unsupported type: {arg['type']}")
                value = None

            args[arg["name"]] = value

        args["mint"] = str(accounts[0])
        args["bondingCurve"] = str(accounts[2])
        args["associatedBondingCurve"] = str(accounts[3])
        args["user"] = str(accounts[7])
        return args