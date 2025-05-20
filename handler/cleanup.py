# Import libraries
import asyncio
import logging

# Import packages
from solders.pubkey import Pubkey
from spl.token.instructions import burn
from spl.token.instructions import BurnParams
from spl.token.instructions import close_account
from spl.token.instructions import CloseAccountParams

# Import local packages
from core.client import SolanaClient
from core.priority import PriorityFeeHandler
from core.pubkeys import SystemAddresses
from core.wallet import Wallet

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'AccountCleaner'
class AccountCleaner:
    """
    This class manages the cleanup of SPL token associated token accounts (ATAs) on the Solana blockchain.
    It can optionally burn any remaining token balance and then close the ATA to reclaim storage rent.
    Cleanup behavior is configurable, supporting both forced burning and optional use of priority fees.
    It is intended to be used post-trade, post-session, or after trade failures to prevent wallet clutter
    and free up system resources.

    Parameters:
    - client (SolanaClient): Solana RPC interface used to query and send transactions.
    - wallet (Wallet): The wallet responsible for ownership and signing cleanup transactions.
    - priority_fee_manager (PriorityFeeHandler): Manager used to calculate optional priority fees.
    - use_priority_fee (bool): Whether to apply priority fees during cleanup.
    - force_burn (bool): Whether to forcibly burn token balances before closing the ATA.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, client: SolanaClient, wallet: Wallet, priority_fee_manager: PriorityFeeHandler, use_priority_fee: bool = False, force_burn: bool = False):
        """
        Initializes the AccountCleaner instance with references to the Solana client, wallet,
        and fee manager. It sets flags that control cleanup behavior, such as whether to forcibly
        burn tokens and whether to calculate and apply priority fees when submitting the cleanup
        transactions. This setup ensures safe, configurable account management after trading.

        Parameters:
        - client (SolanaClient): A live client instance for RPC access.
        - wallet (Wallet): User’s wallet to sign and authorize account operations.
        - priority_fee_manager (PriorityFeeHandler): Handles dynamic or fixed priority fee logic.
        - use_priority_fee (bool): Enables or disables use of priority fee for cleanup.
        - force_burn (bool): Enables burning of token balances prior to ATA closure.

        Returns:
        - None
        """
        self.client = client
        self.wallet = wallet
        self.priority_fee_manager = priority_fee_manager
        self.use_priority_fee = use_priority_fee
        self.close_with_force_burn = force_burn

    # Function 'cleanup_ata'
    async def cleanup_ata(self, mint: Pubkey) -> None:
        """
        Cleans up the associated token account (ATA) for a given token mint. If the account has a
        non-zero token balance and the `force_burn` flag is enabled, it first submits a burn instruction.
        It then sends a close account instruction to remove the ATA and reclaim rent. The method
        handles RPC delays with a built-in pause and supports optional priority fee injection for faster
        confirmation. It gracefully skips already closed accounts.

        Parameters:
        - mint (Pubkey): The public key of the token mint whose ATA should be cleaned up.

        Returns:
        - None
        """
        ata = self.wallet.get_associated_token_address(mint)
        solana_client = await self.client.get_client()
        priority_fee = (
            await self.priority_fee_manager.calculate_priority_fee([ata])
            if self.use_priority_fee
            else None
        )

        logger.info("Waiting for 15 seconds for RPC node to synchronize...")
        await asyncio.sleep(15)

        try:
            info = await solana_client.get_account_info(ata, encoding="base64")
            if not info.value:
                logger.info(f"ATA {ata} does not exist or already closed.")
                return

            balance = await self.client.get_token_account_balance(ata)
            instructions = []

            if balance > 0 and self.close_with_force_burn:
                logger.info(f"Burning {balance} tokens from ATA {ata} (mint: {mint})...")
                burn_ix = burn(BurnParams(account=ata, mint=mint, owner=self.wallet.pubkey, amount=balance, program_id=SystemAddresses.TOKEN_PROGRAM))
                instructions.append(burn_ix)

            elif balance > 0:
                logger.info(f"Skipping ATA {ata} with non-zero balance ({balance} tokens) "f"because CLEANUP_FORCE_CLOSE_WITH_BURN is disabled.")
                return

            logger.info(f"Closing ATA: {ata}")
            close_ix = close_account(CloseAccountParams(account=ata, dest=self.wallet.pubkey, owner=self.wallet.pubkey, program_id=SystemAddresses.TOKEN_PROGRAM))
            instructions.append(close_ix)

            if instructions:
                tx_sig = await self.client.build_and_send_transaction(instructions, self.wallet.keypair, skip_preflight=True, priority_fee=priority_fee)
                await self.client.confirm_transaction(tx_sig)
                logger.info(f"Closed successfully: {ata}")

        except Exception as e:
            logger.warning(f"Cleanup failed for ATA {ata}: {e!s}")


# Function 'should_cleanup_after_failure'
def should_cleanup_after_failure(cleanup_mode) -> bool:
    """
    Determines if cleanup should be triggered after a failed token purchase.
    This is used to prevent accumulation of unused token accounts when a trade
    fails midway due to slippage, RPC error, or market shifts.

    Parameters:
    - cleanup_mode (str): Cleanup mode string, typically one of: "disabled", "on_fail", "after_sell", "post_session".

    Returns:
    - bool: True if cleanup mode is "on_fail", otherwise False.
    """
    return cleanup_mode == "on_fail"


# Function 'should_cleanup_after_sell'
def should_cleanup_after_sell(cleanup_mode) -> bool:
    """
    Checks whether account cleanup should occur immediately after a successful token sell operation.
    This is useful for users who want to ensure their wallet remains clean after each trade cycle,
    minimizing exposure to unused SPL accounts or rent costs.

    Parameters:
    - cleanup_mode (str): Cleanup trigger mode string.

    Returns:
    - bool: True if cleanup should follow a token sale, False otherwise.
    """
    return cleanup_mode == "after_sell"


# Function 'should_cleanup_post_session'
def should_cleanup_post_session(cleanup_mode) -> bool:
    """
    Indicates whether all account cleanup tasks should be delayed until the end of the trading session.
    This setting is typically used when batch-cleaning resources after multiple tokens have been processed,
    rather than doing so after each individual trade.

    Parameters:
    - cleanup_mode (str): The mode used to control when cleanup occurs.

    Returns:
    - bool: True if cleanup is scheduled post-session, otherwise False.
    """
    return cleanup_mode == "post_session"


# Function 'handle_cleanup_after_failure'
async def handle_cleanup_after_failure(client, wallet, mint, priority_fee_manager, cleanup_mode, cleanup_with_prior_fee, force_burn):
    """
    Handles ATA cleanup after a failed buy attempt, based on cleanup configuration.
    It initializes an `AccountCleaner` instance and invokes the cleanup operation
    if the mode is set to trigger on failure. The function is safe to call in any
    failure-handling logic and includes token burning if configured.

    Parameters:
    - client (SolanaClient): RPC client used for on-chain interaction.
    - wallet (Wallet): Wallet used to sign cleanup instructions.
    - mint (Pubkey): Token mint whose ATA should be cleaned.
    - priority_fee_manager (PriorityFeeHandler): Priority fee manager to use.
    - cleanup_mode (str): Determines when cleanup is triggered.
    - cleanup_with_prior_fee (bool): Enables priority fee usage for cleanup.
    - force_burn (bool): Enables forced burning of tokens before closure.

    Returns:
    - None
    """
    if should_cleanup_after_failure(cleanup_mode):
        logger.info("[Cleanup] Triggered by failed buy transaction.")
        manager = AccountCleanupManager(client, wallet, priority_fee_manager, cleanup_with_prior_fee, force_burn)
        await manager.cleanup_ata(mint)


# Function 'handle_cleanup_after_sell'
async def handle_cleanup_after_sell(client, wallet, mint, priority_fee_manager, cleanup_mode, cleanup_with_prior_fee, force_burn):
    """
    Triggers account cleanup after a successful token sale, depending on the agent's configuration.
    It instantiates an `AccountCleaner` with the appropriate settings and performs ATA cleanup
    if the cleanup mode is "after_sell". This helps maintain wallet hygiene after each successful cycle.

    Parameters:
    - client (SolanaClient): Client interface to the Solana RPC.
    - wallet (Wallet): Signing wallet instance.
    - mint (Pubkey): The token mint to clean up.
    - priority_fee_manager (PriorityFeeHandler): Fee manager for priority fee logic.
    - cleanup_mode (str): Cleanup mode used to trigger behavior.
    - cleanup_with_prior_fee (bool): Whether to apply priority fees.
    - force_burn (bool): Whether to burn tokens before ATA closure.

    Returns:
    - None
    """
    if should_cleanup_after_sell(cleanup_mode):
        logger.info("[Cleanup] Triggered after token sell.")
        manager = AccountCleanupManager(client, wallet, priority_fee_manager, cleanup_with_prior_fee, force_burn)
        await manager.cleanup_ata(mint)


# Function 'handle_cleanup_post_session'
async def handle_cleanup_post_session(client, wallet, mints, priority_fee_manager, cleanup_mode, cleanup_with_prior_fee, force_burn):
    """
    Initiates bulk cleanup for all traded token accounts at the end of a session. This method loops
    over each token mint and performs ATA cleanup using the configured burn and fee settings. It is
    useful for deferred cleanup strategies and helps avoid redundant cleanup operations during the
    session while preserving wallet cleanliness post-exit.

    Parameters:
    - client (SolanaClient): Solana RPC client instance.
    - wallet (Wallet): Wallet used to authorize instructions.
    - mints (list[Pubkey]): A list of token mint public keys to clean.
    - priority_fee_manager (PriorityFeeHandler): Priority fee provider.
    - cleanup_mode (str): Current cleanup strategy mode.
    - cleanup_with_prior_fee (bool): Whether to apply fees during cleanup.
    - force_burn (bool): Whether to burn before closing accounts.

    Returns:
    - None
    """
    if should_cleanup_post_session(cleanup_mode):
        logger.info("[Cleanup] Triggered post trading session.")
        manager = AccountCleanupManager(client, wallet, priority_fee_manager, cleanup_with_prior_fee, force_burn)
        for mint in mints:
            await manager.cleanup_ata(mint)