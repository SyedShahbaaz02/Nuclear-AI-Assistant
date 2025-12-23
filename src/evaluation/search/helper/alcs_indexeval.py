from pydantic import BaseModel
from typing import List
import numpy as np
import pandas as pd


class IndexEvalModel(BaseModel):
    beta_factor: int
    num_docs: int


class IndexEvalService():

    def __init__(self, index_eval_model: IndexEvalModel):
        self.beta = index_eval_model.beta_factor
        self.num_docs = index_eval_model.num_docs

    def encode_result(self, predicted: list, target: list) -> str:
        pos_list = list()
        for ts in target:
            for idx, ps in enumerate(predicted):
                if any([ref in ts for ref in ps]):
                    pos_list.append(idx)
                    break

        pos_list = sorted(pos_list)
        return '|'.join([str(x) for x in pos_list]) if pos_list else '999'

    def calculate_scores_at_k(self, fetched: str) -> list:
        positions = [int(x) for x in fetched.split('|')]
        positions = sorted(list(set(positions)))  # Remove duplicates and sort (corner case)

        precision_at_k = [0] * (1 + self.num_docs)
        recall_at_k = [0] * (1 + self.num_docs)
        fbeta_at_k = [0] * (1 + self.num_docs)
        listed = 0

        for k in range(self.num_docs):
            if k in positions:
                listed += 1
            precision_at_k[k + 1] = listed / (k + 1)
            recall_at_k[k + 1] = listed / len(positions)
            if precision_at_k[k + 1] + recall_at_k[k + 1] > 0:
                fbeta_at_k[k + 1] = ((1 + self.beta ** 2) * precision_at_k[k + 1] * recall_at_k[k + 1]) / \
                                ((self.beta ** 2 * precision_at_k[k + 1]) + recall_at_k[k + 1])
        return [precision_at_k, recall_at_k, fbeta_at_k]

    def calculate_rr(self, fetched: str) -> float:
        positions = [int(x) for x in fetched.split('|')]
        if not positions or positions[0] > self.num_docs:
            return 0.0
        return 1.0 / (positions[0] + 1)

    def calculate_metrics(self, eval_dataset: pd.DataFrame) -> dict:
        patk = [0] * (1 + self.num_docs)
        ratk = [0] * (1 + self.num_docs)
        fatk = [0] * (1 + self.num_docs)
        mrr = 0.0
        cnt = 0
        for idx, row in eval_dataset.iterrows():
            res = row['results']
            if not res:
                continue
            row_scores = self.calculate_scores_at_k(res)
            patk = [x + y for x, y in zip(patk, row_scores[0])]
            ratk = [x + y for x, y in zip(ratk, row_scores[1])]
            fatk = [x + y for x, y in zip(fatk, row_scores[2])]

            mrr += self.calculate_rr(res)
            cnt += 1

        patk = [x / cnt for x in patk]
        ratk = [x / cnt for x in ratk]
        fatk = [x / cnt for x in fatk]
        mrr /= cnt if cnt > 0 else 0

        metrics = {
            'Precision@K': patk,
            'Recall@K': ratk,
            'Fbeta@K': fatk,
            'MRR': mrr
        }

        return metrics

    def get_score_stats(self, scores_matrix: List[List[float]]) -> List[List[float]]:
        if not scores_matrix or len(scores_matrix) < 2:
            return [list(), list()]
        matrix = np.array(scores_matrix)
        averages = np.mean(matrix, axis=0)
        stdevs = np.std(matrix, axis=0)
        return [averages, stdevs]

    def get_k_distribution(self, positions: List[str]) -> List[float]:
        if not positions:
            return []

        kcnt = [0] * (self.num_docs + 1)
        for x in positions:
            if '|' in x:
                continue  # Skip if multiple positions are given
            pos = min(int(x), len(kcnt) - 1)
            kcnt[pos] += 1
        return kcnt


