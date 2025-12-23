from pydantic import BaseModel
from typing import Optional
import time
import pandas as pd
from openai import AzureOpenAI
from .alcs_prompt import Prompts as pt


class AzureOpenAIModel(BaseModel):
    open_api_key: str
    open_api_uri: str
    open_api_version: Optional[str] = '2024-10-21'
    chatgpt_model_id: str
    embedding_model_id: Optional[str] = None
    overlap_size: Optional[int] = 200
    content_field: Optional[str] = 'chunk'
    id_field: Optional[str] = 'id'


class AzureOpenAIService():

    default_embedding_model_id = "text-embedding-ada-002"

    def __init__(self, azure_openai_model: AzureOpenAIModel):

        self._azure_openai_model = azure_openai_model

        self._openai_client = AzureOpenAI(
            api_key=self._azure_openai_model.open_api_key,
            azure_endpoint=self._azure_openai_model.open_api_uri,
            api_version=self._azure_openai_model.open_api_version
        )

    def generate_embeddings(self,
                            entries: list,
                            embedding_model_id: str = default_embedding_model_id) -> list:

        embeddings = []

        # Generate embedding for each entry
        for entry in entries:
            # Create embedding
            try:
                response = self._openai_client.embeddings.create(input=entry, model=embedding_model_id)
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(f"Error: {e}")
                embeddings.append(-99999.99999)  # Error in generating embedding. Append Error code.

        return embeddings

    def generate_queries(self, entries: list[dict], query_type: str, query_count: int) -> list:

        queries = []

        # Generate related and unrelated queries for each entry
        for entry in entries:

            # Read content
            content = entry[self._azure_openai_model.content_field]

            # Remove the first and last overlap_size characters from the content, as it overlaps
            # with the previous and next chunk of text, to remove duplicate content
            if len(content) <= 2*self._azure_openai_model.overlap_size:
                continue

            content = content[self._azure_openai_model.overlap_size:-self._azure_openai_model.overlap_size]

            if (query_type == 'related' or query_type == 'both'):
                response_related = self._openai_client.chat.completions.create(
                    model=self._azure_openai_model.chatgpt_model_id,
                    messages=[
                        {
                            'role': 'system',
                            'content': pt.related_question_system_prompt.value
                        },
                        {
                            'role': 'assistant',
                            'content': pt.related_question_assistant_prompt.value.format(document=content,
                                                                                         ques_cnt=query_count)
                        }
                    ]
                )

            queries.extend(
                [
                    {'source': entry[self._azure_openai_model.id_field], 'question': question, 'type': 'related'}
                    for question in response_related.choices[0].message.content.splitlines()
                ]
            )

            if (query_type == 'unrelated' or query_type == 'both'):
                response_unrelated = self._openai_client.chat.completions.create(
                    model=self._azure_openai_model.chatgpt_model_id,
                    messages=[
                        {
                            'role': 'system',
                            'content': pt.unrelated_question_system_prompt.value
                        },
                        {
                            'role': 'assistant',
                            'content': pt.unrelated_question_assistant_prompt.value.format(document=content,
                                                                                           ques_cnt=query_count)
                        }
                    ]
                )

            queries.extend(
                [
                    {'source': entry[self._azure_openai_model.id_field], 'question': question, 'type': 'unrelated'}
                    for question in response_unrelated.choices[0].message.content.splitlines()
                ]
            )

            time.sleep(5)  # To avoid hitting the rate limit

        # Drop NaN from questions
        queries = pd.Series(queries).dropna().tolist()

        return queries

    def save_queries_to_file(self, queries: list, file_path: str) -> None:
        """
        Takes the questions that have been generated and outputs them to the file_path in CSV format.
        """

        # Convert List to DataFrame
        df_queries = pd.DataFrame(queries)

        # Save DataFrame to a CSV file
        df_queries.to_csv(file_path, index=False)  # Set index=False to exclude the index column
