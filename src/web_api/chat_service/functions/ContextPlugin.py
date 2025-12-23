import logging

from semantic_kernel.functions.kernel_function_decorator import kernel_function

from constants import ChatServiceConstants
from models import ReportabilityContext, Intent


logger = logging.getLogger(ChatServiceConstants.LOGGER_NAME.value + __name__)


class ContextPlugin:
    """Plugin to add used document IDs to the ReportabilityContext NUREGDocs list."""

    def __init__(self, state: ReportabilityContext) -> None:
        """Initializes the plugin with a ReportabilityContext.

        Args:
            context (ReportabilityContext): The context object to update.
        """
        self._state = state

    @kernel_function(
        name="set_intent",
        description="""
        Logs the intent that was detected from the users message.
        This is useful for tracking the user's intent during the reportability assessment.
        The intent can be 'reportability' or 'invalid'.
        """
    )
    def set_intent(self, intent: Intent) -> None:
        logger.debug(f"Setting intent in ReportabilityContext: {intent}")
        if not isinstance(intent, Intent):
            raise ValueError("Expected an Intent enum value.")
        self._state.intent = intent
