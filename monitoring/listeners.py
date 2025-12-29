# Import libraries
import asyncio
import json
import logging

import requests
import websockets

# Import packages
from collections.abc import Awaitable
from collections.abc import Callable
from datetime import datetime
from datetime import UTC
from solders.pubkey import Pubkey

# Import local packages
from monitoring.base import BaseTokenListener
from monitoring.processor import LogsProcessor
from monitoring.processor import PumpProcessor
from handler.base import TokenInfo
from screeners.pumpswap import PumpScreener
from utils.scaler import NumberScaler

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'BlockListener'
class BlockListener(BaseTokenListener):
    """ Class description """

    # Class initialization
    def __init__(self, wss_endpoint: str, pump_program: Pubkey, chaininterval: int):
        """ Initializer description """
        self.wss_endpoint = wss_endpoint
        self.pump_program = pump_program
        self.chaininterval = chaininterval
        self.event_processor = PumpProcessor(pump_program)
        self.ping_interval = 20

    # Function 'listen_for_tokens'
    @staticmethod
    async def extractholders(token_address):
        url = f"https://frontend-api-v3.pump.fun/coins/top-holders/{token_address}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Connection": "close"
        }

        try:
            with requests.Session() as s:
                s.headers.update(headers)
                r = s.get(url, timeout=5)
                r.raise_for_status()
                wallets = r.json()
                holders = wallets.get("topHolders", {}).get("value", [])
                return [entry["address"] for entry in holders if "address" in entry]
        except requests.HTTPError:
            return []
        except (requests.RequestException, ValueError, KeyError):
            return []

    @staticmethod
    async def extractbalance(wallet_address, rpc_url="https://api.mainnet-beta.solana.com"):
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }

        try:
            response = requests.post(rpc_url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json().get("result", {})
            lamports = result.get("value", 0)
            sol = lamports / 1_000_000_000
            return sol
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None

    # Function 'listen_for_tokens'
    async def listen_for_tokens(self,
        token_callback: Callable[[TokenInfo],
        Awaitable[None]],
        maxopentrades: int | int = 1,
        matchstring: str | None = None,
        matchaddress: str | None = None,
        nostopping: bool = False,
        tokenminage: int | int = 1,
        tokenmaxage: int | int = 1,
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
        maxliquidity: int = 5) -> None:
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
                            if NumberScaler.safefloat(self.chaininterval) is not False:
                                await asyncio.sleep(self.chaininterval)
                            screener = PumpScreener()
                            marketinfo = screener.tokenquery(str(token_info.mint))
                            if marketinfo:
                                token_info.created = marketinfo["created"]
                                token_info.price = marketinfo["price"]
                                token_info.liquidity = marketinfo["liquidity"]
                                token_info.volume = marketinfo["volume"]
                                token_info.marketcap = marketinfo["marketcap"]

                                if float(token_info.liquidity) <= minliquidity:
                                    logger.warning(f"Skipping token {token_info.symbol} - Minimum L/P of {minliquidity} SOL not reached")
                                    continue

                                if float(token_info.liquidity) >= maxliquidity:
                                    logger.warning(f"Skipping token {token_info.symbol} - Maximum L/P of {maxliquidity} SOL reached")
                                    continue

                                if float(token_info.marketcap) <= minmarketcap:
                                    logger.warning(f"Skipping token {token_info.symbol} - Minimum M/C of {minmarketcap} SOL not reached")
                                    continue

                                if float(token_info.marketcap) >= maxmarketcap:
                                    logger.warning(f"Skipping token {token_info.symbol} - Maximum M/C of {maxmarketcap} SOL reached")
                                    continue

                            # Filter 'tokenminage'
                            # Filter 'tokenmaxage'
                            if nostopping is False:
                                spread = int(datetime.now(UTC).timestamp()) - token_info.created
                                if not (tokenminage <= spread <= tokenmaxage):
                                    logger.warning(f"Skipping token {token_info.symbol} - Age {spread}s not in range [{tokenminage}s, {tokenmaxage}s]")
                                    continue

                            # Filter 'matchstring'
                            if matchstring and not (matchstring.lower()
                                in token_info.name.lower() or matchstring.lower()
                                in token_info.symbol.lower()):
                                logger.warning(f"Skipping token {token_info.symbol} - Does not match filter {matchstring}")
                                continue

                            # Filter 'matchaddress'
                            if matchaddress and str(token_info.user) != matchaddress:
                                logger.warning(f"Skipping token {token_info.symbol} - Does not match user address {matchaddress}")
                                continue

                            # Filter 'minholders'
                            if minholders > 0:
                                holders = await self.extractholders(token_info.mint)
                                if len(holders) < minholders:
                                    logger.warning(f"Skipping token {token_info.symbol} - Does not match the minimum required of token holders")
                                    continue

                                if len(holders) > maxholders:
                                    logger.warning(f"Skipping token {token_info.symbol} - Does not match the maximum allowed of token holders")
                                    continue

                                if holderscheck is True:
                                    for wallet in enumerate(holders, start=1):
                                        balance = await self.extractbalance(wallet)
                                        if balance < holdersbalance:
                                            logger.warning(f"Skipping token {token_info.symbol} - Does not match the minimum required of SOL balance")
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
    def __init__(self, wss_endpoint: str, pump_program: Pubkey, chaininterval: int):
        """ Initializer description """
        self.wss_endpoint = wss_endpoint
        self.pump_program = pump_program
        self.chaininterval = chaininterval
        self.event_processor = LogsProcessor(pump_program)
        self.ping_interval = 20

    # Function 'listen_for_tokens'
    @staticmethod
    async def extractholders(token_address):
        url = f"https://frontend-api-v3.pump.fun/coins/top-holders/{token_address}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Connection": "close"
        }

        try:
            with requests.Session() as s:
                s.headers.update(headers)
                r = s.get(url, timeout=5)
                r.raise_for_status()
                wallets = r.json()
                holders = wallets.get("topHolders", {}).get("value", [])
                return [entry["address"] for entry in holders if "address" in entry]
        except requests.HTTPError:
            return []
        except (requests.RequestException, ValueError, KeyError):
            return []

    @staticmethod
    async def extractbalance(wallet_address, rpc_url="https://api.mainnet-beta.solana.com"):
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }

        try:
            response = requests.post(rpc_url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json().get("result", {})
            lamports = result.get("value", 0)
            sol = lamports / 1_000_000_000
            return sol
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None

    # Function 'listen_for_tokens'
    async def listen_for_tokens(self,
        token_callback: Callable[[TokenInfo],
        Awaitable[None]],
        maxopentrades: int | int = 1,
        matchstring: str | None = None,
        matchaddress: str | None = None,
        nostopping: bool = False,
        tokenminage: int | int = 1,
        tokenmaxage: int | int = 1,
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
        maxliquidity: int = 5) -> None:
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
                            if NumberScaler.safefloat(self.chaininterval) is not False:
                                await asyncio.sleep(self.chaininterval)
                            screener = PumpScreener()
                            marketinfo = screener.tokenquery(str(token_info.mint))
                            if marketinfo:
                                token_info.created = marketinfo["created"]
                                token_info.price = marketinfo["price"]
                                token_info.liquidity = marketinfo["liquidity"]
                                token_info.volume = marketinfo["volume"]
                                token_info.marketcap = marketinfo["marketcap"]

                                if float(token_info.liquidity) <= minliquidity:
                                    logger.warning(f"Skipping token {token_info.symbol} - Minimum L/P of {minliquidity} SOL not reached")
                                    continue

                                if float(token_info.liquidity) >= maxliquidity:
                                    logger.warning(f"Skipping token {token_info.symbol} - Maximum L/P of {maxliquidity} SOL reached")
                                    continue

                                if float(token_info.marketcap) <= minmarketcap:
                                    logger.warning(f"Skipping token {token_info.symbol} - Minimum M/C of {minmarketcap} SOL not reached")
                                    continue

                                if float(token_info.marketcap) >= maxmarketcap:
                                    logger.warning(f"Skipping token {token_info.symbol} - Maximum M/C of {maxmarketcap} SOL reached")
                                    continue

                            # Filter 'tokenminage'
                            # Filter 'tokenmaxage'
                            if nostopping is False:
                                spread = int(datetime.now(UTC).timestamp()) - token_info.created
                                if not (tokenminage <= spread <= tokenmaxage):
                                    logger.warning(f"Skipping token {token_info.symbol} - Age {spread}s not in range [{tokenminage}s, {tokenmaxage}s]")
                                    continue

                            # Filter 'matchstring'
                            if matchstring and not (matchstring.lower()
                                in token_info.name.lower() or matchstring.lower()
                                in token_info.symbol.lower()):
                                logger.warning(f"Skipping token {token_info.symbol} - Does not match filter {matchstring}")
                                continue

                            # Filter 'matchaddress'
                            if matchaddress and str(token_info.user) != matchaddress:
                                logger.warning(f"Skipping token {token_info.symbol} - Does not match user address {matchaddress}")
                                continue

                            # Filter 'minholders'
                            if minholders > 0:
                                holders = await self.extractholders(token_info.mint)
                                if len(holders) < minholders:
                                    logger.warning(f"Skipping token {token_info.symbol} - Does not match the minimum required of token holders")
                                    continue

                                if len(holders) > maxholders:
                                    logger.warning(f"Skipping token {token_info.symbol} - Does not match the maximum allowed of token holders")
                                    continue

                                if holderscheck is True:
                                    for wallet in enumerate(holders, start=1):
                                        balance = await self.extractbalance(wallet)
                                        if balance < holdersbalance:
                                            logger.warning(f"Skipping token {token_info.symbol} - Does not match the minimum required of SOL balance")
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