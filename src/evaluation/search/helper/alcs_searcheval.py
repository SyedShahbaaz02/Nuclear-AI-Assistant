# pip install scikit-learn
from pydantic import BaseModel
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from alcs_search import SearchType


# Define Threshold Values
class SearchTypeThreshold(BaseModel):
    FullText: Optional[float] = 25.0
    Vector: Optional[float] = 0.80
    Hybrid: Optional[float] = 0.027


class SearchEvalService():

    _eval_df = pd.DataFrame()

    def __init__(self, search_type_threshold: SearchTypeThreshold):
        self._search_type_threshold = search_type_threshold

    # Function to calculate cosine similarity
    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # Function to encode eval dataset results for metrics calculations
    def encode_eval_dataset(self, search_type: SearchType):

        # Get search type threshold value
        srch_th = getattr(self._search_type_threshold, search_type.name, None)

        self._eval_df['y_pred'] = self._eval_df.apply(lambda row:
                                                      1 if ((row['y_pred_score'] >= srch_th) &
                                                            (row['y_true_source'] == row['y_pred_source']))
                                                      else 0, axis=1)

        return srch_th

    def get_scores(self, search_type: SearchType, eval_dataset: list[dict]) -> dict:

        self._eval_df = pd.DataFrame(eval_dataset).dropna()

        # Encode dataset
        threshold = self.encode_eval_dataset(search_type=search_type)

        # Calculate metrics
        st_accuracy = accuracy_score(y_true=self._eval_df['y_true'], y_pred=self._eval_df['y_pred'])
        st_precision = precision_score(y_true=self._eval_df['y_true'], y_pred=self._eval_df['y_pred'])
        st_recall = recall_score(y_true=self._eval_df['y_true'], y_pred=self._eval_df['y_pred'])
        st_f1 = f1_score(y_true=self._eval_df['y_true'], y_pred=self._eval_df['y_pred'])
        st_cfm = confusion_matrix(y_true=self._eval_df['y_true'], y_pred=self._eval_df['y_pred']).flatten()
        self._eval_df['cosine_score'] = self._eval_df.apply(lambda row: self.cosine_similarity(
            np.array(row['y_true_vector']), np.array(row['y_pred_vector'])), axis=1)
        st_avg_cosine = np.mean(self._eval_df['cosine_score'])
        st_med_cosine = np.median(self._eval_df['cosine_score'])

        score_dict = {
            "SearchType": search_type.name,
            "Threshold": threshold,
            "Rows": len(self._eval_df),
            "Accuracy": st_accuracy,
            "Precision": st_precision,
            "Recall": st_recall,
            "F1Score": st_f1,
            "AvgCosine": st_avg_cosine,
            "MedianCosine": st_med_cosine,
            "TN": st_cfm[0],
            "FP": st_cfm[1],
            "FN": st_cfm[2],
            "TP": st_cfm[3]
        }

        return score_dict
