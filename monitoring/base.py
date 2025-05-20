# Import packages
from abc import ABC
from abc import abstractmethod
from collections.abc import Awaitable
from collections.abc import Callable

# Import local packages
from handler.base import TokenInfo

# Class 'BaseTokenListener'
class BaseTokenListener(ABC):
    """
    Abstract base class that defines the interface for token listeners used in the PumpAgent system.
    Token listeners are responsible for monitoring the Solana blockchain via different mechanisms
    (e.g., logs, blocks, geyser) and identifying newly created Pump.fun tokens. This class serves
    as the blueprint for any real-time listener implementation by enforcing a consistent contract
    through its abstract method `listen_for_tokens`.

    Parameters:
    - None (abstract base class)

    Returns:
    - None
    """

    # Function 'listen_for_tokens'
    @abstractmethod
    async def listen_for_tokens(self, token_callback: Callable[[TokenInfo], Awaitable[None]], match_string: str | None = None, creator_address: str | None = None) -> None:
        """
        Abstract method that must be implemented by subclasses to begin listening for newly launched tokens.
        When a matching token is detected, the provided asynchronous `token_callback` is called with a
        `TokenInfo` object. Optional filters allow narrowing results by token name pattern or creator address.
        This interface enables flexibility while ensuring consistent integration with PumpAgent.

        Parameters:
        - token_callback (Callable[[TokenInfo], Awaitable[None]]): Async function to be called when a token is detected.
        - match_string (str | None): Optional substring filter applied to token names or symbols.
        - creator_address (str | None): Optional Solana address to restrict tokens created by a specific user.

        Returns:
        - None
        """
        pass