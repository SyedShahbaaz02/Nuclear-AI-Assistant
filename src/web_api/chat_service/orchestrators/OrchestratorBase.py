from abc import ABC
from state import StateBase
from typing import AsyncIterator, TypeVar, Generic

T = TypeVar('T')


class OrchestratorBase(ABC, Generic[T]):
    """Abstract base class for agent orchestration.

    Provides a standard interface for orchestrating communication
    with multiple agents in a streaming response manner.
    """

    def __init__(self, state: StateBase[T]) -> None:
        """Initialize the orchestrator with configuration.

        Args:
            state (StateBase[T]): The state for orchestration.
        """
        self._state = state

    async def invoke_stream(self) -> AsyncIterator[str]:
        """Invoke the orchestration of communication with agents and stream responses.

        Yields:
            str: Streamed response items from the agents.
        """
        pass
