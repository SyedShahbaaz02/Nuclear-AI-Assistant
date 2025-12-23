from enum import Enum
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from semantic_kernel.agents import ChatHistoryAgentThread
from semantic_kernel.contents import ChatHistory
from semantic_kernel.kernel_pydantic import KernelBaseModel
from typing import Any, Optional

from . import AIChatRequest, AIChatRole
from .search_models import SearchModelsBase


class Intent(Enum):
    """Intent is an enumeration representing the intent of a chat session."""
    INVALID = "invalid"
    REPORTABILITY = "reportability"


class ContextModel(KernelBaseModel):
    """
    ContextModel is a base model for context-related data in the chat service.

    Attributes:
        model_config (ConfigDict): Configuration for model serialization and deserialization.
            - alias_generator: Function to convert field names to camelCase.
            - populate_by_name: Allows population of fields by their Python names.
            - from_attributes: Enables model creation from object attributes.

    This model is intended to be extended by other context-specific models within the chat service.
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )


class Recommendation(ContextModel):
    """
    Recommendation is a context model used to represent a recommendation made by the system.

    Attributes:
        regulation_name (str): The name of the regulation related to the recommendation.
        confidence_score (float): The confidence score of the recommendation.
        reasoning (str): The reasoning behind the recommendation.
    """
    regulation_name: str = Field(..., description="The name of the regulation related to the recommendation.")
    confidence_score: float = Field(..., description="Value between 0 and 1 representing the confidence score.")
    reasoning: str = Field(..., description="The reasoning behind the recommendation.")


class TokenUsage(ContextModel):
    """
    TokenUsage is a context model used to track token usage statistics.

    Attributes:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        total_tokens (int): The total number of tokens used.
    """
    agent_name: Optional[str] = Field(None, description="The name of the agent associated with the token usage.")
    prompt_tokens: int = Field(0, description="The number of tokens used in the prompt.")
    completion_tokens: int = Field(0, description="The number of tokens used in the completion.")


class ReportabilityContext(ContextModel):
    """
    ReportabilityContext is a context model used to manage the state of a chat session for reportability analysis.

    Attributes:
        current_input_index (int): The index of the current input in the chat session. Defaults to 0.
        message_history (list[AIChatMessage]): A list containing the history of AI chat messages in the session.
        streaming_response (Optional[Any]): An optional field to store the current streaming response, if any.
        chat_request (Optional[AIChatRequest]): The AI chat request associated with the session.
        all_chunks (str): A string containing all chunks of the chat session.
        intent (Intent): The intent of the chat session, defaulting to an empty string.
        user_input_needed (bool): A flag indicating whether user input is needed in the session.
        recommendations (list[Recommendation]): A list of recommendations made during the session.
        token_usage (list[TokenUsage]): A list of token usage statistics for the session.
        include_eval_content (bool): A flag indicating whether to include evaluation content in the session.
    """
    current_input_index: int = 0
    message_history: ChatHistory = ChatHistory()
    plugin_results: list[SearchModelsBase] = []
    chat_request: Optional[AIChatRequest] = None
    all_chunks: str = ""
    intent: Intent = ""
    user_input_needed: bool = False
    recommendations: list[Recommendation] = []
    token_usage: list[TokenUsage] = []
    include_eval_content: bool = False

    def __init__(self, **data: Any) -> None:
        """
        Initialize ReportabilityContext with optional data.

        Args:
            **data: Arbitrary keyword arguments to initialize the context.
        """
        super().__init__(**data)
        self._transform_chat_request()

    def _transform_chat_request(self) -> None:
        if self.chat_request:
            for message in self.chat_request.messages:
                if message.role == AIChatRole.USER:
                    self.message_history.add_user_message(message.content)
                elif message.role == AIChatRole.ASSISTANT:
                    self.message_history.add_assistant_message(message.content)

    def get_agent_thread(self) -> ChatHistoryAgentThread:
        """
        Retrieves the agent thread from the message history.

        Returns:
            ChatHistoryAgentThread: The agent thread containing the chat history.
        """
        return ChatHistoryAgentThread(
            thread_id=self.chat_request.session_state,
        )
