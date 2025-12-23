from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from models import AIChatRequest

T = TypeVar('T')


class StateBase(ABC, Generic[T]):
    """Abstract base class for managing chat state."""

    def __init__(self, chat_request: AIChatRequest) -> None:
        """Initialize state with an AIChatRequest.

        Args:
            chat_request (AIChatRequest): The chat request object.
        """
        self._chat_request = chat_request

    @abstractmethod
    def get_state(self) -> T:
        """Retrieve the current state.

        Returns:
            T: The current state.
        """
        pass

    @abstractmethod
    def set_state(self, state: T) -> None:
        """Set the current state.

        Args:
            state (T): The state to set.
        """
        pass
