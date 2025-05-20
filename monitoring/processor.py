# Import libraries
import base58
import base64
import json
import logging
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


# Class 'GeyserProcessor'
class GeyserProcessor:
    """
    This class processes Solana transaction data intercepted from the Geyser plugin in real time.
    It parses instruction data for Pump.fun token creation events by detecting known discriminators
    and decoding associated token metadata fields such as name, symbol, URI, and account addresses.
    The processor returns a structured `TokenInfo` object if the data matches expected creation patterns.

    Parameters:
    - pump_program (Pubkey): The Pump.fun program address to validate instructions against.

    Returns:
    - None
    """

    # Define 'CREATE_DISCRIMINATOR'
    CREATE_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 8576854823835016728)

    # Class initialization
    def __init__(self, pump_program: Pubkey):
        """
        Initializes the GeyserProcessor by storing the target Pump.fun program ID. This value is used
        to validate whether decoded instructions should be processed. All token-related instructions
        must match this program before being parsed for name, symbol, URI, and other fields.

        Parameters:
        - pump_program (Pubkey): Program ID of the Pump.fun contract.

        Returns:
        - None
        """
        self.pump_program = pump_program

    # Function 'process_transaction_data'
    def process_transaction_data(self, instruction_data: bytes, accounts: list, keys: list) -> TokenInfo | None:
        """
        Parses binary instruction data from a Geyser-provided transaction event to determine if it represents
        a Pump.fun token creation. If the discriminator matches the known CREATE token instruction, the function
        attempts to extract name, symbol, uri, and relevant public keys from the encoded byte structure.

        Parameters:
        - instruction_data (bytes): Raw bytes from the Solana transaction instruction.
        - accounts (list): Indexes of accounts used in the instruction.
        - keys (list): Full list of public keys included in the transaction.

        Returns:
        - TokenInfo | None: Parsed token metadata or None if the data is invalid.
        """
        if not instruction_data.startswith(self.CREATE_DISCRIMINATOR):
            return None

        try:
            offset = 8

            # Function 'read_string'
            def read_string():
                """
                Reads a UTF-8 encoded string from the binary instruction data buffer starting at
                the current `offset` value. This function first unpacks a 4-byte little-endian integer
                representing the length of the string, then extracts the string bytes, decodes them,
                and updates the offset for subsequent reads. This method is used to parse fields like
                name, symbol, and URI in transaction instructions.

                Parameters:
                - None (uses nonlocal `offset` and global `instruction_data`)

                Returns:
                - str: The decoded UTF-8 string extracted from the instruction buffer.
                """
                nonlocal offset
                length = struct.unpack_from("<I", instruction_data, offset)[0]
                offset += 4
                value = instruction_data[offset:offset + length].decode("utf-8")
                offset += length
                return value

            # Function 'get_account_key'
            def get_account_key(index):
                """
                Retrieves a public key from the transaction's key list using an account index reference.
                This function ensures safe access by validating both the provided account index and the
                resulting key index against the respective list lengths. It returns the corresponding
                `Pubkey` if valid, or `None` if the index is out of bounds. This is commonly used to
                resolve mint, bonding curve, or user keys from compact transaction metadata.

                Parameters:
                - index (int): The index within the accounts list to resolve.

                Returns:
                - Pubkey | None: The resolved public key, or None if index is invalid.
                """
                if index >= len(accounts):
                    return None
                account_index = accounts[index]
                if account_index >= len(keys):
                    return None
                return Pubkey.from_bytes(keys[account_index])

            name = read_string()
            symbol = read_string()
            uri = read_string()

            mint = get_account_key(0)
            bonding_curve = get_account_key(2)
            associated_bonding_curve = get_account_key(3)
            user = get_account_key(7)

            if not all([mint, bonding_curve, associated_bonding_curve, user]):
                logger.warning("Missing required account keys in token creation")
                return None

            return TokenInfo(
                name=name,
                symbol=symbol,
                uri=uri,
                mint=mint,
                bonding_curve=bonding_curve,
                associated_bonding_curve=associated_bonding_curve,
                user=user,
            )

        except Exception as e:
            logger.error(f"Failed to process transaction data: {e}")
            return None


