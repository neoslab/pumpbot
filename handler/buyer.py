# Import libraries
import asyncio
import base58
import logging
import os
import struct

# Import packages
from solders.instruction import AccountMeta
from solders.instruction import Instruction
from solders.pubkey import Pubkey
from spl.token.instructions import create_idempotent_associated_token_account
from typing import Final

# Import local packages
from core.client import SolanaClient
from core.curve import BondingCurveHandler
from core.priority import PriorityFeeHandler
from core.pubkeys import LAMPORTS_PER_SOL
from core.pubkeys import PumpAddresses
from core.pubkeys import SystemAddresses
from core.pubkeys import TOKEN_DECIMALS
from core.wallet import Wallet
from handler.base import TokenInfo
from handler.base import Trader
from handler.base import TradeResult

# Define 'logger'
logger = logging.getLogger(__name__)

# Define 'EXPECTED_DISCRIMINATOR'
EXPECTED_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 16927863322537952870)


# Class 'TokenBuyer'
class TokenBuyer(Trader):
    """ Class description """

    # Class initialization
    def __init__(self,
        botname: str,
        client: SolanaClient,
        wallet: Wallet,
        curve_manager: BondingCurveHandler,
        priority_fee_manager: PriorityFeeHandler,
        amount: float,
        slippage: float = 0.01,
        max_retries: int = 5,
        extreme_fast_token_amount: int = 0,
        extreme_fast_mode: bool = False,
        sandbox: bool = False):
        """ Initializer description """

        # Validate wallet object
        if wallet is None or not wallet.validprikey:
            raise ValueError("Wallet or wallet.pubkey is not initialized correctly.")

        self.botname = botname
        self.client = client
        self.wallet = wallet
        self.curve_manager = curve_manager
        self.priority_fee_manager = priority_fee_manager
        self.amount = amount
        self.slippage = slippage
        self.max_retries = max_retries
        self.extreme_fast_mode = extreme_fast_mode
        self.extreme_fast_token_amount = extreme_fast_token_amount
        self.sandbox = sandbox

    # Function 'execute'
    async def execute(self, token_info: TokenInfo, *args, **kwargs) -> TradeResult:
        """ Function description """
        try:
            amount_lamports = int(self.amount * LAMPORTS_PER_SOL)
            if self.extreme_fast_mode:
                token_amount = self.extreme_fast_token_amount
                token_price_sol = self.amount / token_amount
            else:
                curve_state = await self.curve_manager.get_curve_state(token_info.boundingcurve)
                token_price_sol = curve_state.calculate_price()
                token_amount = self.amount / token_price_sol

            max_amount_lamports = int(amount_lamports * (1 + self.slippage))
            totalcost = (max_amount_lamports / LAMPORTS_PER_SOL)

            if self.sandbox is False:
                associated_token_account = self.wallet.get_associated_token_address(token_info.mint)
                tx_signature = await self._send_buy_transaction(token_info, associated_token_account, token_amount, max_amount_lamports)

            logger.info(f"Buying {token_amount:.6f} tokens at {token_price_sol:.8f} SOL per token")
            logger.info(f"Total cost: {self.amount:.6f} SOL (max: {max_amount_lamports / LAMPORTS_PER_SOL:.6f} SOL)")

            if self.sandbox is True:
                tx_signature = base58.b58encode(os.urandom(64)).decode('utf-8')
                logger.info(f"Buy transaction confirmed in sandbox mode")
                await asyncio.sleep(2)
                return TradeResult(success=True, tx_signature=tx_signature, amount=token_amount, total=totalcost, price=token_price_sol)
            else:
                success = await self.client.confirm_transaction(tx_signature)
                if success:
                    logger.info(f"Buy transaction confirmed: {tx_signature}")
                    return TradeResult(success=True, tx_signature=tx_signature, amount=token_amount, total=totalcost, price=token_price_sol)
                else:
                    return TradeResult(success=False, error_message=f"Transaction failed to confirm: {tx_signature}")

        except Exception as e:
            logger.error(f"Buy operation failed: {e!s}")
            return TradeResult(success=False, error_message=str(e))

    # Function '_send_buy_transaction'
    async def _send_buy_transaction(self, token_info: TokenInfo, associated_token_account: Pubkey, token_amount: float, max_amount_lamports: int) -> str:
        """ Function description """
        accounts = [
            AccountMeta(pubkey = PumpAddresses.GLOBAL, is_signer = False, is_writable=False),
            AccountMeta(pubkey = PumpAddresses.FEE, is_signer = False, is_writable=True),
            AccountMeta(pubkey = token_info.mint, is_signer = False, is_writable=False),
            AccountMeta(pubkey = token_info.boundingcurve, is_signer = False, is_writable=True),
            AccountMeta(pubkey = token_info.basecurve, is_signer = False, is_writable=True),
            AccountMeta(pubkey = associated_token_account, is_signer = False, is_writable=True),
            AccountMeta(pubkey = self.wallet.pubkey, is_signer = True, is_writable=True),
            AccountMeta(pubkey = SystemAddresses.PROGRAM, is_signer = False, is_writable=False),
            AccountMeta(pubkey = SystemAddresses.TOKEN_PROGRAM, is_signer = False, is_writable=False),
            AccountMeta(pubkey = SystemAddresses.RENT, is_signer = False, is_writable=False),
            AccountMeta(pubkey = PumpAddresses.EVENT_AUTHORITY, is_signer = False, is_writable=False),
            AccountMeta(pubkey = PumpAddresses.PROGRAM, is_signer = False, is_writable=False)
        ]

        idempotent_ata_ix = create_idempotent_associated_token_account(self.wallet.pubkey, self.wallet.pubkey, token_info.mint, SystemAddresses.TOKEN_PROGRAM)
        token_amount_raw = int(token_amount * 10**TOKEN_DECIMALS)
        data = (EXPECTED_DISCRIMINATOR + struct.pack("<Q", token_amount_raw) + struct.pack("<Q", max_amount_lamports))
        buy_ix = Instruction(PumpAddresses.PROGRAM, data, accounts)

        try:
            return await self.client.build_and_send_transaction([idempotent_ata_ix, buy_ix], self.wallet.keypair, skip_preflight=True, max_retries=self.max_retries, priority_fee=await self.priority_fee_manager.calculate_priority_fee(self._get_relevant_accounts(token_info)))
        except Exception as e:
            logger.error(f"Buy transaction failed: {e!s}")
            raise