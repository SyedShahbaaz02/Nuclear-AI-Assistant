import httpx
import asyncio
from pydantic import ValidationError
from openai import AzureOpenAI
from .eval_models import (
    Recommendation,
    RecommendationScore,
    ParsedResponse,
    SubsectionClassification,
    ChatResponse,
    DataFrameColumnNames,
    all_reportable_subsections,
)
from .ai_chat_models import (
    AIChatRequest,
    AIChatMessage,
    AIChatRole,
    AIChatCompletionDelta,
    AIChatErrorResponse,
)


async def get_streamed_response(message: str, ask_licensing_chat_endpoint: str, api_timeout: float) -> ChatResponse:
    """
    Calls the API and constructs the full response from the streamed chunks.
    It traps exceptions and returns a RecommendationFailure object if an error occurs.
    We do this on a row by row basis as to not disrupt the entire process if one row fails.

    Args:
        message (str): The message to send to the API.
    Returns:
        str | RecommendationFailure: The response from the API or a failure object.
    """
    chat_response: ChatResponse = ChatResponse()
    request_start_time: float = asyncio.get_event_loop().time()
    try:
        chat_message = AIChatMessage(role=AIChatRole.USER, content=message)
        chat_request = AIChatRequest(messages=[chat_message])
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", ask_licensing_chat_endpoint, json=chat_request.model_dump(),
                headers=headers, timeout=api_timeout
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
                all_chunks = ""
                # combine all of the chunks before iterating over them
                async for chunk in response.aiter_text():
                    all_chunks += chunk
                    if chat_response.time_to_first_chunk == 0.0:
                        chat_response.time_to_first_chunk = asyncio.get_event_loop().time() - request_start_time
                try:
                    # Split the chunk by new lines and process each line separately
                    # This is a workaround for the issue where the API sends multiple deltas in one chunk
                    # and we need to handle them separately
                    deltas = all_chunks.splitlines()
                    for delta in deltas:
                        if not delta.strip():
                            continue
                        chat_completion_delta = AIChatCompletionDelta.model_validate_json(delta)
                        if chat_completion_delta.delta.content:
                            chat_response.response_text += chat_completion_delta.delta.content
                        if chat_completion_delta.context:
                            chat_response.context = chat_completion_delta.context["token_usage"]
                except ValidationError:
                    chat_error_response = AIChatErrorResponse.model_validate_json(delta)
                    raise Exception(f"API call failed with error: {chat_error_response.error.message}")

    except Exception as e:
        chat_response.error = e
    chat_response.time_to_completion = asyncio.get_event_loop().time() - request_start_time
    return chat_response


async def parse_response(
        chat_response: ChatResponse, openai_client: AzureOpenAI,
        open_ai_deployment_id: str, parsing_prompt: str) -> ParsedResponse:
    """
    Uses the OpenAI API to parse the recommendation message and return a structured response.
    It traps exceptions and returns a RecommendationFailure object if an error occurs.
    This is done to ensure that the entire process is not disrupted if one row fails.

    Args:
        message (str | RecommendationFailure): The message to parse.
    Returns:
        Recommendation | RecommendationFailure: The parsed recommendation or a failure object.
    """
    parsed_response: ParsedResponse = ParsedResponse()
    start_time: float = asyncio.get_event_loop().time()
    if chat_response.error:
        parsed_response.error = Exception("API failed to provide a response")
        return parsed_response
    try:
        response = openai_client.chat.completions.create(
            model=open_ai_deployment_id,
            messages=[
                {
                    'role': 'system',
                    'content': parsing_prompt.format(
                        message=chat_response.response_text
                    )
                }
            ],
            temperature=0,
        )
        parsed_response.recommendation = Recommendation.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        parsed_response.error = e

    parsed_response.time_to_completion = asyncio.get_event_loop().time() - start_time
    return parsed_response


def to_binary_int_array(subsections: list[str]) -> list[int]:
    """
    Converts a list of subsections to a binary integer array.
    Each subsection is represented by a 1 if it is present, or 0 if it is not.

    Args:
        subsections (list[str]): The list of subsections.
    Returns:
        list[int]: The binary integer array.
    """
    return [1 if subsection in subsections else 0 for subsection in all_reportable_subsections]


def get_recommendation_classification(row) -> RecommendationScore:
    """
    For each row in the DataFrame, evaluates the recommendation in comparison to what was expected and
    assigns the resulting score to a new column.
    Args:
        row (pd.Series): The row to process.
    Returns:
        RecommendationClassification: The classification of the recommendation.
    """
    state = RecommendationScore()
    chat_recommendation: ParsedResponse = row[DataFrameColumnNames.CHAT_RECOMMENDATION]
    api_response: ChatResponse = row[DataFrameColumnNames.CHAT_RESPONSE]
    if api_response.error:
        state.chat_failure = 1
    elif chat_recommendation.error:
        state.parsing_failure = 1
    else:
        expected_subsections = row[DataFrameColumnNames.SUBSECTIONS]
        recommended_subsections = chat_recommendation.recommendation.subsections

        state.y_true = to_binary_int_array(expected_subsections)
        state.y_pred = to_binary_int_array(recommended_subsections)

        # classify the expected reportable subsections
        for subsection in all_reportable_subsections:
            sub_class = SubsectionClassification(subsection=subsection)
            if subsection in expected_subsections and subsection in recommended_subsections:
                sub_class.true_positive = 1
            elif subsection in expected_subsections and subsection not in recommended_subsections:
                sub_class.false_negative = 1
            elif subsection not in expected_subsections and subsection in recommended_subsections:
                sub_class.false_positive = 1
            elif subsection not in expected_subsections and subsection not in recommended_subsections:
                sub_class.true_negative = 1
            state.add_subsection_classification(sub_class)
        # catch subsections that aren't in our list of expected subsections
        # and are in the recommended subsections
        for subsection in recommended_subsections:
            if subsection not in all_reportable_subsections:
                state.unexpected_subsections.append(subsection)

        state.tokens_by_agent = api_response.context

    return state


async def clean_ler_content(
        text: str, openai_client: AzureOpenAI, open_ai_deployment_id: str, clean_ler_prompt: str) -> str:
    """
    Removes references to CFR codes from the provided LER content using an AI model.

    Args:
        text (str): The LER content to clean.
        openai_client (AzureOpenAI): The Semantic Kernel OpenAI client instance.
        open_ai_deployment_id (str): The deployment ID for the OpenAI model.
        clean_ler_prompt (str): The prompt instructing the model how to clean the content.

    Returns:
        str: The cleaned LER content with CFR references removed.
    """
    response = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": clean_ler_prompt},
            {"role": "user", "content": text},
        ],
        model=open_ai_deployment_id,
    )
    return response.choices[0].message.content.strip()
