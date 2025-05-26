# Import packages
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from solders.pubkey import Pubkey

# Import local packages
from core.pubkeys import PumpAddresses


# Class 'TokenInfo'
@dataclass
class TokenInfo:
    """ Class description """

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
        """ Function description """
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
        """ Function description """
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
    """ Class description """
    success: bool
    tx_signature: str | None = None
    error_message: str | None = None
    amount: float | None = None
    price: float | None = None


# Class 'Trader'
class Trader(ABC):
    """ Class description """

    # Function 'execute'
    @abstractmethod
    async def execute(self, *args, **kwargs) -> TradeResult:
        """ Function description """
        pass

    # Function '_get_relevant_accounts'
    @staticmethod
    def _get_relevant_accounts(token_info: TokenInfo) -> list[Pubkey]:
        """ Function description """
        return [
            token_info.mint,                # Token mint address
            token_info.bonding_curve,       # Bonding curve address
            PumpAddresses.PROGRAM,          # Pump.fun program address
            PumpAddresses.FEE               # Pump.fun fee account
        ]