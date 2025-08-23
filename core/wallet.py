# Import libraries
import base58
import requests

# Import packages
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address


# Class 'Wallet'
class Wallet:
    """Handles Solana wallet keypair and associated addresses."""

    def __init__(self, private_key: str):
        """Initialize the wallet from a base58-encoded private key."""
        self._private_key = private_key
        self._keypair = self._load_keypair(private_key)
        self.validkey = self._keypair is not None

    @property
    def validprikey(self) -> bool:
        """Return True if the private key is valid and keypair is loaded."""
        return self.validkey

    @property
    def pubkey(self) -> Pubkey:
        """Return the public key of the wallet."""
        if not self.validkey:
            raise ValueError("Cannot access pubkey from an invalid keypair.")
        return self._keypair.pubkey()

    @property
    def keypair(self) -> Keypair:
        """Return the keypair object."""
        if not self.validkey:
            raise ValueError("Cannot access keypair from an invalid keypair.")
        return self._keypair

    def get_associated_token_address(self, mint: Pubkey) -> Pubkey:
        """Return the associated token account address for the given mint."""
        return get_associated_token_address(self.pubkey, mint)

    @staticmethod
    def _load_keypair(private_key: str) -> Keypair | None:
        """Load a Keypair object from a base58-encoded private key string."""
        try:
            private_key_bytes = base58.b58decode(private_key)
            return Keypair.from_bytes(private_key_bytes)
        except (ValueError, TypeError, AssertionError):
            return None

    def balance(self, rpc_url: str = "https://api.mainnet-beta.solana.com") -> float | None:
        """
        Retrieve the SOL balance (in SOL) using raw JSON-RPC and solders.pubkey.

        Parameters:
        - rpc_url (str): The RPC endpoint to query

        Returns:
        - float | None: Balance in SOL, or None on failure
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [str(self.pubkey)]
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(rpc_url, json=payload, headers=headers, timeout=10)
            result = response.json()

            if "result" in result and "value" in result["result"]:
                lamports = result["result"]["value"]
                return lamports / 1_000_000_000
        except Exception as e:
            print(f"Error fetching balance: {e}")
        return None