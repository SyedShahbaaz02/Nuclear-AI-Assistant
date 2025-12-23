from typing import Optional, Any
from enum import Enum
from sklearn.metrics import precision_score, recall_score, f1_score
from pydantic import ConfigDict, Field, BaseModel
from pydantic.alias_generators import to_camel


class DataFrameColumnNames(str, Enum):
    LER_NUMBER = "ler_number"
    REPORTABLE = "reportable"
    CONTENT = "content"
    SUBSECTIONS = "subsections"
    CHAT_RECOMMENDATION = "chat_recommendation"
    CHAT_RESPONSE = "chat_response"
    SCORE = "score"


class RecommendationBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
        arbitrary_types_allowed=True,  # Allow arbitrary types like Exception
    )


class Recommendation(RecommendationBaseModel):
    reportable: bool
    subsections: list[str]


class RecommendationFailureDuring(str, Enum):
    API_CALL = "api_call"
    RESPONSE_PARSING = "response_parsing"


class Classification(RecommendationBaseModel):
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0
    true_negative: int = 0


class SubsectionClassification(Classification):
    subsection: str


class ScoreAggregator(RecommendationBaseModel):
    total_records: int = 0
    y_true: list[list[int]] = Field(default_factory=list)
    y_pred: list[list[int]] = Field(default_factory=list)
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0
    true_negative: int = 0
    chat_failure: int = 0
    parsing_failure: int = 0
    unexpected_subsections: set[str] = Field(default_factory=set)
    tokens_by_agent: list[dict[str, Any]] = Field(default_factory=list)

    def summarize_token_counts(self, tokens_update: list[dict[str, Any]]) -> None:
        for token in tokens_update:
            result = None
            for item in self.tokens_by_agent:
                if item['agent_name'] == token['agent_name']:
                    result = item
                    break

            if result is None:
                self.tokens_by_agent.append(token)
            else:
                result["prompt_tokens"] += token["prompt_tokens"]
                result["completion_tokens"] += token["completion_tokens"]


class RecommendationScore(Classification):
    y_true: list[int] = Field(default_factory=list)
    y_pred: list[int] = Field(default_factory=list)
    chat_failure: int = 0
    parsing_failure: int = 0
    subsection_classifications: list[SubsectionClassification] = Field(default_factory=list)
    unexpected_subsections: list[str] = Field(default_factory=list)
    tokens_by_agent: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return self.chat_failure > 0 or self.parsing_failure > 0

    def add_subsection_classification(self, sub_class: SubsectionClassification) -> None:
        self.subsection_classifications.append(sub_class)
        self.true_positive += sub_class.true_positive
        self.false_positive += sub_class.false_positive
        self.false_negative += sub_class.false_negative
        self.true_negative += sub_class.true_negative


class EvalResults(RecommendationBaseModel):
    total_score: ScoreAggregator = Field(default_factory=ScoreAggregator)
    total_records: int = 0

    @property
    def accuracy(self) -> float:
        denominator = (
            self.total_score.true_positive
            + self.total_score.true_negative
            + self.total_score.false_positive
            + self.total_score.false_negative
        )
        return (
            self.total_score.true_positive + self.total_score.true_negative) / denominator if denominator > 0 else 0.0

    @property
    def total_errors(self) -> int:
        return self.total_score.chat_failure + self.total_score.parsing_failure

    @property
    def total_success(self) -> int:
        return self.total_records - self.total_errors

    @property
    def error_rate(self) -> float:
        if self.total_records > 0:
            return self.total_errors / self.total_records
        return 0.0

    @property
    def success_rate(self) -> float:
        if self.total_records > 0:
            return self.total_success / self.total_records
        return 0.0

    @property
    def micro_precision(self) -> float:
        return precision_score(self.total_score.y_true, self.total_score.y_pred, average='micro')

    @property
    def micro_recall(self) -> float:
        return recall_score(self.total_score.y_true, self.total_score.y_pred, average='micro')

    @property
    def micro_f1_score(self) -> float:
        return f1_score(self.total_score.y_true, self.total_score.y_pred, average='micro')


class ChatResponse(RecommendationBaseModel):
    response_text: str = ""
    time_to_first_chunk: float = 0.0
    time_to_completion: float = 0.0
    error: Optional[Exception] = None
    context: Optional[list[dict[str, Any]]] = None


class ParsedResponse(RecommendationBaseModel):
    recommendation: Optional[Recommendation] = None
    error: Optional[Exception] = None
    time_to_completion: float = 0.0


