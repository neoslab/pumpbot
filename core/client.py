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
    """
    This class provides an asynchronous interface for interacting with the Solana blockchain using
    a specified RPC endpoint. It encapsulates a wide range of functionalities including RPC POST
    requests, blockhash caching, account queries, token balance fetching, transaction building and
    sending, and transaction confirmation. Designed for high-performance Solana clients, this class
    supports retries, fee prioritization, and modular transaction composition.

    Parameters:
    - rpcendpoint (str): The base URL of the Solana RPC endpoint to connect to.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, rpcendpoint: str):
        """
        Initializes the SolanaClient with the given RPC endpoint and sets up internal structures
        for caching, client instantiation, and blockhash updates. It prepares the instance to
        communicate asynchronously with the Solana network using either low-level RPC POST
        or high-level async client operations. No external setup is required beyond the endpoint.

        Parameters:
        - rpcendpoint (str): The URL of the Solana RPC endpoint to use for all blockchain queries.

        Returns:
        - None
        """
        self.rpcendpoint = rpcendpoint

    # Function 'PostRPC'
    async def PostRPC(self, body: dict[str, Any]) -> dict[str, Any] | None:
        """
        Sends a raw JSON-RPC request to the Solana RPC endpoint using the aiohttp client session.
        The request is posted with a 10-second timeout and handles common network and decoding
        errors gracefully. Useful for custom or low-level Solana method calls not yet implemented
        in higher-level libraries.

        Parameters:
        - body (dict[str, Any]): The JSON-RPC body to send in the POST request.

        Returns:
        - dict[str, Any] | None: Parsed JSON response if successful, or None on failure.
        """
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
        """
        Performs a health check on the connected Solana RPC node by sending the `getHealth`
        JSON-RPC method. This can help validate node status for routing, fallback, or diagnostics.
        Returns a status string such as "ok" if the node is healthy, or None if it fails.

        Parameters:
        - None

        Returns:
        - str | None: The health status string (e.g., "ok"), or None if the request fails.
        """
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
        """
        Continuously fetches the latest blockhash from the Solana network at the specified interval
        and caches it internally for reuse during transaction construction. This helps reduce the
        latency and load involved in repeatedly querying for blockhashes per transaction.

        Parameters:
        - interval (float): Time in seconds between blockhash refreshes (default is 5.0).

        Returns:
        - None
        """
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
        """
        Retrieves the most recently cached blockhash from the background updater. This avoids
        repeatedly calling the RPC and provides the latest known blockhash for transaction signing.
        If no blockhash has been cached yet, an exception is raised.

        Parameters:
        - None

        Returns:
        - Hash: The most recent valid blockhash as a `solders.hash.Hash` object.
        """
        async with self._blockhash_lock:
            if self._cached_blockhash is None:
                raise RuntimeError("No cached blockhash available yet")
            return self._cached_blockhash

    # Function 'get_client'
    async def get_client(self) -> AsyncClient:
        """
        Lazily initializes and returns an instance of the Solana AsyncClient used for high-level
        RPC operations. This client instance is cached for reuse and enables interaction with
        the blockchain without re-instantiating the connection each time.

        Parameters:
        - None

        Returns:
        - AsyncClient: An instance of Solana's asynchronous client.
        """
        if self._client is None:
            self._client = AsyncClient(self.rpc_endpoint)
        return self._client

    # Function 'close'
    async def close(self):
        """
        Closes any open asynchronous resources used by the client, including cancelling the
        blockhash updater task and closing the RPC connection. This method should be called
        during application shutdown or when the client is no longer needed.

        Parameters:
        - None

        Returns:
        - None
        """
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
        """
        Fetches and returns the account information for a given public key on the Solana blockchain.
        Uses base64 encoding and raises an exception if the account does not exist. The result
        includes all data associated with the account including balance, owner, and state.

        Parameters:
        - pubkey (Pubkey): The Solana public key identifying the account.

        Returns:
        - dict[str, Any]: A dictionary with decoded account information.
        """
        client = await self.get_client()
        response = await client.get_account_info(pubkey, encoding="base64")
        if not response.value:
            raise ValueError(f"Account {pubkey} not found")
        return response.value

    # Function 'get_token_account_balance'
    async def get_token_account_balance(self, token_account: Pubkey) -> int:
        """
        Retrieves the token balance of a specific SPL token account by querying the Solana blockchain.
        The value is extracted and converted to an integer. If the account is not found or invalid,
        the balance is returned as zero.

        Parameters:
        - token_account (Pubkey): The public key of the SPL token account.

        Returns:
        - int: The current token balance in raw units (not formatted).
        """
        client = await self.get_client()
        response = await client.get_token_account_balance(token_account)
        if response.value:
            return int(response.value.amount)
        return 0

    # Function 'get_latest_blockhash'
    async def get_latest_blockhash(self) -> Hash:
        """
        Fetches the most up-to-date blockhash from the Solana cluster using processed commitment.
        This is used when constructing and signing transactions to ensure they are not expired
        upon submission. Always fetches a fresh value regardless of the cache.

        Parameters:
        - None

        Returns:
        - Hash: A valid and recent blockhash needed for transaction finalization.
        """
        client = await self.get_client()
        response = await client.get_latest_blockhash(commitment="processed")
        return response.value.blockhash

    # Function 'build_and_send_transaction'
    async def build_and_send_transaction(self, instructions: list[Instruction], signer_keypair: Keypair, skip_preflight: bool = True, max_retries: int = 3, priority_fee: int | None = None) -> str:
        """
        Constructs and sends a signed transaction to the Solana blockchain using provided instructions
        and a signing keypair. Optionally includes compute unit priority fees and supports exponential
        retry logic for transient network or RPC failures. Returns the transaction signature upon success.

        Parameters:
        - instructions (list[Instruction]): A list of Solana instructions to be included in the transaction.
        - signer_keypair (Keypair): The keypair used to sign the transaction.
        - skip_preflight (bool): Whether to skip preflight simulation (default: True).
        - max_retries (int): Maximum number of retries on failure (default: 3).
        - priority_fee (int | None): Optional compute unit price to prioritize the transaction.

        Returns:
        - str: The transaction signature (string) if the submission is successful.
        """
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
        """
        Confirms that a previously submitted transaction has been finalized on the blockchain
        using the provided signature and commitment level. Handles confirmation delays or
        failure gracefully and returns a boolean outcome for higher-level flow control.

        Parameters:
        - signature (str): The transaction signature to confirm.
        - commitment (str): The desired confirmation level (e.g., "processed", "confirmed").

        Returns:
        - bool: True if the transaction is confirmed successfully, False otherwise.
        """
        client = await self.get_client()
        try:
            await client.confirm_transaction(signature, commitment=commitment, sleep_seconds=1)
            return True
        except Exception as e:
            logger.error(f"Failed to confirm transaction {signature}: {e!s}")
            return False