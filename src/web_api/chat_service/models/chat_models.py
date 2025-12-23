from enum import Enum
from pydantic import ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from typing import Any, Optional


class ChatModel(KernelBaseModel):
    """
    ChatModel is a data model class that inherits from KernelBaseModel. It uses a custom configuration
    (ConfigDict) to control model behavior, including:

    - alias_generator: Uses the `to_camel` function to convert field names to camelCase for serialization.
    - populate_by_name: Allows population of fields by their Python names as well as aliases.
    - from_attributes: Enables model instantiation from attribute dictionaries.

    This configuration is useful for seamless integration with APIs or systems that require camelCase
    naming conventions and flexible data population.
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )


class AIChatRole(str, Enum):
    """
    Enumeration representing the possible roles in an AI chat conversation.

    Attributes:
        USER (str): Represents the user role in the conversation.
        ASSISTANT (str): Represents the AI assistant role in the conversation.
        SYSTEM (str): Represents the system role, typically used for instructions or context.
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AIChatFile(ChatModel):
    """
    Represent a file associated with an AI chat message.

    Attributes:
        content_type (str): The MIME type of the file content. Serialized as "contentType".
        data (bytes): The raw binary data of the file.
    """
    content_type: str = Field(serialization_alias="contentType")
    data: bytes


class AIChatMessage(ChatModel):
    """
    Represent a single message in the chat conversation.

    This model captures an individual message exchanged during a chat session,
    including the role of the sender (user, assistant, system), the content of the message,
    and any associated files or context.

    Attributes:
        role (AIChatRole): The role of the AI in the conversation (e.g., assistant, system).
        content (str): The textual content of the AI's message.
        context (Optional[dict[str, Any]]): Additional contextual information relevant to the message.
        files (Optional[list[AIChatFile]]): List of files associated with the message, if any.
    """
    role: AIChatRole
    content: str
    context: Optional[dict[str, Any]] = None
    files: Optional[list[AIChatFile]] = None


class AIChatMessageDelta(ChatModel):
    """
    Represents a partial (delta) AI chat message, used for streaming chat responses.

    Attributes:
        role (Optional[AIChatRole]): The role of the message sender (e.g., user, assistant, system).
        content (Optional[str]): The content of the chat message, which may be partial or incremental.
        context (Optional[dict[str, Any]]): Additional context or metadata associated with the message.
    """
    role: Optional[AIChatRole] = None
    content: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class AIChatCompletion(ChatModel):
    """
    Represents a chat completion response from an AI model.

    Attributes:
        message (AIChatMessage): The AI-generated chat message.
        session_state (Optional[Any]): The current state of the chat session, serialized as "sessionState".
        Defaults to None.
        context (Optional[dict[str, Any]]): Additional context information for the chat completion. Defaults to None.
    """
    message: AIChatMessage
    session_state: Optional[Any] = Field(serialization_alias="sessionState", default=None)
    context: Optional[dict[str, Any]] = None


class AIChatCompletionDelta(ChatModel):
    """
    Represents a delta (incremental update) in an AI chat completion response.

    Attributes:
        delta (AIChatMessageDelta): The incremental message content or update.
        session_state (Optional[Any]): The current session state, if any. Serialized as "sessionState".
        context (Optional[dict[str, Any]]): Additional context information relevant to the chat completion.
    """
    delta: AIChatMessageDelta
    session_state: Optional[Any] = Field(serialization_alias="sessionState", default=None)
    context: Optional[dict[str, Any]] = None


class AIChatCompletionOptions(ChatModel):
    """
    Configuration options for an AI chat completion.

    Attributes:
        context (Optional[dict[str, Any]]): Additional context information for the chat model.
        session_state (Optional[Any]): State for maintaining chat continuity, serialized as "sessionState".
    """
    context: Optional[dict[str, Any]] = None
    session_state: Optional[Any] = Field(serialization_alias="sessionState", default=None)


class AIChatError(ChatModel):
    """
    Represents an error returned by the AI chat service.

    Attributes:
        code (str): A machine-readable error code identifying the type of error.
        message (str): A human-readable description of the error.
    """
    code: str
    message: str


class AIChatErrorResponse(ChatModel):
    """
    Represents an error response for AI chat operations.
    It wraps an AIChatError inside a response object. It`s used as the top-level structure
    when returning errors from your API, making it clear that the response is an error and not a regular chat message.

    Attributes:
        error (AIChatError): The error details associated with the chat response.
    """
    error: AIChatError


class AIChatRequest(ChatModel):
    """
    Represents a request to the AI chat service.

    Attributes:
        messages (list[AIChatMessage]): A list of chat messages to be processed by the AI.
        session_state (Optional[Any]): The current session state, if any. Serialized as "sessionState".
        context (Optional[bytes]): Optional context data in bytes to provide additional information
        for the chat session.
    """
    messages: list[AIChatMessage]
    session_state: Optional[Any] = Field(serialization_alias="sessionState", default=None)
    context: Optional[Any] = None

    @field_validator('messages')
    @classmethod
    def messages_must_not_be_empty(cls, v):
        """
        Validate that the messages list is not empty.
        
        Raises:
            ValueError: If the messages list is empty.
        """
        if not v:
            raise ValueError('messages must not be empty')
        return v
