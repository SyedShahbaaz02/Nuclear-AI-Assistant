from typing import Optional

from .StateBase import StateBase
from models import AIChatRequest, ReportabilityContext


class MemoryState(StateBase[ReportabilityContext]):
    """In-memory implementation of StateBase for ReportabilityContext."""

    def __init__(self, chat_request: AIChatRequest) -> None:
        """Initialize MemoryState with an AIChatRequest.

        Args:
            chat_request (AIChatRequest): The chat request object.
        """
        super().__init__(chat_request)
        self._state: ReportabilityContext = ReportabilityContext(chat_request=chat_request)

    def get_state(self) -> Optional[ReportabilityContext]:
        """Retrieve the current ReportabilityContext state.

        Returns:
            Optional[ReportabilityContext]: The current state or None if unset.
        """
        return self._state

    def set_state(self, state: ReportabilityContext) -> None:
        """Set the current ReportabilityContext state.

        Args:
            state (ReportabilityContext): The state to set.
        """
        self._state = state
