# Import libraries
import logging
import struct

# Import packages
from typing import Final
from construct import Flag
from construct import Int64ul
from construct import Struct
from solders.pubkey import Pubkey

# Import local packages
from core.client import SolanaClient
from core.pubkeys import LAMPORTS_PER_SOL
from core.pubkeys import TOKEN_DECIMALS

# Define 'logger'
logger = logging.getLogger(__name__)

# Define 'EXPECTED_DISCRIMINATOR'
EXPECTED_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 6966180631402821399)


# Class 'BondingCurveState'
class BondingCurveState:
    """ Class description """

    # Define 'DEFSTRUCT'
    DEFSTRUCT = Struct
    (
        "virtual_token_reserves" / Int64ul,
        "virtual_sol_reserves" / Int64ul,
        "real_token_reserves" / Int64ul,
        "real_sol_reserves" / Int64ul,
        "token_total_supply" / Int64ul,
        "complete" / Flag
    )

    # Class initialization
    def __init__(self, data: bytes) -> None:
        """ Initializer description """
        if data[:8] != EXPECTED_DISCRIMINATOR:
            raise ValueError("Invalid curve state discriminator")

        parsed = BondingCurveState.DEFSTRUCT.parse(data[8:])
        self.__dict__.update(parsed)

    # Function 'calculate_price'
    def calculate_price(self) -> float:
        """ Function description """
        if self.virtual_token_reserves <= 0 or self.virtual_sol_reserves <= 0:
            raise ValueError("Invalid reserve state")

        return (self.virtual_sol_reserves / LAMPORTS_PER_SOL) / (self.virtual_token_reserves / 10**TOKEN_DECIMALS)

    # Function 'token_reserves'
    @property
    def token_reserves(self) -> float:
        """ Function description """
        return self.virtual_token_reserves / 10**TOKEN_DECIMALS

    # Function 'sol_reserves'
    @property
    def sol_reserves(self) -> float:
        """ Function description """
        return self.virtual_sol_reserves / LAMPORTS_PER_SOL


# Class 'BondingCurveHandler'
class BondingCurveHandler:
    """ Class description """

    # Class initialization
    def __init__(self, client: SolanaClient):
        """ Initializer description """
        self.client = client

    # Function 'get_curve_state'
    async def get_curve_state(self, curve_address: Pubkey) -> BondingCurveState:
        """ Function description """
        try:
            account = await self.client.get_account_info(curve_address)
            if not account or not getattr(account, "data", None):
                logger.error(f"[CRITICAL] Bonding curve account {curve_address} is empty or invalid")
                raise ValueError(f"No data in bonding curve account {curve_address}")

            if not isinstance(account.data, bytes):
                logger.error(f"[CRITICAL] Unexpected type for account.data: {type(account.data)} — expected bytes")
                raise ValueError("account.data is not of type bytes")

            logger.debug(f"Fetched account: {account}")
            logger.debug(f"Type of account.data: {type(account.data)}")
            logger.debug(f"Raw data preview: {account.data[:32] if isinstance(account.data, bytes) else account.data}")

            return BondingCurveState(account.data)
        except Exception as e:
            logger.error(f"Failed to get curve state: {str(e)}")
            raise ValueError(f"Invalid curve state: {str(e)}")

    # Function 'calculate_price'
    async def calculate_price(self, curve_address: Pubkey) -> float:
        """ Function description """
        curve_state = await self.get_curve_state(curve_address)
        return curve_state.calculate_price()

    # Function 'calculate_expected_tokens'
    async def calculate_expected_tokens(self, curve_address: Pubkey, sol_amount: float) -> float:
        """ Function description """
        curve_state = await self.get_curve_state(curve_address)
        price = curve_state.calculate_price()
        return sol_amount / price