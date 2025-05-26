# Import libraries
import base58

# Import packages
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address


# Class 'Wallet'
class Wallet:
    """ Class description """

    # Class initialization
    def __init__(self, private_key: str):
        """ Initializer description """
        self._private_key = private_key
        self._keypair = self._load_keypair(private_key)

    # Function 'pubkey'
    @property
    def pubkey(self) -> Pubkey:
        """ Function description """
        return self._keypair.pubkey()

    # Function 'keypair'
    @property
    def keypair(self) -> Keypair:
        """ Function description """
        return self._keypair

    # Function 'get_associated_token_address'
    def get_associated_token_address(self, mint: Pubkey) -> Pubkey:
        """ Function description """
        return get_associated_token_address(self.pubkey, mint)

    # Function '_load_keypair'
    @staticmethod
    def _load_keypair(private_key: str) -> Keypair:
        """ Function description """
        private_key_bytes = base58.b58decode(private_key)
        return Keypair.from_bytes(private_key_bytes)