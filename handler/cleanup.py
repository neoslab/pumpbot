# Import libraries
import asyncio
import logging

# Import packages
from solders.pubkey import Pubkey
from spl.token.instructions import burn
from spl.token.instructions import BurnParams
from spl.token.instructions import close_account
from spl.token.instructions import CloseAccountParams
from typing import List

# Import local packages
from core.client import SolanaClient
from core.priority import PriorityFeeHandler
from core.pubkeys import SystemAddresses
from core.wallet import Wallet

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'AccountCleaner'
class AccountCleaner:
    """ Class description """

    # Class initialization
    def __init__(self,
            client: SolanaClient,
            wallet: Wallet,
            priority_fee_manager: PriorityFeeHandler,
            use_priority_fee: bool = False,
            force_burn: bool = False
        ):
        """ Initializer description """
        self.client = client
        self.wallet = wallet
        self.priority_fee_manager = priority_fee_manager
        self.use_priority_fee = use_priority_fee
        self.close_with_force_burn = force_burn

    # Function 'cleanup_ata'
    async def cleanup_ata(self, mint: Pubkey) -> None:
        """ Function description """
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


# Class 'CleanupHandler'
class CleanupHandler:

    # Class initialization
    def __init__(self,
            client: SolanaClient,
            wallet: Wallet,
            priority_fee_manager: PriorityFeeHandler,
            cleanup_mode: str,
            use_priority_fee: bool = False,
            force_burn: bool = False
        ):
        """ Initializer description """
        self.client = client
        self.wallet = wallet
        self.priority_fee_manager = priority_fee_manager
        self.cleanup_mode = cleanup_mode
        self.use_priority_fee = use_priority_fee
        self.force_burn = force_burn

    # Function '_perform_cleanup'
    async def _perform_cleanup(self, mint: Pubkey) -> None:
        """ Function description """
        cleaner = AccountCleaner(
            client=self.client,
            wallet=self.wallet,
            priority_fee_manager=self.priority_fee_manager,
            use_priority_fee=self.use_priority_fee,
            force_burn=self.force_burn
        )
        await cleaner.cleanup_ata(mint)

    # Function 'should_cleanup_after_failure'
    def should_cleanup_after_failure(self) -> bool:
        """ Function description """
        return self.cleanup_mode == "on_fail"

    # Function 'should_cleanup_after_sell'
    def should_cleanup_after_sell(self) -> bool:
        """ Function description """
        return self.cleanup_mode == "after_sell"

    # Function 'should_cleanup_post_session'
    def should_cleanup_post_session(self) -> bool:
        """ Function description """
        return self.cleanup_mode == "post_session"

    # Function 'handle_cleanup_after_failure'
    async def handle_cleanup_after_failure(self, mint: Pubkey) -> None:
        """ Function description """
        if self.should_cleanup_after_failure():
            logger.info("[Cleanup] Triggered by failed buy transaction.")
            await self._perform_cleanup(mint)

    # Function 'handle_cleanup_after_sell'
    async def handle_cleanup_after_sell(self, mint: Pubkey) -> None:
        """ Function description """
        if self.should_cleanup_after_sell():
            logger.info("[Cleanup] Triggered after token sell.")
            await self._perform_cleanup(mint)

    # Function 'handle_cleanup_post_session'
    async def handle_cleanup_post_session(self, mints: List[Pubkey]) -> None:
        """ Function description """
        if self.should_cleanup_post_session():
            logger.info("[Cleanup] Triggered after session ends.")
            cleaner = AccountCleaner(
                client=self.client,
                wallet=self.wallet,
                priority_fee_manager=self.priority_fee_manager,
                use_priority_fee=self.use_priority_fee,
                force_burn=self.force_burn
            )
            for mint in mints:
                await cleaner.cleanup_ata(mint)



