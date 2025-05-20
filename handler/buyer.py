# Import libraries
import logging
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
    """
    This class handles the execution of token purchases on Pump.fun using bonding curve mechanics.
    It calculates the expected token price, determines the optimal amount of tokens to buy based
    on slippage and capital constraints, builds the transaction with all required accounts and
    instructions, and submits it to the Solana blockchain. It supports both fast fixed-amount mode
    and curve-based pricing. Upon execution, it returns a `TradeResult` containing the outcome.

    Parameters:
    - client (SolanaClient): An initialized RPC client for network interaction.
    - wallet (Wallet): A wallet instance used to sign and submit the transaction.
    - curve_manager (BondingCurveHandler): Used to fetch and calculate dynamic pricing from the bonding curve.
    - priority_fee_manager (PriorityFeeHandler): Responsible for calculating transaction priority fees.
    - amount (float): Amount in SOL to spend on purchasing the token.
    - slippage (float): Maximum allowable slippage when buying the token.
    - max_retries (int): Maximum retries allowed for transaction submission.
    - extreme_fast_token_amount (int): If in fast mode, number of tokens to assume for fixed pricing.
    - extreme_fast_mode (bool): When enabled, bypasses curve reading for immediate pricing logic.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, client: SolanaClient, wallet: Wallet, curve_manager: BondingCurveHandler, priority_fee_manager: PriorityFeeHandler, amount: float, slippage: float = 0.01, max_retries: int = 5, extreme_fast_token_amount: int = 0, extreme_fast_mode: bool = False):
        """
        Initializes the TokenBuyer instance with required dependencies and trading parameters.
        It prepares the environment to execute buy operations on Pump.fun tokens using either
        a price-estimating bonding curve or fast mode fallback with a predefined token quantity.
        This setup allows flexible and fast trade execution while maintaining fee and retry control.

        Parameters:
        - client (SolanaClient): Client interface to interact with the Solana RPC.
        - wallet (Wallet): The trading wallet used to sign and submit transactions.
        - curve_manager (BondingCurveHandler): Provides bonding curve pricing support.
        - priority_fee_manager (PriorityFeeHandler): Priority fee calculator.
        - amount (float): Capital in SOL used to perform the purchase.
        - slippage (float): Maximum allowed slippage tolerance (default: 0.01).
        - max_retries (int): Retry count for transaction failures.
        - extreme_fast_token_amount (int): Token quantity to simulate in fast mode.
        - extreme_fast_mode (bool): Skips pricing logic and trades with fixed assumptions.

        Returns:
        - None
        """
        self.client = client
        self.wallet = wallet
        self.curve_manager = curve_manager
        self.priority_fee_manager = priority_fee_manager
        self.amount = amount
        self.slippage = slippage
        self.max_retries = max_retries
        self.extreme_fast_mode = extreme_fast_mode
        self.extreme_fast_token_amount = extreme_fast_token_amount

    # Function 'execute'
    async def execute(self, token_info: TokenInfo, *args, **kwargs) -> TradeResult:
        """
        Executes the purchase of a specified token based on configuration. If extreme fast mode is
        enabled, a fixed token quantity is used to estimate the price. Otherwise, the bonding curve
        is consulted to calculate the current token price. The function constructs a buy transaction
        using the Pump.fun protocol and submits it with the appropriate fee and retries. Confirmation
        is awaited before returning a structured `TradeResult`.

        Parameters:
        - token_info (TokenInfo): Metadata and program references for the token to buy.
        - *args, **kwargs: Reserved for compatibility with abstract `Trader.execute`.

        Returns:
        - TradeResult: Outcome of the trade, including success status, transaction signature, price, and amount.
        """
        try:
            amount_lamports = int(self.amount * LAMPORTS_PER_SOL)

            if self.extreme_fast_mode:
                token_amount = self.extreme_fast_token_amount
                token_price_sol = self.amount / token_amount
            else:
                curve_state = await self.curve_manager.get_curve_state(token_info.bonding_curve)
                token_price_sol = curve_state.calculate_price()
                token_amount = self.amount / token_price_sol

            max_amount_lamports = int(amount_lamports * (1 + self.slippage))
            associated_token_account = self.wallet.get_associated_token_address(token_info.mint)
            tx_signature = await self._send_buy_transaction(token_info, associated_token_account, token_amount, max_amount_lamports)
            logger.info(f"Buying {token_amount:.6f} tokens at {token_price_sol:.8f} SOL per token")
            logger.info(f"Total cost: {self.amount:.6f} SOL (max: {max_amount_lamports / LAMPORTS_PER_SOL:.6f} SOL)")
            success = await self.client.confirm_transaction(tx_signature)

            if success:
                logger.info(f"Buy transaction confirmed: {tx_signature}")
                return TradeResult(success=True, tx_signature=tx_signature, amount=token_amount, price=token_price_sol)
            else:
                return TradeResult(success=False, error_message=f"Transaction failed to confirm: {tx_signature}")

        except Exception as e:
            logger.error(f"Buy operation failed: {e!s}")
            return TradeResult(success=False, error_message=str(e))

    # Function '_send_buy_transaction'
    async def _send_buy_transaction(self, token_info: TokenInfo, associated_token_account: Pubkey, token_amount: float, max_amount_lamports: int) -> str:
        """
        Constructs and submits a buy transaction for a given token on Pump.fun. This includes creating
        the associated token account if needed (idempotent), preparing account metas for all required
        programs and accounts, and encoding the buy instruction with amount and price constraints.
        The function uses the priority fee manager and retries the transaction if necessary. Upon success,
        returns the Solana transaction signature.

        Parameters:
        - token_info (TokenInfo): Token metadata and address structure.
        - associated_token_account (Pubkey): Precomputed ATA for receiving tokens.
        - token_amount (float): Number of tokens to purchase.
        - max_amount_lamports (int): Maximum lamports allowed to spend including slippage.

        Returns:
        - str: Solana transaction signature of the successful submission.
        """
        accounts = [
            AccountMeta(pubkey = PumpAddresses.GLOBAL, is_signer = False, is_writable=False),
            AccountMeta(pubkey = PumpAddresses.FEE, is_signer = False, is_writable=True),
            AccountMeta(pubkey = token_info.mint, is_signer = False, is_writable=False),
            AccountMeta(pubkey = token_info.bonding_curve, is_signer = False, is_writable=True),
            AccountMeta(pubkey = token_info.associated_bonding_curve, is_signer = False, is_writable=True),
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