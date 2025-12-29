# Import packages
from abc import ABC
from abc import abstractmethod
from collections.abc import Awaitable
from collections.abc import Callable

# Import local packages
from handler.base import TokenInfo

# Class 'BaseTokenListener'
class BaseTokenListener(ABC):
    """ Class description """

    # Function 'listen_for_tokens'
    @abstractmethod
    async def listen_for_tokens(self, token_callback: Callable[[TokenInfo], Awaitable[None]], match_string: str | None = None, creator_address: str | None = None) -> None:
        """ Function description """
        pass