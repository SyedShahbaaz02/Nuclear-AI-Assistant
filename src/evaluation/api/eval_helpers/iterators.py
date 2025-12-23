import asyncio
from openai import AzureOpenAI
from .eval_models import (
    DataFrameColumnNames,
)
from .workers import (
    get_streamed_response,
    parse_response,
    get_recommendation_classification
)
import pandas as pd


async def add_response(
        df: pd.DataFrame, throttle_time: float, ask_licensing_chat_endpoint: str, api_timeout: float) -> pd.DataFrame:
    """
    Calls the API for each row in the DataFrame and adds the response to a new column.
    Args:
        df (pd.DataFrame): The DataFrame to process.
        throttle_time (float): The time to wait between API calls.
        ask_licensing_chat_endpoint (str): The endpoint for the API.
        api_timeout (float): The timeout for the API call.
    Returns:
        pd.DataFrame: The DataFrame with the API responses added.
    """
    responses = []
    for _, row in df.iterrows():
        responses.append(
            await get_streamed_response(row[DataFrameColumnNames.CONTENT], ask_licensing_chat_endpoint, api_timeout))
        await asyncio.sleep(throttle_time)
    df[DataFrameColumnNames.CHAT_RESPONSE.value] = responses
    return df


async def add_recommendation(
        df: pd.DataFrame, throttle_time: float, openai_client: AzureOpenAI,
        open_ai_deployment_id: str, parsing_prompt
        ) -> pd.DataFrame:
    """
    Parses the response from the API for each row in the DataFrame and adds the results to a new column

    Args:
        df (pd.DataFrame): The DataFrame to process.
        throttle_time (float): The time to wait between API calls.
        openai_client (AzureOpenAI): The OpenAI client to use for API calls.
        open_ai_deployment_id (str): The deployment ID for the OpenAI model.
        parsing_prompt (str): The prompt to use for parsing the response.
    Returns:
        pd.DataFrame: The DataFrame with the recommendation added.
    """
    parsed_recommendations = []
    for _, row in df.iterrows():
        parsed_recommendations.append(
            await parse_response(
                row[DataFrameColumnNames.CHAT_RESPONSE], openai_client, open_ai_deployment_id,
                parsing_prompt))
        await asyncio.sleep(throttle_time)
    df[DataFrameColumnNames.CHAT_RECOMMENDATION.value] = parsed_recommendations
    return df


def add_recommendation_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row in the DataFrame, evaluates the recommendation in comparison to what was expected and
    assigns the resulting score to a new column.

    Args:
        df (pd.DataFrame): The DataFrame to process.
    Returns:
        pd.DataFrame: The DataFrame with the score added.
    """
    scores = []
    for _, row in df.iterrows():
        scores.append(get_recommendation_classification(row))
    df[DataFrameColumnNames.SCORE.value] = scores
    return df
