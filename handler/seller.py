# Import libraries
import asyncio
import base58
import logging
import os
import struct

# Import packages
from decimal import Decimal
from decimal import InvalidOperation
from typing import Final
from solders.instruction import AccountMeta
from solders.instruction import Instruction
from solders.pubkey import Pubkey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
from utils.models import PumpBase
from utils.models import PumpTableTrades

# Define 'logger'
logger = logging.getLogger(__name__)

# Define 'EXPECTED_DISCRIMINATOR'
EXPECTED_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 12502976635542562355)


# Class 'TokenSeller'
class TokenSeller(Trader):
    """ Class description """

    # Class initialization
    def __init__(self,
         client: SolanaClient,
         wallet: Wallet,
         curve_manager: BondingCurveHandler,
         priority_fee_manager: PriorityFeeHandler,
         slippage: float = 0.25,
         max_retries: int = 5,
         sandbox: bool = False):
        """ Initializer description """
        self.client = client
        self.wallet = wallet
        self.curve_manager = curve_manager
        self.priority_fee_manager = priority_fee_manager
        self.slippage = slippage
        self.max_retries = max_retries
        self.sandbox = sandbox

        # === Trades Database ===
        datapathdir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        dbtradesdir = os.path.join(datapathdir, "database")
        os.makedirs(dbtradesdir, exist_ok=True)
        dbtradespath = os.path.join(dbtradesdir, "trades.db")
        dbtradesbase = f"sqlite:///{dbtradespath}"
        self.dbtradeengine = create_engine(dbtradesbase)
        PumpBase.metadata.create_all(self.dbtradeengine)
        self.TradesSession = sessionmaker(bind=self.dbtradeengine)

    # Function 'execute'
    async def _get_token_balance_from_db(self, mint: str) -> Decimal | None:
        """ Function description """
        sessiondb = self.TradesSession()
        try:
            trade = (sessiondb.query(PumpTableTrades).filter_by(mint=mint, status="OPEN").order_by(PumpTableTrades.start.desc()).first())
            if trade and trade.amount:
                try:
                    return Decimal(trade.amount.replace(',', ''))
                except (InvalidOperation, AttributeError):
                    return None
            return None
        finally:
            sessiondb.close()

    # Function 'execute'
    async def execute(self, token_info: TokenInfo, *args, **kwargs) -> TradeResult:
        """ Function description """
        try:
            associated_token_account = self.wallet.get_associated_token_address(token_info.mint)
            if self.sandbox is False:
                token_balance = await self.client.get_token_account_balance(associated_token_account)
            else:
                token_balance = await self._get_token_balance_from_db(str(token_info.mint))

            token_balance_decimal = token_balance / 10 ** TOKEN_DECIMALS
            logger.info(f"Token balance: {token_balance_decimal}")

            if token_balance == 0:
                return TradeResult(success=False, error_message="No tokens to sell")

            curve_state = await self.curve_manager.get_curve_state(token_info.boundingcurve)
            token_price_sol = curve_state.calculate_price()
            expected_sol_output = float(token_balance_decimal) * float(token_price_sol)
            min_sol_output = int((expected_sol_output * (1 - self.slippage)) * LAMPORTS_PER_SOL)

            logger.info(f"Selling {token_balance} tokens at ~{token_price_sol:.8f} SOL each")
            logger.info(f"Expected SOL output: {expected_sol_output:.8f} | Min with slippage: {min_sol_output / LAMPORTS_PER_SOL:.8f} SOL")

            if self.sandbox is True:
                tx_signature = base58.b58encode(os.urandom(64)).decode("utf-8")
                logger.info(f"Fake sell confirmed (sandbox mode): {tx_signature}")
                await asyncio.sleep(2)
                return TradeResult(success=True, tx_signature=tx_signature, amount=token_balance, price=token_price_sol)
            else:
                tx_signature = await self._send_sell_transaction(token_info, associated_token_account, token_balance, min_sol_output)
                success = await self.client.confirm_transaction(tx_signature)
                if success:
                    return TradeResult(success=True, tx_signature=tx_signature, amount=token_balance_decimal, price=token_price_sol)
                return TradeResult(success=False, error_message="Transaction failed to confirm")

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
            AccountMeta(pubkey = token_info.boundingcurve, is_signer = False, is_writable = True),
            AccountMeta(pubkey = token_info.basecurve,is_signer = False, is_writable = True),
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