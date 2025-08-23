# Import libraries
import logging
import statistics

# Import packages
from abc import ABC
from abc import abstractmethod
from solders.pubkey import Pubkey

# Import local packages
from core.client import SolanaClient

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'PriorityFeeHandler'
class PriorityFeeHandler:
    """ Class description """

    # Class initialization
    def __init__(self, client: SolanaClient, enable_dynamic_fee: bool, enable_fixed_fee: bool, fixed_fee: int, extra_fee: float, hard_cap: int):
        """ Initializer description """
        self.client = client
        self.enable_dynamic_fee = enable_dynamic_fee
        self.enable_fixed_fee = enable_fixed_fee
        self.fixed_fee = fixed_fee
        self.extra_fee = extra_fee
        self.hard_cap = hard_cap
        self.dynamic_fee_plugin = DynamicPriorityFee(client)
        self.fixed_fee_plugin = FixedPriorityFee(fixed_fee)

    # Function 'calculate_priority_fee'
    async def calculate_priority_fee(self, accounts: list[Pubkey] | None = None) -> int | None:
        """ Function description """
        base_fee = await self._get_base_fee(accounts)
        if base_fee is None:
            return None

        final_fee = int(base_fee * (1 + self.extra_fee))
        if final_fee > self.hard_cap:
            logger.warning(f"Calculated priority fee {final_fee} exceeds hard cap {self.hard_cap}. Applying hard cap.")
            final_fee = self.hard_cap

        return final_fee

    # Function '_get_base_fee'
    async def _get_base_fee(self, accounts: list[Pubkey] | None = None) -> int | None:
        """ Function description """
        if self.enable_dynamic_fee:
            dynamic_fee = await self.dynamic_fee_plugin.get_priority_fee(accounts)
            if dynamic_fee is not None:
                return dynamic_fee

        if self.enable_fixed_fee:
            return await self.fixed_fee_plugin.get_priority_fee()

        return None


# Class 'PriorityFeePlugin'
class PriorityFeePlugin(ABC):
    """ Class description """

    # Function 'get_priority_fee'
    @abstractmethod
    async def get_priority_fee(self) -> int | None:
        """ Function description """
        pass


# Class 'DynamicPriorityFee'
class DynamicPriorityFee(PriorityFeePlugin):
    """ Class description """

    # Class initialization
    def __init__(self, client: SolanaClient):
        """ Initializer description """
        self.client = client

    # Function 'get_priority_fee'
    async def get_priority_fee(self, accounts: list[Pubkey] | None = None) -> int | None:
        """ Function description """
        try:
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getRecentPrioritizationFees",
                "params": [[str(account) for account in accounts]] if accounts else [],
            }

            response = await self.client.PostRPC(body)
            if not response or "result" not in response:
                logger.error("Failed to fetch recent prioritization fees: invalid response")
                return None

            fees = [fee["prioritizationFee"] for fee in response["result"]]
            if not fees:
                logger.warning("No prioritization fees found in the response")
                return None

            prior_fee = int(statistics.quantiles(fees, n=10)[-3])
            return prior_fee

        except Exception as e:
            logger.error(f"Failed to fetch recent priority fee: {str(e)}", exc_info=True)
            return None


# Class 'FixedPriorityFee'
class FixedPriorityFee(PriorityFeePlugin):
    """ Class description """

    # Class initialization
    def __init__(self, fixed_fee: int):
        """ Initializer description """
        self.fixed_fee = fixed_fee

    # Function 'get_priority_fee'
    async def get_priority_fee(self) -> int | None:
        """ Function description """
        if self.fixed_fee == 0:
            return None
        return self.fixed_fee