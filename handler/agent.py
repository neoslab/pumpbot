# Import libraries
import asyncio
import json
import logging
import os

# Import packages
from datetime import datetime
from datetime import UTC
from time import monotonic
from solders.pubkey import Pubkey

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
from screeners.pumpfun import PumpFunScreener
from monitoring.listeners import BlockListener
from monitoring.listeners import LogsListener

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
            sandbox: bool = False,
            initbalance: int = 10,
            maxopentrades: int = 5,

            # Monitoring
            chainlistener: str = "logs",

            # Filters
            matchstring: str | None = None,
            matchaddress: str | None = None,
            noshorting: bool = False,
            nostopping: bool = False,

            # Timing
            tokenidleinit: int = 15,
            tokenidleshort: int = 15,
            tokenidlenew: int = 15,
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
            countdown: int = 900,

            # Priority
            priodynamic: bool = False,
            priofixed: bool = True,
            priolamports: int = 200_000,
            prioextrafee: float = 0.0,
            priohardcap: int = 200_000,

            # Retries
            maxattempts: int = 3,

            # Wipe
            cleanall: str = "disabled",
            cleanburn: bool = False,
            cleanrate: bool = False,

            # Rules
            minmarketcap: float = 0.0,
            maxmarketcap: float = 0.0,
            minmarketvol: float = 0.0,
            maxmarketvol: float = 0.0,
            minholdowner: float = 0.0,
            maxholdowner: float = 0.0,
            topholders: float = 0.0,
            minholders: float = 0.0,
            maxholders: float = 0.0,
            holderscheck: bool = False,
            holdersbalance: float = 0.0,
            minliquidity: int = 3,
            maxliquidity: int = 3,
        ):
        """ Initializer description """
        # Client
        self.solanaclient = SolanaClient(rpcendpoint)

        # Main
        self.sandbox = sandbox
        self.initbalance = initbalance
        self.maxopentrades = maxopentrades

        # Wallet
        for privkey in privatekey:
            self.wallet = Wallet(privkey)
            if not self.wallet.validkey:
                self.sandbox = True

        # Monitoring
        chainlistener = chainlistener.lower()
        if chainlistener == "logs":
            self.tokenlistener = LogsListener(wssendpoint, PumpAddresses.PROGRAM)
            logger.info("Using logsSubscribe listener for token monitoring")
        else:
            self.tokenlistener = BlockListener(wssendpoint, PumpAddresses.PROGRAM)
            logger.info("Using blockSubscribe listener for token monitoring")

        # Filters
        self.matchstring = matchstring
        self.matchaddress = matchaddress
        self.noshorting = noshorting
        self.nostopping = nostopping

        # Timing
        self.tokenidleinit = tokenidleinit
        self.tokenidleshort = tokenidleshort
        self.tokenidlenew = tokenidlenew
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
        self.countdown = countdown                  # Not used

        # Curve Handler
        self.curvehandler = BondingCurveHandler(self.solanaclient)

        # Priotity Fee
        self.priorityorderfee = PriorityFeeHandler(
            client = self.solanaclient,
            enable_dynamic_fee = priodynamic,
            enable_fixed_fee = priofixed,
            fixed_fee = priolamports,
            extra_fee = prioextrafee,
            hard_cap = priohardcap
        )

        # Buyer
        if self.sandbox is False:
            self.buyer = TokenBuyer(
                self.solanaclient,
                self.wallet,
                self.curvehandler,
                self.priorityorderfee,
                buyamount,
                buyslippage,
                maxattempts,
                fasttokens,
                fastmode)

        # Seller
        if self.sandbox is False:
            self.seller = TokenSeller(
                self.solanaclient,
                self.wallet,
                self.curvehandler,
                self.priorityorderfee,
                sellslippage,
                maxattempts)

        # Cleanup parameters
        self.cleanall = cleanall
        self.cleanburn = cleanburn
        self.cleanrate = cleanrate

        # State
        self.tokenmints: set[Pubkey] = set()
        self.tokenqueue: asyncio.Queue = asyncio.Queue()
        self.tokenprocessing: set[str] = set()
        self.tokentimestamps: dict[str, float] = {}

        # Rules
        self.maxliquidity = maxliquidity            # Not used
        self.minliquidity = minliquidity            # Not used
        self.holdersbalance = holdersbalance        # Not used
        self.holderscheck = holderscheck            # Not used
        self.maxholders = maxholders                # Not used
        self.minholders = minholders                # Not used
        self.topholders = topholders                # Not used
        self.maxholdowner = maxholdowner            # Not used
        self.minholdowner = minholdowner            # Not used
        self.maxmarketvol = maxmarketvol            # Not used
        self.minmarketvol = minmarketvol            # Not used
        self.maxmarketcap = maxmarketcap            # Not used
        self.minmarketcap = minmarketcap            # Not used

    # Function 'StoreTrade'
    @staticmethod
    def StoreTrade(action: str, tokendata: TokenInfo, price: float, amount: float, tx_hash: str | None) -> None:
        """ Function description """
        try:
            os.makedirs("trades", exist_ok=True)
            logdata = {
                "timestamp": datetime.now(UTC).isoformat(),
                "action": action,
                "token": str(tokendata.mint),
                "symbol": tokendata.symbol,
                "price": price,
                "amount": amount,
                "tx": str(tx_hash) if tx_hash else None,
            }

            with open("trades/trades.log", "a") as logwrite:
                logwrite.write(json.dumps(logdata) + "\n")
        except Exception as e:
            logger.error(f"Failed to log trade information: {e!s}")

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

        listenertask = asyncio.create_task(self.tokenlistener.listen_for_tokens(TokenCallback, self.matchstring, self.matchaddress))
        try:
            logger.info(f"Waiting for a suitable token (timeout: {self.tokentimeout}s)...")
            await asyncio.wait_for(tokenfound.wait(), timeout=self.tokentimeout)

            if fetchtoken is not None:
                logger.info(f"Found token: {fetchtoken.symbol} ({fetchtoken.mint})")
                return fetchtoken
            else:
                logger.warning("Token event was set, but no token was retrieved.")
                return None

        except TimeoutError:
            logger.info(f"Timed out after waiting {self.tokentimeout}s for a token")
            return None
        finally:
            listenertask.cancel()
            try:
                await listenertask
            except asyncio.CancelledError:
                pass

    # Function 'HandleSuccessBuy'
    async def HandleSuccessBuy(self, tokendata: TokenInfo, buyresult: TradeResult) -> None:
        """ Function description """
        logger.info(f"Successfully bought {tokendata.symbol}")
        self.StoreTrade("buy", tokendata, buyresult.price, buyresult.amount, buyresult.tx_signature)
        self.tokenmints.add(tokendata.mint)

        if not self.noshorting:
            logger.info(f"Waiting for {self.tokenidleshort} seconds before selling...")
            await asyncio.sleep(self.tokenidleshort)

            logger.info(f"Selling {tokendata.symbol}...")
            sellresult: TradeResult = await self.seller.execute(tokendata)

            if sellresult.success:
                logger.info(f"Successfully sold {tokendata.symbol}")
                self.StoreTrade("sell", tokendata, sellresult.price, sellresult.amount, sellresult.tx_signature)
                handler = CleanupHandler(self.solanaclient, self.wallet, self.priorityorderfee, self.cleanall, self.cleanrate, self.cleanburn)
                await handler.handle_cleanup_after_sell(tokendata.mint)
            else:
                logger.error(f"Failed to sell {tokendata.symbol}: {sellresult.error_message}")
        else:
            logger.info("No-Shorting enabled. Skipping sell operation.")

    # Function 'HandleFailedBuy'
    async def HandleFailedBuy(self, tokendata: TokenInfo, buyresult: TradeResult) -> None:
        """ Function description """
        logger.error(f"Failed to buy {tokendata.symbol}: {buyresult.error_message}")
        handler = CleanupHandler(self.solanaclient, self.wallet, self.priorityorderfee, self.cleanall, self.cleanrate, self.cleanburn)
        await handler.handle_cleanup_after_failure(tokendata.mint)

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
        screener = PumpFunScreener()
        screener.tokenquery(str(tokendata.mint))

    # Function 'ProcessQueue'
    async def ProcessQueue(self) -> None:
        """ Function description """
        while True:
            try:
                tokendata = await self.tokenqueue.get()
                tokenkey = str(tokendata.mint)

                current_time = monotonic()
                token_age = current_time - self.tokentimestamps.get(tokenkey, current_time)

                if token_age > self.tokenmaxage:
                    logger.info(f"Skipping token {tokendata.symbol} - too old ({token_age:.1f}s > {self.tokenmaxage}s)")
                    continue

                self.tokenprocessing.add(tokenkey)
                logger.info(f"Processing fresh token: {tokendata.symbol} (age: {token_age:.1f}s)")
                if self.sandbox is False:
                    await self.HandleTokenOrder(tokendata)

            except asyncio.CancelledError:
                logger.info("Token queue processor was cancelled")
                break
            except Exception as e:
                logger.error(f"Error in token queue processor: {e!s}")
            finally:
                self.tokenqueue.task_done()

    # Function 'HandleTokenOrder'
    async def HandleTokenOrder(self, tokendata: TokenInfo) -> None:
        """ Function description """
        try:
            if not self.fastmode:
                logger.info(f"Waiting for {self.tokenidleinit} seconds for the bonding curve to stabilize...")
                await asyncio.sleep(self.tokenidleinit)

            logger.info(f"Buying {self.buyamount:.6f} SOL worth of {tokendata.symbol}...")
            buyresult: TradeResult = await self.buyer.execute(tokendata)

            if buyresult.success:
                await self.HandleSuccessBuy(tokendata, buyresult)
            else:
                await self.HandleFailedBuy(tokendata, buyresult)

            if self.nostopping:
                logger.info(f"Filter-Off enabled. Waiting {self.tokenidlenew} seconds before looking for next token...")
                await asyncio.sleep(self.tokenidlenew)

        except Exception as e:
            logger.error(f"Error handling token {tokendata.symbol}: {e!s}")

    # Function 'AgentStart'
    async def AgentStart(self) -> None:
        """ Function description """
        logger.info("Starting PumpBot agent")
        logger.info(f"Match filter: {self.matchstring if self.matchstring else 'None'}")
        logger.info(f"Creator filter: {self.matchaddress if self.matchaddress else 'None'}")
        logger.info(f"No-Shorting: {self.noshorting}")
        logger.info(f"Filter-Off: {self.nostopping}")
        logger.info(f"Max token age: {self.tokenmaxage} seconds")

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
                    if self.sandbox is False:
                        await self.HandleTokenOrder(tokendata)
                        logger.info("Finished processing single token. Exiting...")
                else:
                    logger.info(f"No suitable token found within timeout period ({self.tokentimeout}s). Exiting...")
            else:
                logger.info("Running in continuous mode - will process tokens until interrupted")
                processortask = asyncio.create_task(self.ProcessQueue())

                try:
                    await self.tokenlistener.listen_for_tokens(lambda token: self.TokenQueue(token), self.matchstring, self.matchaddress)
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