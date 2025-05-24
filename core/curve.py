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
    """
    This class represents the decoded state of a bonding curve account on the Solana blockchain.
    It parses the raw on-chain binary data using a predefined structure and exposes key values
    such as virtual reserves and total supply. The class includes helper methods for calculating
    token price and reserve balances, and validates that the binary data includes a correct discriminator.

    Parameters:
    - data (bytes): Raw binary data fetched from a Solana account, expected to follow a specific structure.

    Returns:
    - None
    """

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
        """
        Initializes the BondingCurveState instance by validating and parsing binary account data.
        It checks for the expected 8-byte discriminator and then extracts the bonding curve fields
        using a fixed structure defined by `construct.Struct`. Upon successful parsing, the instance
        dynamically sets all fields as attributes for easy access and downstream computation.

        Parameters:
        - data (bytes): Raw byte string from a Solana on-chain bonding curve account.

        Returns:
        - None
        """
        if data[:8] != EXPECTED_DISCRIMINATOR:
            raise ValueError("Invalid curve state discriminator")

        parsed = BondingCurveState.DEFSTRUCT.parse(data[8:])
        self.__dict__.update(parsed)

    # Function 'calculate_price'
    def calculate_price(self) -> float:
        """
        Calculates the current price of one token unit in SOL based on the virtual reserves.
        The price is determined by dividing the SOL reserves by the token reserves after
        adjusting for units (lamports and decimals). This function helps simulate or estimate
        token acquisition cost based on bonding curve economics.

        Parameters:
        - None

        Returns:
        - float: The computed price per token expressed in SOL.
        """
        if self.virtual_token_reserves <= 0 or self.virtual_sol_reserves <= 0:
            raise ValueError("Invalid reserve state")

        return (self.virtual_sol_reserves / LAMPORTS_PER_SOL) / (self.virtual_token_reserves / 10**TOKEN_DECIMALS)

    # Function 'token_reserves'
    @property
    def token_reserves(self) -> float:
        """
        Returns the virtual token reserves normalized using the standard number of decimals
        defined in the application (typically 6 or 9). This property is useful for analytics
        or UI display, ensuring token amounts are expressed in human-readable units.

        Parameters:
        - None

        Returns:
        - float: Token reserves in normalized decimal units.
        """
        return self.virtual_token_reserves / 10**TOKEN_DECIMALS

    # Function 'sol_reserves'
    @property
    def sol_reserves(self) -> float:
        """
        Returns the virtual SOL reserves held by the bonding curve, normalized from lamports
        to SOL units. This provides a readable format suitable for dashboards, metrics, or
        calculations involving SOL-to-token conversion.

        Parameters:
        - None

        Returns:
        - float: SOL reserves expressed in whole SOL units.
        """
        return self.virtual_sol_reserves / LAMPORTS_PER_SOL


# Class 'BondingCurveHandler'
class BondingCurveHandler:
    """
    This class provides high-level async utilities to interact with bonding curve accounts
    on the Solana blockchain. It uses a SolanaClient instance to fetch account data and
    parse it into structured state objects. Key features include fetching the curve state,
    computing token prices, and estimating token output from a given SOL input based on
    current bonding curve dynamics.

    Parameters:
    - client (SolanaClient): An initialized SolanaClient instance for performing RPC operations.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, client: SolanaClient):
        """
        Initializes the BondingCurveHandler by storing a reference to the provided SolanaClient.
        This client is later used to asynchronously fetch bonding curve account data and perform
        related operations. The handler abstracts lower-level RPC calls and provides simplified
        access to economic computations involving the bonding curve.

        Parameters:
        - client (SolanaClient): A previously configured SolanaClient instance used for blockchain access.

        Returns:
        - None
        """
        self.client = client

    # Function 'get_curve_state'
    async def get_curve_state(self, curve_address: Pubkey) -> BondingCurveState:
        """
        Asynchronously retrieves and decodes the bonding curve account data from the blockchain.
        It ensures the account contains valid data, validates it using the BondingCurveState parser,
        and returns the structured representation. If the account is invalid or empty, a detailed
        error is raised for handling by the caller.

        Parameters:
        - curve_address (Pubkey): The public key of the bonding curve account to query.

        Returns:
        - BondingCurveState: Parsed and validated bonding curve state object.
        """
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
        """
        Calculates the current price of a token on a bonding curve by fetching the curve state
        and delegating the computation to its internal logic. This is useful for market simulation,
        live pricing, or tokenomics visualization in real-time applications.

        Parameters:
        - curve_address (Pubkey): The public key of the bonding curve account.

        Returns:
        - float: The computed token price in SOL units.
        """
        curve_state = await self.get_curve_state(curve_address)
        return curve_state.calculate_price()

    # Function 'calculate_expected_tokens'
    async def calculate_expected_tokens(self, curve_address: Pubkey, sol_amount: float) -> float:
        """
        Estimates how many tokens a user would receive for a specified amount of SOL at current
        bonding curve pricing. It first fetches the curve state and computes the token price,
        then divides the input SOL by the price. This provides a simplified estimation for use
        in UIs, quoting systems, or strategy tools.

        Parameters:
        - curve_address (Pubkey): Public key of the bonding curve account.
        - sol_amount (float): Amount of SOL the user intends to spend.

        Returns:
        - float: Estimated number of tokens that would be received.
        """
        curve_state = await self.get_curve_state(curve_address)
        price = curve_state.calculate_price()
        return sol_amount / price