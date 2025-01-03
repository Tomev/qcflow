from typing import Optional, Union

from qcflow.gateway.base_models import RequestModel, ResponseModel
from qcflow.utils import IS_PYDANTIC_V2_OR_NEWER

_REQUEST_PAYLOAD_EXTRA_SCHEMA = {
    "example": {
        "input": ["hello", "world"],
    }
}


class RequestPayload(RequestModel):
    input: Union[str, list[str], list[int], list[list[int]]]

    class Config:
        if IS_PYDANTIC_V2_OR_NEWER:
            json_schema_extra = _REQUEST_PAYLOAD_EXTRA_SCHEMA
        else:
            schema_extra = _REQUEST_PAYLOAD_EXTRA_SCHEMA


class EmbeddingObject(ResponseModel):
    object: str = "embedding"
    embedding: Union[list[float], str]
    index: int


class EmbeddingsUsage(ResponseModel):
    prompt_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


_RESPONSE_PAYLOAD_EXTRA_SCHEMA = {
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "index": 0,
            "embedding": [
                0.017291732,
                -0.017291732,
                0.014577783,
                -0.02902633,
                -0.037271563,
                0.019333655,
                -0.023055641,
                -0.007359971,
                -0.015818445,
                -0.030654699,
                0.008348623,
                0.018312693,
                -0.017149571,
                -0.0044424757,
                -0.011165961,
                0.01018377,
            ],
        },
        {
            "object": "embedding",
            "index": 1,
            "embedding": [
                0.0060126893,
                -0.008691099,
                -0.0040095365,
                0.019889368,
                0.036211833,
                -0.0013270887,
                0.013401738,
                -0.0036735237,
                -0.0049594184,
                0.035229642,
                -0.03435084,
                0.019798903,
                -0.0006110424,
                0.0073793563,
                0.005657291,
                0.022487005,
            ],
        },
    ],
    "model": "text-embedding-ada-002-v2",
    "usage": {"prompt_tokens": 400, "total_tokens": 400},
}


class ResponsePayload(ResponseModel):
    object: str = "list"
    data: list[EmbeddingObject]
    model: str
    usage: EmbeddingsUsage

    class Config:
        if IS_PYDANTIC_V2_OR_NEWER:
            json_schema_extra = _RESPONSE_PAYLOAD_EXTRA_SCHEMA
        else:
            schema_extra = _RESPONSE_PAYLOAD_EXTRA_SCHEMA
