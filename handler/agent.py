# Import libraries
import asyncio
import logging
import os
import requests

# Import packages
from datetime import datetime
from datetime import UTC
from decimal import Decimal
from decimal import ROUND_HALF_UP
from time import monotonic
from solders.pubkey import Pubkey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

# Import local packages
from core.client import SolanaClient
from core.curve import BondingCurveHandler
from core.priority import PriorityFeeHandler
from core.pubkeys import PumpAddresses
from core.wallet import Wallet
from handler.base import TokenInfo
from handler.base import TradeResult
from handler.buyer import TokenBuyer
from handler.cleanup import CleanupHandler
from handler.seller import TokenSeller
from monitoring.listeners import BlockListener
from monitoring.listeners import LogsListener
from utils.models import PumpBase
from utils.models import PumpTableTrades
from utils.models import PumpTableWallet
from utils.scaler import NumberScaler
from utils.scripts import ScriptUtils

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'PumpAgent'
class PumpAgent:
    """ Class description """

    # Class initialization
    def __init__(self,
        # Node
        rpcendpoint: str,
        wssendpoint: str,

        # Wallet
        privatekey: str,

        # Main
        botname: str,
        sandbox: bool = False,
        initbalance: int = 10,
        maxopentrades: int = 5,

        # Monitoring
        chainlistener: str = "logs",
        chaininterval: int = 15,

        # Filters
        matchstring: str | None = None,
        matchaddress: str | None = None,
        noshorting: bool = False,
        nostopping: bool = False,

        # Timing
        tokenidleinit: int = 15,
        tokenidleshort: int = 15,
        tokenidlefresh: int = 15,
        tokenminage: int | float = 0.001,
        tokenmaxage: int | float = 0.001,
        tokentimeout: int = 30,

        # Timing
        buyamount: float = 0.0,
        buyslippage: float = 0.0,
        sellslippage: float = 0.0,
        fastmode: bool = False,
        fasttokens: int = 15,
        stoploss: float = 0.0,
        takeprofit: float = 0.0,
        trailprofit: bool = False,
        trailone: float = 0.0,
        trailtwo: float = 0.0,
        trailthree: float = 0.0,
        trailfour: float = 0.0,
        trailfive: float = 0.0,

        # Priority
        priodynamic: bool = False,
        priofixed: bool = True,
        priolamports: int = 200_000,
        prioextrafee: float = 0.0,
        priohardcap: int = 200_000,

        # Retries
        maxattempts: int = 3,

        # Cleanup
        cleanall: str = "disabled",
        cleanburn: bool = False,
        cleanrate: bool = False,

        # Rules
        minmarketcap: int = 2,
        maxmarketcap: int = 5,
        minmarketvol: int = 2,
        maxmarketvol: int = 5,
        minholdowner: float = 0.0,
        maxholdowner: float = 0.0,
        topholders: float = 0.0,
        minholders: int = 2,
        maxholders: int = 50,
        holderscheck: bool = False,
        holdersbalance: float = 0.0,
        minliquidity: int = 2,
        maxliquidity: int = 5):
        """ Initializer description """
        # Client
        self.solanaclient = SolanaClient(rpcendpoint)

        # Wallet
        self.wallet = Wallet(privatekey)

        # Main
        self.botname = botname
        self.sandbox = sandbox
        self.maxopentrades = maxopentrades
        self.liveopentrades: set[str] = set()
        if self.sandbox is True:
            self.initbalance = initbalance
        else:
            self.initbalance = self.wallet.balance()

        # Monitoring
        chainlistener = chainlistener.lower()
        self.chaininterval = chaininterval
        if chainlistener == "logs":
            self.tokenlistener = LogsListener(wssendpoint, PumpAddresses.PROGRAM, chaininterval)
            logger.info("Using logsSubscribe listener for token monitoring")
        else:
            self.tokenlistener = BlockListener(wssendpoint, PumpAddresses.PROGRAM, chaininterval)
            logger.info("Using blockSubscribe listener for token monitoring")

        # Filters
        self.matchstring = matchstring
        self.matchaddress = matchaddress
        self.noshorting = noshorting
        self.nostopping = nostopping

        # Timing
        self.tokenidleinit = tokenidleinit
        self.tokenidleshort = tokenidleshort
        self.tokenidlefresh = tokenidlefresh
        self.tokenminage = tokenminage
        self.tokenmaxage = tokenmaxage              # Not used
        self.tokentimeout = tokentimeout

        # Trading
        self.buyamount = buyamount
        self.buyslippage = buyslippage
        self.sellslippage = sellslippage
        self.fastmode = fastmode
        self.fasttokens = fasttokens
        self.stoploss = stoploss                    # Not used
        self.takeprofit = takeprofit                # Not used
        self.trailprofit = trailprofit              # Not used
        self.trailone = trailone                    # Not used
        self.trailtwo = trailtwo                    # Not used
        self.trailthree = trailthree                # Not used
        self.trailfour = trailfour                  # Not used
        self.trailfive = trailfive                  # Not used

        # Curve Handler
        self.curvehandler = BondingCurveHandler(self.solanaclient)

        # Priotity
        self.priorityorderfee = PriorityFeeHandler(
            client = self.solanaclient,
            enable_dynamic_fee = priodynamic,
            enable_fixed_fee = priofixed,
            fixed_fee = priolamports,
            extra_fee = prioextrafee,
            hard_cap = priohardcap
        )

        # Retries
        self.maxattempts = maxattempts

        # Cleanup
        self.cleanall = cleanall
        self.cleanburn = cleanburn
        self.cleanrate = cleanrate

        # State
        self.tokenmints: set[Pubkey] = set()
        self.tokenqueue: asyncio.Queue = asyncio.Queue()
        self.tokenprocessing: set[str] = set()
        self.tokentimestamps: dict[str, float] = {}

        # Rules
        self.minmarketcap = minmarketcap            # Not used
        self.maxmarketcap = maxmarketcap            # Not used
        self.minmarketvol = minmarketvol            # Not used
        self.maxmarketvol = maxmarketvol            # Not used
        self.minholdowner = minholdowner            # Not used
        self.maxholdowner = maxholdowner            # Not used
        self.topholders = topholders                # Not used
        self.minholders = minholders                # Not used
        self.maxholders = maxholders                # Not used
        self.holderscheck = holderscheck            # Not used
        self.holdersbalance = holdersbalance        # Not used
        self.minliquidity = minliquidity            # Not used
        self.maxliquidity = maxliquidity            # Not used

        # Buyer
        self.buyer = TokenBuyer(
            self.botname,
            self.solanaclient,
            self.wallet,
            self.curvehandler,
            self.priorityorderfee,
            self.buyamount,
            self.buyslippage,
            self.maxattempts,
            self.fasttokens,
            self.fastmode,
            self.sandbox)

        # Seller
        self.seller = TokenSeller(
            self.solanaclient,
            self.wallet,
            self.curvehandler,
            self.priorityorderfee,
            self.sellslippage,
            self.maxattempts,
            self.sandbox)

        # === Define 'database' path ===
        datapathdir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # === Trades Database ===
        dbtradesdir = os.path.join(datapathdir, "database")
        os.makedirs(dbtradesdir, exist_ok=True)
        dbtradespath = os.path.join(dbtradesdir, "trades.db")
        dbtradesbase = f"sqlite:///{dbtradespath}"
        self.dbtradesengine = create_engine(dbtradesbase)
        PumpBase.metadata.create_all(self.dbtradesengine)
        self.TradesSession = sessionmaker(bind=self.dbtradesengine)

        # === Wallet Database ===
        dbwalletdir = os.path.join(datapathdir, "database")
        os.makedirs(dbtradesdir, exist_ok=True)
        dbwalletpath = os.path.join(dbwalletdir, "wallet.db")
        dbwalletbase = f"sqlite:///{dbwalletpath}"
        self.dbwalletengine = create_engine(dbwalletbase)
        PumpBase.metadata.create_all(self.dbwalletengine)
        self.WalletSession = sessionmaker(bind=self.dbwalletengine)

        # === Update Wallet Balance ===
        sessdbwallet = self.WalletSession()
        try:
            balance = sessdbwallet.query(PumpTableWallet).get(1)
            if not balance:
                balance = PumpTableWallet(id=1, balance=str(self.initbalance))
                sessdbwallet.add(balance)
                sessdbwallet.commit()
        except SQLAlchemyError:
            sessdbwallet.rollback()
        finally:
            sessdbwallet.close()

    # Function 'tokenmarket'
    @staticmethod
    def tokenmarket(mint):
        """ Function description """
        url = f"https://swap-api.pump.fun/v1/coins/{mint}/candles?interval=1s&limit=1&currency=USD"

        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            tokeninfo = r.json()
            if not tokeninfo:
                return False
            tokenprice = float(tokeninfo[0]["close"])
            return NumberScaler.showprice(tokenprice)
        except (requests.RequestException, ValueError, KeyError):
            return False

    # Function 'listen_for_tokens'
    async def openedtrades(self):
        """ Function description """
        sessdbtrades = self.TradesSession()
        nbrtrades = sessdbtrades.execute(select(func.count()).select_from(PumpTableTrades).where(PumpTableTrades.status == "OPEN")).scalar_one()
        return nbrtrades

    # Function 'StoreTrade'
    async def StoreTrade(self, action: str, tokendata: TokenInfo, price: float, amount: float, total: float, tx_hash: str | None, tradeuuid: str) -> None:
        """ Function description """
        sessdbtrades = self.TradesSession()
        sessdbwallet = self.WalletSession()
        try:
            walletrow = sessdbwallet.query(PumpTableWallet).get(1)
            if not walletrow:
                logger.error("Wallet balance not initialized. Aborting trade store.")
                return

            loadfund = Decimal(walletrow.balance)
            if action == "buy":
                walletsol = loadfund - Decimal(str(total))
                walletrow.balance = str(walletsol)

                # Save trade
                trade = PumpTableTrades(
                    uuid=str(tradeuuid),
                    start=int(datetime.now(UTC).timestamp()),
                    mint=str(tokendata.mint),
                    bot=self.botname,
                    open=NumberScaler.showprice(price),
                    amount=NumberScaler.showprice(amount),
                    total=NumberScaler.showprice(total),
                    signature=str(tx_hash) if tx_hash else None,
                    status="OPEN"
                )
                sessdbtrades.add(trade)
                sessdbtrades.commit()
                sessdbwallet.commit()
                logger.info(f"Trade recorded (BUY) and wallet updated: new balance = {walletsol} SOL")

            if action == "sell":
                trade = sessdbtrades.query(PumpTableTrades).filter_by(uuid=str(tradeuuid), status="OPEN").order_by(PumpTableTrades.start.desc()).first()
                if not trade:
                    logger.error(f"No open trade found for UUID {tradeuuid}")
                    return

                stoptime = int(datetime.now(UTC).timestamp())

                quotedprice = NumberScaler.convertdecimal(price)
                marketprice = NumberScaler.convertdecimal(trade.open)
                amount = NumberScaler.convertdecimal(trade.amount)

                countprofit = (quotedprice - marketprice) * amount
                tradeprofit = f"{countprofit:.12f}".rstrip("0").rstrip(".")

                calcratio = ((quotedprice - marketprice) / marketprice) * 100
                traderatio = f"{calcratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"

                # Update trade
                trade.stop = stoptime
                trade.duration = stoptime - trade.start
                trade.close = NumberScaler.showprice(quotedprice)
                trade.profit = NumberScaler.showprice(tradeprofit)
                trade.status = "CLOSED"
                trade.ratio = traderatio

                # Update wallet balance (add or subtract total gain/loss)
                walletsol = loadfund + (quotedprice * amount)
                walletrow.balance = str(walletsol)

                sessdbtrades.commit()
                sessdbwallet.commit()
                logger.info(f"Trade recorded (SELL) and wallet updated: new balance = {walletsol} SOL")

        except SQLAlchemyError:
            sessdbtrades.rollback()
            sessdbwallet.rollback()
            logger.error("Database error while storing trade")
        finally:
            sessdbtrades.close()
            sessdbwallet.rollback()

    # Function 'WaitForToken'
    async def WaitForToken(self) -> TokenInfo | None:
        """ Function description """
        tokenfound = asyncio.Event()
        fetchtoken: TokenInfo | None = None

        # Function 'TokenCallback'
        async def TokenCallback(token: TokenInfo) -> None:
            """ Function description """
            nonlocal fetchtoken
            tokenkey = str(token.mint)

            if tokenkey not in self.tokenprocessing:
                self.tokentimestamps[tokenkey] = monotonic()
                fetchtoken = token
                self.tokenprocessing.add(tokenkey)
                tokenfound.set()

        listenertask = asyncio.create_task(self.tokenlistener.listen_for_tokens(
            TokenCallback,
            self.maxopentrades,
            self.matchstring,
            self.matchaddress,
            self.nostopping,
            self.tokenminage,
            self.tokenmaxage,
            self.minmarketcap,
            self.maxmarketcap,
            self.minmarketvol ,
            self.maxmarketvol,
            self.minholdowner,
            self.maxholdowner,
            self.topholders,
            self.minholders,
            self.maxholders ,
            self.holderscheck,
            self.holdersbalance,
            self.minliquidity,
            self.maxliquidity))
        try:
            logger.info(f"Waiting for a suitable token (timeout: {self.tokentimeout}s)...")
            await asyncio.wait_for(tokenfound.wait(), timeout=self.tokentimeout)

        except TimeoutError:
            logger.info(f"Timed out after waiting {self.tokentimeout}s for a token")
        finally:
            listenertask.cancel()

        try:
            await listenertask
        except asyncio.CancelledError:
            pass

        if fetchtoken is not None:
            logger.info(f"Found token: {fetchtoken.symbol} ({fetchtoken.mint})")
            return fetchtoken
        else:
            logger.warning("Token event was set, but no token was retrieved.")
            return None

    # Function 'tokenswapback'
    async def tokenswapback(self, tokendata: TokenInfo, tradeuuid: str) -> None:
        """ Function description """
        logger.info(f"Selling {tokendata.symbol}...")
        sellresult: TradeResult = await self.seller.execute(tokendata)

        if sellresult.success:
            logger.info(f"Successfully sold {tokendata.symbol}")
            await self.StoreTrade("sell", tokendata, sellresult.price, sellresult.amount, sellresult.total, sellresult.tx_signature, tradeuuid)
            handler = CleanupHandler(self.solanaclient, self.wallet, self.priorityorderfee, self.cleanall, self.cleanrate, self.cleanburn)
            await handler.handle_cleanup_after_sell(tokendata.mint)
        else:
            logger.error(f"Failed to sell {tokendata.symbol}: {sellresult.error_message}")
            
    # Function 'handletransaction'
    async def handletransaction(self, tokendata: TokenInfo, buyresult: TradeResult, tradeuuid: str) -> None:
        """Handle the post-buy trade logic, including SL/TP monitoring and fallback sell after timeout."""
        logger.info(f"Successfully bought {tokendata.symbol}")

        await self.StoreTrade("buy", tokendata, buyresult.price, buyresult.amount, buyresult.total, buyresult.tx_signature, tradeuuid)
        self.tokenmints.add(tokendata.mint)

        if self.noshorting:
            logger.info(f"No-Shorting enabled. Skipping post-buy monitoring for {tokendata.symbol}")
            return

        logger.info(f"Starting dynamic SL/TP monitoring for {tokendata.symbol}...")

        try:
            entry_price = buyresult.price
            start_time = datetime.now().timestamp()
            timeout = self.tokenidleshort
            interval = 5  # seconds

            while True:

                await asyncio.sleep(interval)

                curvestate = await self.curvehandler.get_curve_state(tokendata.boundingcurve)
                current_price = curvestate.calculate_price()
                variation = ((current_price - entry_price) / entry_price) * 100

                logger.critical(f"[{tokendata.symbol}] Price variation: {variation:.2f}%")

                if variation <= -self.stoploss:
                    logger.critical(f"S/L triggered for token {tokendata.mint} ({variation:.2f}%)")
                    await self.tokenswapback(tokendata, tradeuuid)
                    break

                if variation >= self.takeprofit:
                    logger.critical(f"T/P triggered for token {tokendata.mint} ({variation:.2f}%)")
                    await self.tokenswapback(tokendata, tradeuuid)
                    break

                elapsed = datetime.now().timestamp() - start_time
                if elapsed >= timeout:
                    logger.info(f"Timeout reached ({timeout}s). Selling token {tokendata.mint}")
                    await self.tokenswapback(tokendata, tradeuuid)
                    break

        except Exception as e:
            logger.error(f"Error during SL/TP monitoring for {tokendata.symbol}: {e!s}")

    # Function 'handlefailedorder'
    async def handlefailedorder(self, tokendata: TokenInfo, buyresult: TradeResult) -> None:
        """ Function description """
        logger.error(f"Failed to buy {tokendata.symbol}: {buyresult.error_message}")
        handler = CleanupHandler(self.solanaclient, self.wallet, self.priorityorderfee, self.cleanall, self.cleanrate, self.cleanburn)
        await handler.handle_cleanup_after_failure(tokendata.mint)

    # Function 'handletokenorder'
    async def handletokenorder(self, tokendata: TokenInfo, tradeuuid: str) -> None:
        """ Function description """
        if tokendata.price is not None:
            try:
                if not self.fastmode:
                    logger.info(f"Waiting for {self.tokenidleinit} seconds for the bonding curve to stabilize...")
                    await asyncio.sleep(self.tokenidleinit)

                if len(self.liveopentrades) >= self.maxopentrades:
                    logger.warning(f"Skipping token {tokendata.symbol} - Max open trades limit ({self.maxopentrades}) reached")
                    return

                self.liveopentrades.add(tradeuuid)
                logger.info(f"Buying {self.buyamount:.6f} SOL worth of {tokendata.symbol} in the market...")
                buyresult: TradeResult = await self.buyer.execute(tokendata)
                if buyresult.success:
                    await self.handletransaction(tokendata, buyresult, tradeuuid)
                else:
                    await self.handlefailedorder(tokendata, buyresult)

                if self.nostopping:
                    logger.info(f"No-Stopping enabled. Waiting {self.tokenidlefresh} seconds before looking for next token...")
                    await asyncio.sleep(self.tokenidlefresh)

            except Exception as e:
                logger.error(f"Error handling token {tokendata.symbol}: {e!s}")

            finally:
                self.liveopentrades.discard(tradeuuid)

    # Function 'CleanupResources'
    async def CleanupResources(self) -> None:
        """ Function description """
        if self.tokenmints:
            try:
                logger.info(f"Cleaning up {len(self.tokenmints)} traded token(s)...")
                handler = CleanupHandler(self.solanaclient, self.wallet, self.priorityorderfee, self.cleanall, self.cleanrate, self.cleanburn)
                await handler.handle_cleanup_post_session(list(self.tokenmints))
            except Exception as e:
                logger.error(f"Error during cleanup: {e!s}")

        old_keys = {k for k in self.tokentimestamps if k not in self.tokenprocessing}
        for key in old_keys:
            self.tokentimestamps.pop(key, None)

        await self.solanaclient.close()

    # Function 'TokenQueue'
    async def TokenQueue(self, tokendata: TokenInfo) -> None:
        """ Function description """
        tokenkey = str(tokendata.mint)
        if tokenkey in self.tokenprocessing:
            logger.debug(f"Token {tokendata.symbol} already processed. Skipping...")
            return

        self.tokentimestamps[tokenkey] = monotonic()
        await self.tokenqueue.put(tokendata)
        logger.info(f"Queued new token: {tokendata.symbol} ({tokendata.mint})")

    # Function 'ProcessQueue'
    async def ProcessQueue(self) -> None:
        """ Function description """
        while True:
            try:
                tokendata = await self.tokenqueue.get()
                tokenkey = str(tokendata.mint)

                current_time = monotonic()
                spread = current_time - self.tokentimestamps.get(tokenkey, current_time)
                if not (self.tokenminage <= spread <= self.tokenmaxage):
                    logger.warning(f"Skipping token {tokendata.symbol} - Age {spread}s not in range [{self.tokenminage}s, {self.tokenmaxage}s]")
                    continue

                self.tokenprocessing.add(tokenkey)
                logger.info(f"Processing fresh token {tokendata.symbol} (Age: {spread:.1f}s)")
                tradeuuid = ScriptUtils.uuidgen()
                asyncio.create_task(self.handletokenorder(tokendata, tradeuuid))
                logger.info("Finished processing single token. Exiting...")

            except asyncio.CancelledError:
                logger.info("Token queue processor was cancelled")
                break
            except Exception as e:
                logger.error(f"Error in token queue processor: {e!s}")
            finally:
                self.tokenqueue.task_done()

    # Function 'agentstart'
    async def agentstart(self) -> None:
        """ Function description """
        logger.info("Starting PumpBot agent")
        logger.info(f"Match Filter: {self.matchstring if self.matchstring else 'None'}")
        logger.info(f"Match Address: {self.matchaddress if self.matchaddress else 'None'}")
        logger.info(f"No-Shorting: {self.noshorting}")
        logger.info(f"No-Stopping: {self.nostopping}")
        logger.info(f"Min. Token Age: {self.tokenminage} seconds")
        logger.info(f"Max. Token Age: {self.tokenmaxage} seconds")

        try:
            healthresp = await self.solanaclient.GetHealth()
            logger.info(f"RPC warm-up successful (getHealth passed: {healthresp})")
        except Exception as e:
            logger.warning(f"RPC warm-up failed: {e!s}")

        try:
            if not self.nostopping:
                logger.info("Running in single token mode - will process one token and exit")
                tokendata = await self.WaitForToken()
                if tokendata:
                    tradeuuid = ScriptUtils.uuidgen()
                    nbrtrades = await self.openedtrades()
                    if nbrtrades < self.maxopentrades:
                        await self.handletokenorder(tokendata, tradeuuid)
                        logger.info("Finished processing single token. Exiting...")
                    else:
                        logger.warning(f"Skipping token {tokendata.symbol} - Maximum number of {self.maxopentrades} trades reached")
                else:
                    logger.info(f"No suitable token found within timeout period ({self.tokentimeout}s). Exiting...")
            else:
                logger.info("Running in continuous mode - will process tokens until interrupted")
                processortask = asyncio.create_task(self.ProcessQueue())

                try:
                    await self.tokenlistener.listen_for_tokens(
                        lambda token: self.TokenQueue(token),
                        self.maxopentrades,
                        self.matchstring,
                        self.matchaddress,
                        self.nostopping,
                        self.tokenminage,
                        self.tokenmaxage,
                        self.minmarketcap,
                        self.maxmarketcap,
                        self.minmarketvol,
                        self.maxmarketvol,
                        self.minholdowner,
                        self.maxholdowner,
                        self.topholders,
                        self.minholders,
                        self.maxholders,
                        self.holderscheck,
                        self.holdersbalance,
                        self.minliquidity,
                        self.maxliquidity)
                except Exception as e:
                    logger.error(f"Token listening stopped due to error: {e!s}")
                finally:
                    processortask.cancel()
                    try:
                        await processortask
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            logger.error(f"Trading stopped due to error: {e!s}")

        finally:
            await self.CleanupResources()
            logger.info("Pump trader has shut down")