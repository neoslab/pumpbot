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
    """
    This class manages the calculation of Solana transaction priority fees using either
    a dynamic or fixed strategy. It determines the base fee based on recent prioritization
    data (if available) or falls back to a preconfigured fixed fee. The result is adjusted
    with an optional multiplier and capped by a hard limit. This allows flexible fee strategies
    for transaction acceleration under varying network conditions.

    Parameters:
    - client (SolanaClient): Solana client used for fetching fee data.
    - enable_dynamic_fee (bool): Whether to enable dynamic fee computation.
    - enable_fixed_fee (bool): Whether to allow fallback to a fixed fee.
    - fixed_fee (int): The static fallback priority fee in microlamports.
    - extra_fee (float): A percentage to multiply the base fee (e.g., 0.25 for +25%).
    - hard_cap (int): Maximum allowed priority fee in microlamports.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, client: SolanaClient, enable_dynamic_fee: bool, enable_fixed_fee: bool, fixed_fee: int, extra_fee: float, hard_cap: int):
        """
        Initializes the PriorityFeeHandler by injecting the SolanaClient instance and
        configuring the behavior of fee calculation with both fixed and dynamic fee strategies.
        Instantiates the required plugin objects based on the configuration and ensures future
        calls to `calculate_priority_fee` or `_get_base_fee` follow the proper logic.

        Parameters:
        - client (SolanaClient): Solana RPC interface for fee fetching.
        - enable_dynamic_fee (bool): Enables dynamic RPC-based prioritization fee estimation.
        - enable_fixed_fee (bool): Enables fallback to fixed fee logic.
        - fixed_fee (int): Value to use when falling back to fixed fee strategy.
        - extra_fee (float): Optional multiplier applied to the calculated base fee.
        - hard_cap (int): Upper bound limit to prevent excessive priority fees.

        Returns:
        - None
        """
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
        """
        Computes the final priority fee in microlamports to apply to a transaction.
        It queries for dynamic fee data if enabled, applies a multiplier based on `extra_fee`,
        and caps the result using `hard_cap`. Returns `None` if neither fee strategy is applicable
        or data retrieval fails. This method allows adaptable transaction prioritization based
        on network conditions and user preferences.

        Parameters:
        - accounts (list[Pubkey] | None): Optional list of public keys to target for fee analysis.

        Returns:
        - int | None: The final priority fee to apply, or None if not computable.
        """
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
        """
        Retrieves the raw base priority fee either from the dynamic fee plugin (via RPC)
        or a fixed value fallback. Returns `None` if both mechanisms are disabled or if
        dynamic retrieval fails. This is an internal helper method used by
        `calculate_priority_fee` to isolate the base estimation logic.

        Parameters:
        - accounts (list[Pubkey] | None): Optional list of accounts to request fee data for.

        Returns:
        - int | None: The base priority fee estimate, or None if not available.
        """
        if self.enable_dynamic_fee:
            dynamic_fee = await self.dynamic_fee_plugin.get_priority_fee(accounts)
            if dynamic_fee is not None:
                return dynamic_fee

        if self.enable_fixed_fee:
            return await self.fixed_fee_plugin.get_priority_fee()

        return None


# Class 'PriorityFeePlugin'
class PriorityFeePlugin(ABC):
    """
    This abstract base class defines a uniform interface for all priority fee plugins,
    whether dynamic or fixed. Subclasses must implement the asynchronous method
    `get_priority_fee`, which is expected to return an integer value representing
    the desired fee. This interface enables seamless switching or composition
    of multiple fee computation strategies.

    Parameters:
    - None

    Returns:
    - None
    """

    # Function 'get_priority_fee'
    @abstractmethod
    async def get_priority_fee(self) -> int | None:
        """
        Abstract method that must be implemented by subclasses to return a priority fee.
        This function represents the core API for determining how much additional fee
        to pay for prioritizing a transaction. Implementations can use fixed values,
        network analytics, or external heuristics to produce the result.

        Parameters:
        - None

        Returns:
        - int | None: The calculated priority fee in microlamports, or None if not available.
        """
        pass


# Class 'DynamicPriorityFee'
class DynamicPriorityFee(PriorityFeePlugin):
    """
    This class implements a dynamic priority fee strategy using the Solana RPC method
    `getRecentPrioritizationFees`. It fetches fee samples for recent accounts, calculates
    the 80th percentile of those samples, and returns it as the suggested fee. This approach
    adapts to network congestion and promotes competitive transaction speeds based on
    real-time data.

    Parameters:
    - client (SolanaClient): Client used to send the JSON-RPC request.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, client: SolanaClient):
        """
        Initializes the DynamicPriorityFee plugin with a reference to the Solana client
        for making JSON-RPC requests. This client will be used internally to request recent
        prioritization fee data based on the network status and optional account filters.

        Parameters:
        - client (SolanaClient): The Solana RPC client used for fee data queries.

        Returns:
        - None
        """
        self.client = client

    # Function 'get_priority_fee'
    async def get_priority_fee(self, accounts: list[Pubkey] | None = None) -> int | None:
        """
        Requests recent prioritization fee data from the Solana RPC and calculates a
        suggested priority fee based on the 80th percentile (using quantile logic).
        This helps determine a fee that is likely to be competitive enough for fast
        inclusion without overpaying. Returns None on network or data failure.

        Parameters:
        - accounts (list[Pubkey] | None): Optional list of accounts to query fee samples for.

        Returns:
        - int | None: The suggested priority fee in microlamports, or None if data is unavailable.
        """
        try:
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getRecentPrioritizationFees",
                "params": [[str(account) for account in accounts]] if accounts else [],
            }

            response = await self.client.post_rpc(body)
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
    """
    This class implements a basic plugin for returning a preconfigured static priority fee.
    It is useful when dynamic fees are unavailable, too volatile, or undesirable for the
    application. The returned fee is fixed unless explicitly changed via configuration,
    and offers maximum predictability with minimal logic.

    Parameters:
    - fixed_fee (int): The fixed fee in microlamports to apply on every transaction.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, fixed_fee: int):
        """
        Stores the provided fixed fee and prepares the plugin to serve it on demand.
        If the fee is zero, the plugin will return `None` to indicate no prioritization
        should be used. This setup is typically used in fallback configurations or
        for transactions where guaranteed inclusion is not critical.

        Parameters:
        - fixed_fee (int): The hardcoded priority fee to return when queried.

        Returns:
        - None
        """
        self.fixed_fee = fixed_fee

    # Function 'get_priority_fee'
    async def get_priority_fee(self) -> int | None:
        """
        Returns the configured static priority fee if it is greater than zero.
        This function implements the plugin interface and allows a consistent
        fallback when dynamic fees are not enabled or fail to return results.

        Parameters:
        - None

        Returns:
        - int | None: The fixed priority fee, or None if set to zero.
        """
        if self.fixed_fee == 0:
            return None
        return self.fixed_fee