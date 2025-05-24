# Import libraries
import asyncio
import json
import logging
import websockets

# Import packages
from collections.abc import Awaitable
from collections.abc import Callable
from solders.pubkey import Pubkey

# Import local packages
from monitoring.base import BaseTokenListener
from monitoring.processor import LogsProcessor
from monitoring.processor import PumpProcessor
from handler.base import TokenInfo

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'BlockListener'
class BlockListener(BaseTokenListener):
    """
    This class listens to the Solana blockchain through a WebSocket connection
    and processes pump program-specific events in real time. It extends the
    BaseTokenListener to monitor token activity and trigger a specified callback
    whenever relevant token events occur. The class is particularly designed to
    work with programs like Pump.fun and uses a custom event processor for handling
    incoming events. It maintains a persistent WebSocket connection to stream
    data and processes it using user-defined callbacks.

    Parameters:
    - wss_endpoint (str): The WebSocket endpoint of the Solana cluster to connect to.
    - pump_program (Pubkey): The public key of the Pump program to monitor for relevant events.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, wss_endpoint: str, pump_program: Pubkey):
        """
        This initializer sets up the BlockListener with the WebSocket endpoint and
        the Pump program's public key. It also initializes the internal event processor
        that handles matching and decoding Pump-related instructions from the stream.
        The ping interval is configured to maintain a healthy WebSocket connection.
        This setup allows asynchronous processing of real-time blockchain data.

        Parameters:
        - wss_endpoint (str): The URL of the Solana WebSocket endpoint for subscription.
        - pump_program (Pubkey): The Pump program ID used to filter and process events.

        Returns:
        - None
        """
        self.wss_endpoint = wss_endpoint
        self.pump_program = pump_program
        self.event_processor = PumpProcessor(pump_program)
        self.ping_interval = 20

    # Function 'listen_for_tokens'
    async def listen_for_tokens(self, token_callback: Callable[[TokenInfo], Awaitable[None]], match_string: str | None = None, creator_address: str | None = None) -> None:
        """
         Listens to the Solana blockchain in real-time using a persistent WebSocket connection.
         Filters incoming account updates and log messages associated with the specified Pump
         program. When a matching token is detected, it processes the event and triggers the
         user-defined callback. This function allows optional filtering using a substring
         match or creator address to restrict the results to specific token launches or origins.

         Parameters:
         - token_callback (Callable[[TokenInfo], Awaitable[None]]): An asynchronous callback
           function to be called whenever a new matching token event is detected.
         - match_string (str | None): An optional string to match against token metadata or addresses.
         - creator_address: The Solana public key to filter tokens by creator (type not explicitly annotated).

         Returns:
         - None
         """
        while True:
            try:
                async with websockets.connect(self.wss_endpoint) as websocket:
                    await self._subscribe_to_program(websocket)
                    ping_task = asyncio.create_task(self._ping_loop(websocket))

                    try:
                        while True:
                            token_info = await self._wait_for_token_creation(websocket)
                            if not token_info:
                                continue

                            logger.info(f"New token detected: {token_info.name} ({token_info.symbol})")
                            if match_string and not (match_string.lower() in token_info.name.lower() or match_string.lower() in token_info.symbol.lower()):
                                logger.info(f"Token does not match filter '{match_string}'. Skipping...")
                                continue

                            if (creator_address and str(token_info.user) != creator_address):
                                logger.info(f"Token not created by {creator_address}. Skipping...")
                                continue

                            await token_callback(token_info)

                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed. Reconnecting...")
                        ping_task.cancel()

            except Exception as e:
                logger.error(f"WebSocket connection error: {e!s}")
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    # Function '_subscribe_to_program'
    async def _subscribe_to_program(self, websocket) -> None:
        """
        This function sends a JSON-RPC subscription message over the WebSocket connection
        to subscribe to Solana blocks that mention the specified Pump program. It is part
        of the block-level monitoring logic that allows tracking all transactions involving
        the targeted program. The function constructs the subscription payload with
        parameters such as commitment level, encoding type, and transaction details, and
        then sends it to the blockchain node via the WebSocket stream.

        Parameters:
        - websocket: An open WebSocket connection (typically from `websockets.connect`) used to send the subscription message.

        Returns:
        - None
        """
        subscription_message = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "blockSubscribe",
                "params": [
                    {"mentionsAccountOrProgram": str(self.pump_program)},
                    {
                        "commitment": "confirmed",
                        "encoding": "base64",
                        "showRewards": False,
                        "transactionDetails": "full",
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            }
        )

        await websocket.send(subscription_message)
        logger.info(f"Subscribed to blocks mentioning program: {self.pump_program}")

    # Function '_ping_loop'
    async def _ping_loop(self, websocket) -> None:
        """
        This function maintains the WebSocket connection by periodically sending ping
        frames to the Solana node. It uses the ping/pong mechanism to detect broken
        connections and ensure the listener remains active. If the pong response is not
        received within a defined timeout, the function closes the connection to trigger
        a reconnection or termination. This loop runs continuously with an interval
        defined by `self.ping_interval` until cancelled or an error occurs.

        Parameters:
        - websocket: The active WebSocket connection on which pings are sent and pong responses are awaited.

        Returns:
        - None
        """
        try:
            while True:
                await asyncio.sleep(self.ping_interval)
                try:
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10)
                except TimeoutError:
                    logger.warning("Ping timeout - server not responding")
                    await websocket.close()
                    return
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping error: {e!s}")

    # Function '_wait_for_token_creation'
    async def _wait_for_token_creation(self, websocket) -> TokenInfo | None:
        """
        This function waits for a block notification message over the WebSocket and scans
        it for transactions that potentially involve the Pump program. It processes each
        transaction using the internal event processor and extracts token creation events.
        If a valid token event is detected, it returns a populated `TokenInfo` object.
        It includes robust error handling to deal with timeouts, malformed messages,
        or closed connections, returning `None` if no token is detected.

        Parameters:
        - websocket: The WebSocket connection used to receive real-time block data from the Solana cluster.

        Returns:
        - TokenInfo | None: A `TokenInfo` object representing the detected token creation event,
          or `None` if no relevant event is found or an error occurs.
        """
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            data = json.loads(response)

            if "method" not in data or data["method"] != "blockNotification":
                return None

            if "params" not in data or "result" not in data["params"]:
                return None

            block_data = data["params"]["result"]
            if "value" not in block_data or "block" not in block_data["value"]:
                return None

            block = block_data["value"]["block"]
            if "transactions" not in block:
                return None

            for tx in block["transactions"]:
                if not isinstance(tx, dict) or "transaction" not in tx:
                    continue

                token_info = self.event_processor.process_transaction(
                    tx["transaction"][0]
                )
                if token_info:
                    return token_info

        except TimeoutError:
            logger.debug("No data received for 30 seconds")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            raise
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e!s}")

        return None


# Class 'LogsListener'
class LogsListener(BaseTokenListener):
    """
    This class establishes a WebSocket connection to a Solana node and listens for log messages
    that reference a specific Pump program. It filters, decodes, and analyzes transaction logs
    in real time to detect token creation events. When a new token is detected that matches the
    specified criteria, it triggers a user-defined callback. This listener provides an efficient
    method to monitor on-chain activity without using full transaction streams.

    Parameters:
    - wss_endpoint (str): The WebSocket endpoint of a Solana RPC node.
    - pump_program (Pubkey): The public key of the Pump program to monitor in transaction logs.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, wss_endpoint: str, pump_program: Pubkey):
        """
        Initializes the LogsListener instance by setting up the WebSocket endpoint and Pump
        program public key. It also creates an internal log event processor to handle token
        detection based on real-time log messages. The ping interval is set to maintain
        WebSocket health via regular pings.

        Parameters:
        - wss_endpoint (str): URL of the WebSocket endpoint to connect to.
        - pump_program (Pubkey): Program ID to track in log messages.

        Returns:
        - None
        """
        self.wss_endpoint = wss_endpoint
        self.pump_program = pump_program
        self.event_processor = LogsProcessor(pump_program)
        self.ping_interval = 20

    # Function 'listen_for_tokens'
    async def listen_for_tokens(self, token_callback: Callable[[TokenInfo], Awaitable[None]], match_string: str | None = None, creator_address: str | None = None) -> None:
        """
        Listens indefinitely to Solana log messages through a WebSocket connection. Upon receiving
        new logs mentioning the target program, it processes them to detect token creation events.
        It applies optional filters based on name, symbol, or creator address before invoking the
        provided asynchronous callback. The method is resilient to disconnections and attempts
        automatic reconnection with delay.

        Parameters:
        - token_callback (Callable[[TokenInfo], Awaitable[None]]): The async function to call when a token is detected.
        - match_string (str | None): Optional filter to match token name or symbol.
        - creator_address (str | None): Optional filter to only allow tokens created by a specific address.

        Returns:
        - None
        """
        while True:
            try:
                async with websockets.connect(self.wss_endpoint) as websocket:
                    await self._subscribe_to_logs(websocket)
                    ping_task = asyncio.create_task(self._ping_loop(websocket))

                    try:
                        while True:
                            token_info = await self._wait_for_token_creation(websocket)
                            if not token_info:
                                continue

                            logger.info(f"New token detected: {token_info.name} ({token_info.symbol})")
                            if match_string and not (match_string.lower() in token_info.name.lower() or match_string.lower() in token_info.symbol.lower()):
                                logger.info(f"Token does not match filter '{match_string}'. Skipping...")
                                continue

                            if (creator_address and str(token_info.user) != creator_address):
                                logger.info(f"Token not created by {creator_address}. Skipping...")
                                continue
                            await token_callback(token_info)

                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed. Reconnecting...")
                        ping_task.cancel()

            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    # Function '_subscribe_to_logs'
    async def _subscribe_to_logs(self, websocket) -> None:
        """
        Sends a `logsSubscribe` request over the WebSocket connection to subscribe to all Solana
        logs that mention the configured Pump program. After sending the request, it listens for
        and validates the subscription confirmation message. This function ensures that log
        notifications will be streamed for further analysis by the listener.

        Parameters:
        - websocket: The open WebSocket connection used to send and receive subscription messages.

        Returns:
        - None
        """
        subscription_message = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    {"mentions": [str(self.pump_program)]},
                    {"commitment": "processed"},
                ],
            }
        )

        await websocket.send(subscription_message)
        logger.info(f"Subscribed to logs mentioning program: {self.pump_program}")
        response = await websocket.recv()
        response_data = json.loads(response)

        if "result" in response_data:
            logger.info(f"Subscription confirmed with ID: {response_data['result']}")
        else:
            logger.warning(f"Unexpected subscription response: {response}")

    # Function '_ping_loop'
    async def _ping_loop(self, websocket) -> None:
        """
        Keeps the WebSocket connection alive by sending ping messages at regular intervals. If
        the pong response is not received within a defined timeout, the connection is considered
        broken and closed. This watchdog mechanism ensures robustness against dropped or silent
        connections and allows reconnection strategies to be triggered when needed.

        Parameters:
        - websocket: The active WebSocket connection used for sending pings.

        Returns:
        - None
        """
        try:
            while True:
                await asyncio.sleep(self.ping_interval)
                try:
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10)
                except asyncio.TimeoutError:
                    logger.warning("Ping timeout - server not responding")
                    await websocket.close()
                    return
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping error: {str(e)}")

    # Function '_wait_for_token_creation'
    async def _wait_for_token_creation(self, websocket) -> TokenInfo | None:
        """
        Waits for and processes the next log message received from the WebSocket connection.
        It verifies that the incoming message is a `logsNotification`, extracts the log entries
        and transaction signature, and passes them to the event processor for analysis. If a valid
        token creation is detected, the function returns a TokenInfo object; otherwise, it returns None.

        Parameters:
        - websocket: The WebSocket connection used to receive log notifications.

        Returns:
        - TokenInfo | None: A populated TokenInfo object if a token is detected, or None otherwise.
        """
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            data = json.loads(response)

            if "method" not in data or data["method"] != "logsNotification":
                return None

            log_data = data["params"]["result"]["value"]
            logs = log_data.get("logs", [])
            signature = log_data.get("signature", "unknown")
            return self.event_processor.process_program_logs(logs, signature)

        except asyncio.TimeoutError:
            logger.debug("No data received for 30 seconds")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            raise
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

        return None