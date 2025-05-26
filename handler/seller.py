# Import libraries
import logging
import struct

# Import packages
from typing import Final
from solders.instruction import AccountMeta
from solders.instruction import Instruction
from solders.pubkey import Pubkey

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
EXPECTED_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 12502976635542562355)


# Class 'TokenSeller'
class TokenSeller(Trader):
    """ Class description """

    # Class initialization
    def __init__(self, client: SolanaClient, wallet: Wallet, curve_manager: BondingCurveHandler, priority_fee_manager: PriorityFeeHandler, slippage: float = 0.25, max_retries: int = 5):
        """ Initializer description """
        self.client = client
        self.wallet = wallet
        self.curve_manager = curve_manager
        self.priority_fee_manager = priority_fee_manager
        self.slippage = slippage
        self.max_retries = max_retries

    # Function 'execute'
    async def execute(self, token_info: TokenInfo, *args, **kwargs) -> TradeResult:
        """ Function description """
        try:
            associated_token_account = self.wallet.get_associated_token_address(token_info.mint)
            token_balance = await self.client.get_token_account_balance(associated_token_account)
            token_balance_decimal = token_balance / 10**TOKEN_DECIMALS
            logger.info(f"Token balance: {token_balance_decimal}")

            if token_balance == 0:
                logger.info("No tokens to sell.")
                return TradeResult(success=False, error_message="No tokens to sell")

            curve_state = await self.curve_manager.get_curve_state(token_info.bonding_curve)
            token_price_sol = curve_state.calculate_price()
            logger.info(f"Price per Token: {token_price_sol:.8f} SOL")

            amount = token_balance
            expected_sol_output = float(token_balance_decimal) * float(token_price_sol)
            slippage_factor = 1 - self.slippage
            min_sol_output = int((expected_sol_output * slippage_factor) * LAMPORTS_PER_SOL)

            logger.info(f"Selling {token_balance_decimal} tokens")
            logger.info(f"Expected SOL output: {expected_sol_output:.8f} SOL")
            logger.info(f"Minimum SOL output (with {self.slippage * 100}% slippage): {min_sol_output / LAMPORTS_PER_SOL:.8f} SOL")
            tx_signature = await self._send_sell_transaction(token_info, associated_token_account, amount, min_sol_output)
            success = await self.client.confirm_transaction(tx_signature)

            if success:
                logger.info(f"Sell transaction confirmed: {tx_signature}")
                return TradeResult(success=True, tx_signature=tx_signature, amount=token_balance_decimal, price=token_price_sol)
            else:
                return TradeResult(success=False, error_message=f"Transaction failed to confirm: {tx_signature}")

        except Exception as e:
            logger.error(f"Sell operation failed: {str(e)}")
            return TradeResult(success=False, error_message=str(e))

    # Function '_send_sell_transaction'
    async def _send_sell_transaction(self, token_info: TokenInfo, associated_token_account: Pubkey, token_amount: int, min_sol_output: int) -> str:
        """ Function description """
        accounts = [
            AccountMeta(pubkey = PumpAddresses.GLOBAL, is_signer = False, is_writable = False),
            AccountMeta(pubkey = PumpAddresses.FEE, is_signer = False, is_writable = True),
            AccountMeta(pubkey = token_info.mint, is_signer = False, is_writable = False),
            AccountMeta(pubkey = token_info.bonding_curve, is_signer = False, is_writable = True),
            AccountMeta(pubkey = token_info.associated_bonding_curve,is_signer = False, is_writable = True),
            AccountMeta(pubkey = associated_token_account, is_signer = False, is_writable = True),
            AccountMeta(pubkey = self.wallet.pubkey, is_signer = True, is_writable = True),
            AccountMeta(pubkey = SystemAddresses.PROGRAM, is_signer = False, is_writable = False),
            AccountMeta(pubkey = SystemAddresses.ASSOCIATED_TOKEN_PROGRAM, is_signer = False, is_writable = False),
            AccountMeta(pubkey = SystemAddresses.TOKEN_PROGRAM, is_signer = False, is_writable = False),
            AccountMeta(pubkey = PumpAddresses.EVENT_AUTHORITY, is_signer = False, is_writable = False),
            AccountMeta(pubkey = PumpAddresses.PROGRAM, is_signer = False, is_writable = False)
        ]

        data = (EXPECTED_DISCRIMINATOR + struct.pack("<Q", token_amount) + struct.pack("<Q", min_sol_output))
        sell_ix = Instruction(PumpAddresses.PROGRAM, data, accounts)

        try:
            return await self.client.build_and_send_transaction([sell_ix], self.wallet.keypair, skip_preflight=True, max_retries=self.max_retries, priority_fee=await self.priority_fee_manager.calculate_priority_fee(self._get_relevant_accounts(token_info)))
        except Exception as e:
            logger.error(f"Sell transaction failed: {str(e)}")
            raise