# Class 'LogsProcessor'
class LogsProcessor:
    """
    This class parses logs emitted during transaction execution on Solana to detect Pump.fun token creation.
    It identifies the presence of specific instructions via "Program log" statements and decodes base64-encoded
    instruction data embedded in those logs. This method enables token detection using the logsSubscribe
    WebSocket subscription type, without needing to decode full transactions.

    Parameters:
    - pump_program (Pubkey): The Pump.fun program ID to match against incoming logs.

    Returns:
    - None
    """

    # Define 'CREATE_DISCRIMINATOR'
    CREATE_DISCRIMINATOR: Final[int] = 8530921459188068891

    # Class initialization
    def __init__(self, pump_program: Pubkey):
        """
        Initializes the processor by storing the Pump.fun program ID for use in log or instruction validation.
        This ensures that only relevant logs or instructions belonging to the specified Pump.fun program
        are processed when parsing transaction or log data. The program ID is required to distinguish valid
        Pump.fun instructions from other on-chain activities.

        Parameters:
        - pump_program (Pubkey): The public key of the Pump.fun program to filter and verify instructions.

        Returns:
        - None
        """
        self.pump_program = pump_program

    # Function 'process_program_logs'
    def process_program_logs(self, logs: list[str], signature: str) -> TokenInfo | None:
        """
        Scans a list of logs for signs of a Pump.fun token creation instruction. If present, the method
        extracts and decodes the base64-encoded instruction data embedded in the log line and parses it
        into a `TokenInfo` object. This enables token discovery via log-level data without replaying transactions.

        Parameters:
        - logs (list[str]): A list of program logs from the Solana transaction.
        - signature (str): The transaction signature, used for identification and traceability.

        Returns:
        - TokenInfo | None: Returns token metadata if creation is detected; otherwise None.
        """
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
                        bonding_curve = Pubkey.from_string(parsed_data["bondingCurve"])
                        associated_curve = self._find_associated_bonding_curve(
                            mint, bonding_curve
                        )

                        return TokenInfo(
                            name=parsed_data["name"],
                            symbol=parsed_data["symbol"],
                            uri=parsed_data["uri"],
                            mint=mint,
                            bonding_curve=bonding_curve,
                            associated_bonding_curve=associated_curve,
                            user=Pubkey.from_string(parsed_data["user"]),
                        )
                except Exception as e:
                    logger.error(f"Failed to process log data: {e}")

        return None

    # Function '_parse_create_instruction'
    def _parse_create_instruction(self, data: bytes) -> dict | None:
        """
        Parses a raw byte buffer representing the `Create` instruction for a Pump.fun token.
        The function extracts the name, symbol, URI, and three public key values (mint, bonding curve, user)
        using offset-based decoding logic. Returns a dictionary representing the parsed structure.

        Parameters:
        - data (bytes): Instruction byte array extracted from the log.

        Returns:
        - dict | None: Dictionary of decoded values or None if the structure is invalid.
        """
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
    def _find_associated_bonding_curve(self, mint: Pubkey, bonding_curve: Pubkey) -> Pubkey:
        """
        Derives the associated bonding curve address for a token by combining the bonding curve, token
        program ID, and mint address as seeds. This ensures the address matches what Pump.fun expects
        for token routing and reserve accounting.

        Parameters:
        - mint (Pubkey): Token mint public key.
        - bonding_curve (Pubkey): Main bonding curve address.

        Returns:
        - Pubkey: The derived associated bonding curve address.
        """
        derived_address, _ = Pubkey.find_program_address(
            [
                bytes(bonding_curve),
                bytes(SystemAddresses.TOKEN_PROGRAM),
                bytes(mint),
            ],
            SystemAddresses.ASSOCIATED_TOKEN_PROGRAM,
        )
        return derived_address


# Class 'PumpProcessor'
class PumpProcessor:
    """
    This processor handles full Pump.fun transaction decoding using the Solana IDL system.
    It extracts and parses create-token instructions by decoding base64-encoded transaction blobs,
    matching known discriminators, and using IDL definitions to parse arguments. This is useful for
    structured transaction ingestion, debugging, or verifying token creation steps at runtime.

    Parameters:
    - pump_program (Pubkey): Program ID of the Pump.fun smart contract.

    Returns:
    - None
    """

    # Define 'CREATE_DISCRIMINATOR'
    CREATE_DISCRIMINATOR = 8576854823835016728

    # Class initialization
    def __init__(self, pump_program: Pubkey):
        """
        Initializes the PumpProcessor by assigning the target Pump.fun program ID and
        attempting to load the corresponding Interface Definition Language (IDL) file used
        to decode transaction instructions. The IDL provides a structured schema to interpret
        arguments passed to the `create` instruction. This setup enables decoding of Pump.fun
        transactions captured via Geyser or RPC streams.

        Parameters:
        - pump_program (Pubkey): The public key of the Pump.fun program that this processor will decode.

        Returns:
        - None
        """
        self.pump_program = pump_program
        self._idl = self._load_idl()

    # Function '_load_idl'
    def _load_idl(self) -> dict[str, Any]:
        """
        Attempts to load the Pump.fun IDL (interface definition language) file from disk.
        If the file is not found or cannot be parsed, a default minimal fallback definition
        is used. This enables dynamic decoding of transaction instructions based on field names
        and types defined in the contract specification.

        Parameters:
        - None

        Returns:
        - dict[str, Any]: Dictionary representing the IDL, used for decoding instruction arguments.
        """
        try:
            with open("idl/pump_fun_idl.json") as f:
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
        """
        Processes a base64-encoded Solana transaction string to determine if it includes a valid
        Pump.fun token creation. If a matching instruction is found and all arguments are successfully
        parsed, the method returns a `TokenInfo` object. This is a deep decoder that parses the full
        instruction from a VersionedTransaction.

        Parameters:
        - tx_data (str): Base64-encoded transaction string received from RPC or Geyser.

        Returns:
        - TokenInfo | None: Decoded token metadata if the transaction is a valid Pump.fun creation.
        """
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
                    bonding_curve=Pubkey.from_string(decoded_args["bondingCurve"]),
                    associated_bonding_curve=Pubkey.from_string(
                        decoded_args["associatedBondingCurve"]
                    ),
                    user=Pubkey.from_string(decoded_args["user"]),
                )

        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
        return None

    # Function '_decode_create_instruction'
    def _decode_create_instruction(self, ix_data: bytes, ix_def: dict[str, Any], accounts: list[Pubkey]) -> dict[str, Any]:
        """
        Decodes the arguments from a Pump.fun `create` instruction using the provided IDL definition.
        It parses each field using its declared type, extracting strings or public keys as appropriate.
        Account positions are mapped manually to mint, bonding curve, and user values to complete
        the token metadata structure.

        Parameters:
        - ix_data (bytes): Instruction bytes beginning with a discriminator.
        - ix_def (dict[str, Any]): The parsed IDL definition for the instruction.
        - accounts (list[Pubkey]): The account list used in the instruction, ordered by index.

        Returns:
        - dict[str, Any]: A dictionary containing all parsed arguments and account references.
        """
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