from dataclasses import dataclass
from typing import Optional, Union

import numpy as np

from qcflow.utils.annotations import experimental
from qcflow.utils.validation import _is_numeric


def standard_aggregations(scores):
    return {
        "mean": np.mean(scores),
        "variance": np.var(scores),
        "p90": np.percentile(scores, 90),
    }


@experimental
@dataclass
class MetricValue:
    """
    The value of a metric.


    Args:
        scores: The value of the metric per row
        justifications: The justification (if applicable) for the respective score
        aggregate_results: A dictionary mapping the name of the aggregation to its value
    """

    scores: Optional[Union[list[str], list[float]]] = None
    justifications: Optional[list[str]] = None
    aggregate_results: Optional[dict[str, float]] = None

    def __post_init__(self):
        if (
            self.aggregate_results is None
            and isinstance(self.scores, (list, tuple))
            and all(_is_numeric(score) for score in self.scores)
        ):
            self.aggregate_results = standard_aggregations(self.scores)
