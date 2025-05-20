# Import packages
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from solders.pubkey import Pubkey


# Class 'TokenInfo'
@dataclass
class TokenInfo:
    """
    This dataclass represents metadata and on-chain references for a Pump.fun token.
    It contains all necessary information required for trade execution and filtering,
    including the token's name, symbol, mint address, bonding curve, associated bonding
    curve, and creator/user address. It also provides methods to serialize and
    deserialize the token object to and from dictionaries, facilitating easy integration
    with APIs and event listeners.

    Parameters:
    - name (str): The full name of the token.
    - symbol (str): The abbreviated symbol used for display.
    - uri (str): A URI pointing to the token’s metadata or media.
    - mint (Pubkey): The public key of the token mint account.
    - bonding_curve (Pubkey): The bonding curve account associated with the token.
    - associated_bonding_curve (Pubkey): The derived bonding curve account used in pricing.
    - user (Pubkey): The public key of the token creator or issuer.

    Returns:
    - None
    """

    # Define 'name'
    name: str

    # Define 'symbol'
    symbol: str

    # Define 'uri'
    uri: str

    # Define 'mint'
    mint: Pubkey

    # Define 'bonding_curve'
    bonding_curve: Pubkey

    # Define 'associated_bonding_curve'
    associated_bonding_curve: Pubkey

    # Define 'user'
    user: Pubkey

    # Function 'from_dict'
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenInfo":
        """
        Creates a new instance of `TokenInfo` from a dictionary, converting all string-based
        public key fields into their respective `Pubkey` types. This method is useful for
        deserializing token objects from JSON-based inputs such as WebSocket listeners, API
        responses, or storage.

        Parameters:
        - data (dict[str, Any]): A dictionary containing the keys: name, symbol, uri, mint, bondingCurve,
          associatedBondingCurve, and user, all as strings.

        Returns:
        - TokenInfo: A fully constructed TokenInfo instance with proper types.
        """
        return cls(
            name=data["name"],
            symbol=data["symbol"],
            uri=data["uri"],
            mint=Pubkey.from_string(data["mint"]),
            bonding_curve=Pubkey.from_string(data["bondingCurve"]),
            associated_bonding_curve=Pubkey.from_string(data["associatedBondingCurve"]),
            user=Pubkey.from_string(data["user"]),
        )

    # Function 'to_dict'
    def to_dict(self) -> dict[str, str]:
        """
        Serializes the `TokenInfo` instance into a dictionary of strings, converting all public key
        fields into their string representations. This is useful for logging, exporting token info
        to a human-readable format, or preparing data for transmission across external systems or
        APIs that expect JSON or flat-structured outputs.

        Parameters:
        - None

        Returns:
        - dict[str, str]: A dictionary with all values as strings, including public keys.
        """
        return {
            "name": self.name,
            "symbol": self.symbol,
            "uri": self.uri,
            "mint": str(self.mint),
            "bondingCurve": str(self.bonding_curve),
            "associatedBondingCurve": str(self.associated_bonding_curve),
            "user": str(self.user),
       }


# Class 'TradeResult'
@dataclass
class TradeResult:
    """
    This dataclass represents the outcome of a trade operation, including whether the trade succeeded,
    the transaction signature, any error message, and the final amount and price. It is returned by
    buyer or seller classes to communicate the result of a blockchain transaction attempt. This
    encapsulation enables higher-level logic to react to success/failure without manually parsing responses.

    Parameters:
    - success (bool): Indicates whether the trade was completed successfully.
    - tx_signature (str | None): The Solana transaction signature if available.
    - error_message (str | None): Error description if the trade failed.
    - amount (float | None): The number of tokens bought or sold.
    - price (float | None): The price at which the trade was executed.

    Returns:
    - None
    """
    success: bool
    tx_signature: str | None = None
    error_message: str | None = None
    amount: float | None = None
    price: float | None = None


# Class 'Trader'
class Trader(ABC):
    """
    This abstract base class defines the interface for all trade executors within the bot, including
    buyers and sellers. It enforces the implementation of an asynchronous `execute` method for
    performing token operations, while optionally including helper methods like `_get_relevant_accounts`.
    Subclasses like `TokenBuyer` and `TokenSeller` implement specific buy or sell logic based on this base.

    Parameters:
    - None (this is an abstract class)

    Returns:
    - None
    """

    # Function 'execute'
    @abstractmethod
    async def execute(self, *args, **kwargs) -> TradeResult:
        """
        Abstract method that must be implemented by all subclasses to define the logic of a trade.
        The `execute` function is expected to initiate a blockchain transaction and return a
        `TradeResult` object indicating success, failure, transaction hash, and any other relevant data.
        It must be asynchronous to allow non-blocking interaction with the Solana network.

        Parameters:
        - *args, **kwargs: Arbitrary positional and keyword arguments to support flexible subclasses.

        Returns:
        - TradeResult: The structured result of the trade execution, including status and optional metadata.
        """
        pass

    # Function '_get_relevant_accounts'
    def _get_relevant_accounts(self, token_info: TokenInfo) -> list[Pubkey]:
        """
        Internal helper that returns a list of public keys relevant to the transaction being prepared.
        This typically includes the token mint, bonding curve, the Pump.fun program, and the fee account.
        Used for fee prioritization or routing through relevant accounts when calculating dynamic fees
        or setting compute units.

        Parameters:
        - token_info (TokenInfo): The token involved in the trade for which relevant accounts are needed.

        Returns:
        - list[Pubkey]: A list of public keys required during transaction construction.
        """
        return [
            token_info.mint,                # Token mint address
            token_info.bonding_curve,       # Bonding curve address
            PumpAddresses.PROGRAM,          # Pump.fun program address
            PumpAddresses.FEE               # Pump.fun fee account
        ]