# Import libraries
import base58

# Import packages
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address


# Class 'Wallet'
class Wallet:
    """
    This class encapsulates a Solana wallet based on a base58-encoded private key. It provides
    convenient access to the wallet’s public key, keypair, and associated token addresses for SPL tokens.
    The wallet can be used to sign transactions, derive token accounts, and interact securely
    with Solana programs. It ensures that the private key is decoded and converted into a usable keypair
    on initialization.

    Parameters:
    - private_key (str): Base58-encoded private key string for the wallet.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, private_key: str):
        """
        Initializes the Wallet instance by decoding the given base58 private key and generating
        a Keypair object. This keypair is stored internally and used to derive the public key,
        sign transactions, and query associated token accounts. The private key string is stored
        as a reference for logging or export if needed but never directly exposed or reused for
        computation beyond initial load.

        Parameters:
        - private_key (str): The base58-encoded private key to load the wallet.

        Returns:
        - None
        """
        self._private_key = private_key
        self._keypair = self._load_keypair(private_key)

    # Function 'pubkey'
    @property
    def pubkey(self) -> Pubkey:
        """
        Returns the public key associated with the wallet’s keypair. This value is used to identify
        the wallet on-chain and is commonly required for signing, interacting with smart contracts,
        and querying balances. It is derived from the loaded keypair and cached for repeated access.

        Parameters:
        - None

        Returns:
        - Pubkey: The public key corresponding to the loaded private key.
        """
        return self._keypair.pubkey()

    # Function 'keypair'
    @property
    def keypair(self) -> Keypair:
        """
        Provides access to the underlying Keypair object representing the wallet's full cryptographic identity.
        This object can be used to sign transactions and interact with lower-level Solana APIs that require
        keypair input. It is generated once during initialization and reused throughout the wallet's lifecycle.

        Parameters:
        - None

        Returns:
        - Keypair: The Solana keypair derived from the provided private key.
        """
        return self._keypair

    # Function 'get_associated_token_address'
    def get_associated_token_address(self, mint: Pubkey) -> Pubkey:
        """
        Computes the associated token account address for the wallet’s public key and the specified SPL token mint.
        This is useful for querying balances, performing token transfers, or preparing instructions
        for token interactions. The address is derived deterministically and adheres to Solana's
        token program standards.

        Parameters:
        - mint (Pubkey): The public key of the SPL token mint to derive the associated account for.

        Returns:
        - Pubkey: The derived associated token address for the wallet and given mint.
        """
        return get_associated_token_address(self.pubkey, mint)

    # Function '_load_keypair'
    @staticmethod
    def _load_keypair(private_key: str) -> Keypair:
        """
        Decodes a base58-encoded private key string into bytes and initializes a Solana Keypair.
        This is a static method used internally during Wallet initialization to convert persistent
        or user-provided private keys into a usable cryptographic object. It assumes the key is
        properly formatted and securely passed to avoid runtime decoding errors.

        Parameters:
        - private_key (str): Base58 string representing the full private key.

        Returns:
        - Keypair: A Keypair instance constructed from the decoded private key bytes.
        """
        private_key_bytes = base58.b58decode(private_key)
        return Keypair.from_bytes(private_key_bytes)