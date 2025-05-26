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
    """ Class description """

    # Class initialization
    def __init__(self, wss_endpoint: str, pump_program: Pubkey):
        """ Initializer description """
        self.wss_endpoint = wss_endpoint
        self.pump_program = pump_program
        self.event_processor = PumpProcessor(pump_program)
        self.ping_interval = 20

    # Function 'listen_for_tokens'
    async def listen_for_tokens(self, token_callback: Callable[[TokenInfo], Awaitable[None]], match_string: str | None = None, creator_address: str | None = None) -> None:
        """ Function description """
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

                            if creator_address and str(token_info.user) != creator_address:
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
        """ Function description """
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
        """ Function description """
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
        """ Function description """
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
    """ Class description """

    # Class initialization
    def __init__(self, wss_endpoint: str, pump_program: Pubkey):
        """ Initializer description """
        self.wss_endpoint = wss_endpoint
        self.pump_program = pump_program
        self.event_processor = LogsProcessor(pump_program)
        self.ping_interval = 20

    # Function 'listen_for_tokens'
    async def listen_for_tokens(self, token_callback: Callable[[TokenInfo], Awaitable[None]], match_string: str | None = None, creator_address: str | None = None) -> None:
        """ Function description """
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

                            if creator_address and str(token_info.user) != creator_address:
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
        """ Function description """
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
        """ Function description """
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
        """ Function description """
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