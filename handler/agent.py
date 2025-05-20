# Import libraries
import asyncio
import logging

# Import local packages
from core.client import SolanaClient
from core.curve import BondingCurveHandler
from core.priority import PriorityFeeHandler
from core.pubkeys import PumpAddresses
from core.wallet import Wallet
from handler.base import TokenInfo
from handler.base import TradeResult
from handler.buyer import TokenBuyer
from handler.cleanup import handle_cleanup_after_failure
from handler.cleanup import handle_cleanup_after_sell
from handler.cleanup import handle_cleanup_post_session
from handler.seller import TokenSeller
from monitoring.listeners import BlockListener
from monitoring.listeners import GeyserListener
from monitoring.listeners import LogsListener

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'PumpAgent'
class PumpAgent:
    """
    This class implements the full lifecycle logic of an autonomous trading agent
    specifically designed for Pump.fun tokens on the Solana blockchain. It manages the entire
    process—from listening for new tokens, validating age and filters, performing buy/sell trades,
    logging results, to handling post-trade cleanup. The agent supports multiple listening
    mechanisms (Logs, Geyser, Block), advanced slippage/fee tuning, configurable retry behavior,
    and optional anti-short or continuous token mode. It integrates multiple handlers and
    components to abstract complexity and provide a robust automated strategy executor.

    Parameters:
    - rpcendpoint (str): Solana RPC endpoint used for all chain interactions.
    - wssendpoint (str): WebSocket endpoint used for logs or block subscriptions.
    - privkey (str): Base58-encoded private key used to initialize the trading wallet.

    - buyamount (float): Amount of SOL to use when buying a new token.
    - buyslippage (float): Maximum allowed slippage during token purchase.
    - sellslippage (float): Maximum allowed slippage during token sell-off.

    - fastmode (bool): Enables immediate trading without curve stabilization delay.
    - fasttokens (int): Maximum number of tokens to handle in fast mode.

    - listener (str): Type of listener to use: "logs", "geyser", or "block".
    - geyserendpoint (str | None): HTTP endpoint for Geyser listener (if selected).
    - geyserapitoken (str | None): API token used to authenticate against Geyser.
    - geyserauthtype (str): Header type for Geyser authentication (default: "x-token").

    - prioritydynenabled (bool): Enables dynamic priority fee calculation.
    - priorityfixenabled (bool): Enables fallback to a fixed priority fee.
    - prioritybaselamports (int): Base value for fixed priority fee in microlamports.
    - priorityextrafee (float): Multiplier applied to base fee (e.g. 0.25 adds 25%).
    - priorityhardcap (int): Maximum allowed fee to prevent overpaying.

    - waitaftercreation (int): Delay (in seconds) after token creation before buying.
    - waitafterbuy (int): Delay (in seconds) after buying before selling (if not noshorting).
    - waitnewtoken (int): Delay (in seconds) before evaluating the next token.
    - waittokentimeout (int): Timeout (in seconds) for waiting on a new token.
    - maxtokenage (int | float): Maximum age (in seconds) a token can be to be processed.
    - maxretries (int): Max number of retries allowed on failed trade attempts.

    - cleanupmode (str): Cleanup method used ("disabled", "burn", etc.).
    - cleanupburn (bool): Whether to burn tokens during cleanup.
    - cleanupfee (bool): Whether to use a fee token in the cleanup process.

    - matchstring (str | None): Optional filter to match token symbols or names.
    - useraddress (str | None): Optional address filter to track creator.
    - noshorting (bool): When True, prevents auto-sell after buy.
    - filteroff (bool): When True, disables token filtering and allows continuous mode.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self,
            # Connection settings
            rpcendpoint: str,
            wssendpoint: str,
            privkey: str,

            # Trade parameters
            buyamount: float,
            buyslippage: float,
            sellslippage: float,

            # Fast mode settings
            fastmode: bool = False,
            fasttokens: int = 30,

            # Listener configuration
            listener: str = "logs",

            # Geyser configuration (if applicable)
            geyserendpoint: str | None = None,
            geyserapitoken: str | None = None,
            geyserauthtype: str = "x-token",

            # Priority fee configuration
            prioritydynenabled: bool = False,
            priorityfixenabled: bool = True,
            prioritybaselamports: int = 200_000,
            priorityextrafee: float = 0.0,
            priorityhardcap: int = 200_000,

            # Retry and timeout settings
            waitaftercreation: int = 15,
            waitafterbuy: int = 15,
            waitnewtoken: int = 15,
            waittokentimeout: int = 30,
            maxtokenage: int | float = 0.001,
            maxretries: int = 3,

            # Cleanup settings
            cleanupmode: str = "disabled",
            cleanupburn: bool = False,
            cleanupfee: bool = False,

            # Trading filters
            matchstring: str | None = None,
            useraddress: str | None = None,
            noshorting: bool = False,
            filteroff: bool = False,
        ):
        """
        The initializer for the PumpAgent sets up all required subsystems, including
        the Solana client, wallet, bonding curve manager, buyer/seller handlers,
        fee controller, token listener, and trade parameter configuration. It validates
        the selected listener type and initializes it accordingly, preparing the agent
        to either wait for a token (single mode) or listen indefinitely (continuous mode).
        This sets the foundation for a fully autonomous trading session driven by real-time
        token events.

        Parameters:
        (see class docstring for full parameter list)

        Returns:
        - None
        """
        self.solanaclient = SolanaClient(rpcendpoint)
        self.wallet = Wallet(privkey)
        self.curvehandler = BondingCurveHandler(self.solanaclient)
        self.priorityorderfee = PriorityFeeHandler(client = self.solanaclient, enable_dynamic_fee = prioritydynenabled, enable_fixed_fee = priorityfixenabled, fixed_fee = prioritybaselamports, extra_fee = priorityextrafee, hard_cap = priorityhardcap)
        self.buyer = TokenBuyer(self.solanaclient, self.wallet, self.curvehandler, self.priorityorderfee, buyamount, buyslippage, maxretries, fasttokens, fastmode)
        self.seller = TokenSeller(self.solanaclient, self.wallet, self.curvehandler, self.priorityorderfee, sellslippage, maxretries)

        # Initialize the appropriate listener type
        listener = listener.lower()
        if listener == "geyser":
            if not geyserendpoint or not geyserapitoken:
                raise ValueError("Geyser endpoint and API token are required for geyser listener")

            self.token_listener = GeyserListener(
                geyserendpoint,
                geyserapitoken,
                geyserauthtype,
                PumpAddresses.PROGRAM
            )
            logger.info("Using Geyser listener for token monitoring")
        elif listener == "logs":
            self.token_listener = LogsListener(wssendpoint, PumpAddresses.PROGRAM)
            logger.info("Using logsSubscribe listener for token monitoring")
        else:
            self.token_listener = BlockListener(wssendpoint, PumpAddresses.PROGRAM)
            logger.info("Using blockSubscribe listener for token monitoring")

        # Trading parameters
        self.buyamount = buyamount
        self.buyslippage = buyslippage
        self.sellslippage = sellslippage
        self.maxretries = maxretries
        self.fastmode = fastmode
        self.fasttokens = fasttokens

        # Timing parameters
        self.waitaftercreation = waitaftercreation
        self.waitafterbuy = waitafterbuy
        self.waitnewtoken = waitnewtoken
        self.maxtokenage = maxtokenage
        self.waittokentimeout = waittokentimeout

        # Cleanup parameters
        self.cleanupmode = cleanupmode
        self.cleanupburn = cleanupburn
        self.cleanupfee = cleanupfee

        # Trading filters/modes
        self.matchstring = matchstring
        self.useraddress = useraddress
        self.noshorting = noshorting
        self.filteroff = filteroff

        # State tracking
        self.tradedmints: set[Pubkey] = set()
        self.tokenqueue: asyncio.Queue = asyncio.Queue()
        self.processedtokens: set[str] = set()
        self.tokentimestamps: dict[str, float] = {}

    # Function 'StoreTrade'
    def StoreTrade(self, action: str, tokendata: TokenInfo, price: float, amount: float, tx_hash: str | None) -> None:
        """
        Logs trade information to a file for historical tracking and auditing purposes. This method
        creates a log entry containing metadata such as timestamp, token symbol, amount, price, and
        transaction hash, then appends it to a file in the `trades/` directory. If the directory does
        not exist, it is created. Useful for post-analysis or error diagnostics.

        Parameters:
        - action (str): Trade action type, typically "buy" or "sell".
        - tokendata (TokenInfo): Information about the traded token.
        - price (float): Execution price per token.
        - amount (float): Amount of tokens involved in the trade.
        - tx_hash (str | None): Solana transaction signature, if available.

        Returns:
        - None
        """
        try:
            os.makedirs("trades", exist_ok=True)
            logdata = {
                "timestamp": datetime.utcnow().isoformat(),
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
        """
        Waits asynchronously for a new token to be detected by the configured listener. The method
        uses a callback function to monitor token events and sets an internal event flag when a
        matching token is found. If a valid token is received before the timeout expires, it is
        returned; otherwise, the method logs a timeout message and returns `None`.

        Parameters:
        - None

        Returns:
        - TokenInfo | None: A matching token object if found, or None on timeout.
        """
        tokenfound = asyncio.Event()
        fetchtoken = None

        # Function 'TokenCallback'
        async def TokenCallback(token: TokenInfo) -> None:
            """
            Callback function triggered by the token listener when a new token event is received.
            It verifies whether the token has already been processed to avoid duplication, records
            the token’s arrival timestamp, and stores it for further trading actions. If the token
            is valid and new, the function sets an asynchronous event flag to unblock the main
            waiting routine.

            Parameters:
            - token (TokenInfo): An object containing metadata about the detected token, such as mint and symbol.

            Returns:
            - None
            """
            nonlocal fetchtoken
            token_key = str(token.mint)

            if token_key not in self.processedtokens:
                self.tokentimestamps[token_key] = monotonic()
                fetchtoken = token
                self.processedtokens.add(token_key)
                tokenfound.set()

        listenertask = asyncio.create_task(self.tokenlistener.listen_for_tokens(TokenCallback, self.matchstring, self.useraddress))
        try:
            logger.info(f"Waiting for a suitable token (timeout: {self.waittokentimeout}s)...")
            await asyncio.wait_for(tokenfound.wait(), timeout=self.waittokentimeout)
            logger.info(f"Found token: {fetchtoken.symbol} ({fetchtoken.mint})")
            return fetchtoken
        except TimeoutError:
            logger.info(f"Timed out after waiting {self.waittokentimeout}s for a token")
            return None
        finally:
            listenertask.cancel()
            try:
                await listenertask
            except asyncio.CancelledError:
                pass

    # Function 'HandleSuccessBuy'
    async def HandleSuccessBuy(self, tokendata: TokenInfo, buyresult: TradeResult) -> None:
        """
        Handles logic following a successful token purchase, including logging the trade, updating
        internal state, and optionally executing a sell order if shorting is permitted. After the sale,
        the appropriate post-sell cleanup procedure is triggered, depending on the agent's configuration.

        Parameters:
        - tokendata (TokenInfo): Metadata about the token that was bought.
        - buyresult (TradeResult): Result of the buy operation including amount, price, and success status.

        Returns:
        - None
        """
        logger.info(f"Successfully bought {tokendata.symbol}")
        self.StoreTrade("buy", tokendata, buyresult.price, buyresult.amount, buyresult.tx_signature)
        self.tradedmints.add(tokendata.mint)

        if not self.noshorting:
            logger.info(f"Waiting for {self.waitafterbuy} seconds before selling...")
            await asyncio.sleep(self.waitafterbuy)

            logger.info(f"Selling {tokendata.symbol}...")
            sellresult: TradeResult = await self.seller.execute(tokendata)

            if sellresult.success:
                logger.info(f"Successfully sold {tokendata.symbol}")
                self.StoreTrade("sell", tokendata, sellresult.price, sellresult.amount, sellresult.tx_signature)

                await handle_cleanup_after_sell
                (
                    self.solanaclient,
                    self.wallet,
                    tokendata.mint,
                    self.priorityorderfee,
                    self.cleanupmode,
                    self.cleanupfee,
                    self.cleanupburn
                )
            else:
                logger.error(f"Failed to sell {tokendata.symbol}: {sellresult.error_message}")
        else:
            logger.info("No-Shorting enabled. Skipping sell operation.")

    # Function 'HandleFailedBuy'
    async def HandleFailedBuy(self, tokendata: TokenInfo, buyresult: TradeResult) -> None:
        """
        Handles cleanup tasks after a failed token purchase attempt. This ensures any temporary
        allocations or failed transactions are cleared properly to avoid wallet clutter or future
        transaction conflicts. It also considers burn and fee cleanup settings when removing token data.

        Parameters:
        - tokendata (TokenInfo): The token that was attempted to be purchased.
        - buyresult (TradeResult): The result of the failed trade attempt.

        Returns:
        - None
        """
        await handle_cleanup_after_failure
        (
            self.solanaclient,
            self.wallet,
            tokendata.mint,
            self.priorityorderfee,
            self.cleanupmode,
            self.cleanupfee,
            self.cleanupburn
        )

    # Function 'CleanupResources'
    async def CleanupResources(self) -> None:
        """
        Performs a full cleanup at the end of a trading session. This includes deallocating or burning
        any remaining token accounts, applying cleanup logic for each token traded, and closing the
        Solana client connection. It also purges old token timestamps that were never processed. This
        method ensures the agent exits cleanly without leaving behind unnecessary resources.

        Parameters:
        - None

        Returns:
        - None
        """
        if self.tradedmints:
            try:
                logger.info(f"Cleaning up {len(self.tradedmints)} traded token(s)...")
                await handle_cleanup_post_session(
                    self.solanaclient,
                    self.wallet,
                    list(self.tradedmints),
                    self.priorityorderfee,
                    self.cleanupmode,
                    self.cleanupfee,
                    self.cleanupburn
                )
            except Exception as e:
                logger.error(f"Error during cleanup: {e!s}")

        old_keys = {k for k in self.tokentimestamps if k not in self.processedtokens}
        for key in old_keys:
            self.tokentimestamps.pop(key, None)

        await self.solanaclient.close()

    # Function 'TokenQueue'
    async def TokenQueue(self, tokendata: TokenInfo) -> None:
        """
        Adds a token to the internal queue for processing, as long as it has not already been processed.
        The method also tracks the arrival timestamp for age validation and logs the queuing action
        for transparency. Tokens already seen are skipped to avoid redundant trades.

        Parameters:
        - tokendata (TokenInfo): The token detected by a listener that may be eligible for trading.

        Returns:
        - None
        """
        tokenkey = str(tokendata.mint)
        if tokenkey in self.processedtokens:
            logger.debug(f"Token {tokendata.symbol} already processed. Skipping...")
            return

        self.tokentimestamps[tokenkey] = monotonic()
        await self.token_queue.put(tokendata)
        logger.info(f"Queued new token: {tokendata.symbol} ({tokendata.mint})")

    # Function 'ProcessQueue'
    async def ProcessQueue(self) -> None:
        """
        Continuously processes new tokens from the internal queue. For each token, it checks the age
        against a maximum threshold, discards old tokens, and passes valid ones to the trade execution
        handler. This loop runs until cancelled and handles all errors internally to maintain uptime.

        Parameters:
        - None

        Returns:
        - None
        """
        while True:
            try:
                tokendata = await self.tokenqueue.get()
                tokenkey = str(tokendata.mint)

                current_time = monotonic()
                token_age = current_time - self.tokentimestamps.get(tokenkey, current_time)

                if token_age > self.maxtokenage:
                    logger.info(f"Skipping token {tokendata.symbol} - too old ({token_age:.1f}s > {self.maxtokenage}s)")
                    continue

                self.processedtokens.add(tokenkey)
                logger.info(f"Processing fresh token: {tokendata.symbol} (age: {token_age:.1f}s)")
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
        """
        Executes the full trade logic for a token, beginning with an optional delay (unless in fast mode),
        then attempts to buy and, if successful, proceeds with a sell (unless no-shorting is enabled).
        Handles all retry logic, error logging, and calls post-trade cleanup as needed. Token trade
        delays are controlled by configuration.

        Parameters:
        - tokendata (TokenInfo): Metadata about the token being processed.

        Returns:
        - None
        """
        try:
            if not self.fastmode:
                logger.info(f"Waiting for {self.waitaftercreation} seconds for the bonding curve to stabilize...")
                await asyncio.sleep(self.waitaftercreation)

            logger.info(f"Buying {self.buyamount:.6f} SOL worth of {tokendata.symbol}...")
            buyresult: TradeResult = await self.buyer.execute(tokendata)

            if buyresult.success:
                await self.HandleSuccessBuy(tokendata, buyresult)
            else:
                await self.HandleFailedBuy(tokendata, buyresult)

            if self.filteroff:
                logger.info(f"Filter-Off enabled. Waiting {self.waitnewtoken} seconds before looking for next token...")
                await asyncio.sleep(self.waitnewtoken)

        except Exception as e:
            logger.error(f"Error handling token {tokendata.symbol}: {e!s}")

    # Function 'AgentStart'
    async def AgentStart(self) -> None:
        """
        Entry point to launch the agent's trading loop. It verifies RPC health, then either waits
        for a single token (in filtered mode) or runs in continuous token discovery and processing mode.
        It sets up the processor task, handles token reception, and ensures graceful cleanup on exit.
        All errors are caught and logged to avoid interruptions or partial execution.

        Parameters:
        - None

        Returns:
        - None
        """
        logger.info("Starting PumpBot agent")
        logger.info(f"Match filter: {self.matchstring if self.matchstring else 'None'}")
        logger.info(f"Creator filter: {self.useraddress if self.useraddress else 'None'}")
        logger.info(f"No-Shorting: {self.noshorting}")
        logger.info(f"Filter-Off: {self.filteroff}")
        logger.info(f"Max token age: {self.maxtokenage} seconds")

        try:
            healthresp = await self.solanaclient.GetHealth()
            logger.info(f"RPC warm-up successful (getHealth passed: {healthresp})")
        except Exception as e:
            logger.warning(f"RPC warm-up failed: {e!s}")

        try:
            if not self.filteroff:
                logger.info("Running in single token mode - will process one token and exit")
                tokendata = await self.WaitForToken()
                if tokendata:
                    await self.HandleTokenOrder(tokendata)
                    logger.info("Finished processing single token. Exiting...")
                else:
                    logger.info(f"No suitable token found within timeout period ({self.waittokentimeout}s). Exiting...")
            else:
                logger.info("Running in continuous mode - will process tokens until interrupted")
                processortask = asyncio.create_task(self.ProcessQueue())

                try:
                    await self.tokenlistener.listen_for_tokens(lambda token: self.TokenQueue(token), self.matchstring, self.useraddress)
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