class ProcessingTimes(RecommendationBaseModel):
    total_records: int = 0
    time_to_first_chunk: float = 0.0
    time_to_completion: float = 0.0
    time_to_parsing_completion: float = 0.0
    time_to_chat_error: float = 0.0
    time_to_parsing_error: float = 0.0

    @property
    def mean_time_to_first_chunk(self) -> float:
        if self.total_records > 0:
            return self.time_to_first_chunk / self.total_records
        return 0.0

    @property
    def mean_time_to_completion(self) -> float:
        if self.total_records > 0:
            return self.time_to_completion / self.total_records
        return 0.0

    @property
    def mean_time_to_parsing_completion(self) -> float:
        if self.total_records > 0:
            return self.time_to_parsing_completion / self.total_records
        return 0.0

    @property
    def mean_time_to_chat_error(self) -> float:
        if self.total_records > 0:
            return self.time_to_chat_error / self.total_records
        return 0.0

    @property
    def mean_time_to_parsing_error(self) -> float:
        if self.total_records > 0:
            return self.time_to_parsing_error / self.total_records
        return 0.0


# Limiting to subsections of 10 CFR 50.72/73 for now (values pulled from an LER/ENS) need to verify if these are
# the only ones that are reportable

# Comment out this section to analyze LERs
# all_reportable_subsections = [
#    "10 CFR 50.73(a)(2)(i)(A)",
#    "10 CFR 50.73(a)(2)(i)(B)",
#    "10 CFR 50.73(a)(2)(i)(C)",
#    "10 CFR 50.73(a)(2)(ii)(A)",
#    "10 CFR 50.73(a)(2)(ii)(B)",
#    "10 CFR 50.73(a)(2)(iii)",
#    "10 CFR 50.73(a)(2)(iv)(A)",
#    "10 CFR 50.73(a)(2)(v)(A)",
#    "10 CFR 50.73(a)(2)(v)(B)",
#    "10 CFR 50.73(a)(2)(v)(C)",
#    "10 CFR 50.73(a)(2)(v)(D)",
#    "10 CFR 50.73(a)(2)(vii)",
#    "10 CFR 50.73(a)(2)(viii)A",
#    "10 CFR 50.73(a)(2)(viii)B",
#    "10 CFR 50.73(a)(2)(ix)(A)",
#    "10 CFR 50.73(a)(2)(x)",
# ]

all_reportable_subsections = [
    "10 CFR 50.72(b)(1)",

    "10 CFR 50.72(b)(2)(i)",
    "10 CFR 50.72(b)(2)(iv)(A)",
    "10 CFR 50.72(b)(2)(iv)(B)",
    "10 CFR 50.72(b)(2)(xi)",

    "10 CFR 50.72(b)(3)(ii)(A)",
    "10 CFR 50.72(b)(3)(ii)(B)",

    "10 CFR 50.72(b)(3)(iv)(A)",
    "10 CFR 50.72(b)(3)(iv)(B)",


    "10 CFR 50.72(b)(3)(v)(A)",
    "10 CFR 50.72(b)(3)(v)(B)",
    "10 CFR 50.72(b)(3)(v)(C)",
    "10 CFR 50.72(b)(3)(v)(D)",

    "10 CFR 50.72(b)(3)(vi)",
    "10 CFR 50.72(b)(3)(xii)",
    "10 CFR 50.72(b)(3)(xiii)",
    "10 CFR 50.73(a)(2)(i)(A)",
    "10 CFR 50.73(a)(2)(i)(B)",
    "10 CFR 50.73(a)(2)(i)(C)",
    "10 CFR 50.73(a)(2)(ii)(A)",
    "10 CFR 50.73(a)(2)(ii)(B)",
    "10 CFR 50.73(a)(2)(iii)",
    "10 CFR 50.73(a)(2)(iv)(A)",
    "10 CFR 50.73(a)(2)(v)(A)",
    "10 CFR 50.73(a)(2)(v)(B)",
    "10 CFR 50.73(a)(2)(v)(C)",
    "10 CFR 50.73(a)(2)(v)(D)",
    "10 CFR 50.73(a)(2)(vii)",
    "10 CFR 50.73(a)(2)(viii)A",
    "10 CFR 50.73(a)(2)(viii)B",
    "10 CFR 50.73(a)(2)(ix)(A)",
    "10 CFR 50.73(a)(2)(x)",
]
