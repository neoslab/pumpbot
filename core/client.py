# Import libraries
import aiohttp
import asyncio
import json
import logging

# Import packages
from typing import Any
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.rpc.types import TxOpts
from solders.compute_budget import set_compute_unit_limit
from solders.compute_budget import set_compute_unit_price
from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

# Define 'logger'
logger = logging.getLogger(__name__)


# Class 'SolanaClient'
class SolanaClient:
    """ Class description """

    # Class initialization
    def __init__(self, rpcendpoint: str):
        """ Initializer description """
        self.rpcendpoint = rpcendpoint
        self._client = None
        self._cached_blockhash: Hash | None = None
        self._blockhash_lock = asyncio.Lock()
        self._blockhash_updater_task = asyncio.create_task(self.start_blockhash_updater())

    # Function 'PostRPC'
    async def PostRPC(self, body: dict[str, Any]) -> dict[str, Any] | None:
        """ Function description """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpcendpoint, json = body, timeout = aiohttp.ClientTimeout(10)) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"RPC request failed: {e!s}", exc_info=True)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode RPC response: {e!s}", exc_info=True)
            return None

    # Function 'GetHealth'
    async def GetHealth(self) -> str | None:
        """ Function description """
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth"
        }
        result = await self.PostRPC(body)
        if result and "result" in result:
            return result["result"]
        return None

    # Function 'start_blockhash_updater'
    async def start_blockhash_updater(self, interval: float = 5.0):
        """ Function description """
        while True:
            try:
                blockhash = await self.get_latest_blockhash()
                async with self._blockhash_lock:
                    self._cached_blockhash = blockhash
            except Exception as e:
                logger.warning(f"Blockhash fetch failed: {e!s}")
            finally:
                await asyncio.sleep(interval)

    # Function 'get_cached_blockhash'
    async def get_cached_blockhash(self) -> Hash:
        """ Function description """
        async with self._blockhash_lock:
            if self._cached_blockhash is None:
                raise RuntimeError("No cached blockhash available yet")
            return self._cached_blockhash

    # Function 'get_client'
    async def get_client(self) -> AsyncClient:
        """ Function description """
        if self._client is None:
            self._client = AsyncClient(self.rpcendpoint)
        return self._client

    # Function 'close'
    async def close(self):
        """ Function description """
        if self._blockhash_updater_task:
            self._blockhash_updater_task.cancel()
            try:
                await self._blockhash_updater_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.close()
            self._client = None

    # Function 'get_account_info'
    async def get_account_info(self, pubkey: Pubkey) -> dict[str, Any]:
        """ Function description """
        client = await self.get_client()
        response = await client.get_account_info(pubkey, encoding="base64")
        if not response.value:
            raise ValueError(f"Account {pubkey} not found")
        return response.value

    # Function 'get_token_account_balance'
    async def get_token_account_balance(self, token_account: Pubkey) -> int:
        """ Function description """
        client = await self.get_client()
        response = await client.get_token_account_balance(token_account)
        if response.value:
            return int(response.value.amount)
        return 0

    # Function 'get_latest_blockhash'
    async def get_latest_blockhash(self) -> Hash:
        """ Function description """
        client = await self.get_client()
        response = await client.get_latest_blockhash(commitment="processed")
        return response.value.blockhash

    # Function 'build_and_send_transaction'
    async def build_and_send_transaction(self, instructions: list[Instruction], signer_keypair: Keypair, skip_preflight: bool = True, max_retries: int = 3, priority_fee: int | None = None) -> str:
        """ Function description """
        client = await self.get_client()
        logger.info(f"Priority fee in microlamports: {priority_fee if priority_fee else 0}")
        if priority_fee is not None:
            fee_instructions = [set_compute_unit_limit(72_000), set_compute_unit_price(priority_fee)]
            instructions = fee_instructions + instructions

        recent_blockhash = await self.get_cached_blockhash()
        message = Message(instructions, signer_keypair.pubkey())
        transaction = Transaction([signer_keypair], message, recent_blockhash)

        for attempt in range(max_retries):
            try:
                tx_opts = TxOpts(skip_preflight = skip_preflight, preflight_commitment = Processed)
                response = await client.send_transaction(transaction, tx_opts)
                return response.value

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to send transaction after {max_retries} attempts")
                    raise

                wait_time = 2**attempt
                logger.warning(f"Transaction attempt {attempt + 1} failed: {e!s}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)

    # Function 'confirm_transaction'
    async def confirm_transaction(self, signature: str, commitment: str = "confirmed") -> bool:
        """ Function description """
        client = await self.get_client()
        try:
            await client.confirm_transaction(signature, commitment=commitment, sleep_seconds=1)
            return True
        except Exception as e:
            logger.error(f"Failed to confirm transaction {signature}: {e!s}")
            return False