import pandas as pd
import pytest

import qcflow
import qcflow.utils
import qcflow.utils.autologging_utils
from qcflow.metrics import latency
from qcflow.tracing.constant import TraceMetadataKey

from tests.openai.test_openai_evaluate import purge_traces
from tests.tracing.helper import get_traces, reset_autolog_state  # noqa: F401

_EVAL_DATA = pd.DataFrame(
    {
        "inputs": [
            "What is QCFlow?",
            "What is Spark?",
        ],
        "ground_truth": [
            "QCFlow is an open-source platform to manage the ML lifecycle.",
            "Spark is a unified analytics engine for big data processing.",
        ],
    }
)


@pytest.mark.parametrize(
    "config",
    [
        None,
        {"log_traces": False},
        {"log_traces": True},
    ],
)
@pytest.mark.usefixtures("reset_autolog_state")
def test_llama_index_evaluate(single_index, config):
    if config:
        qcflow.llama_index.autolog(**config)
        qcflow.openai.autolog(**config)  # Our model contains OpenAI call as well

    is_trace_disabled = config and not config.get("log_traces", True)
    is_trace_enabled = config and config.get("log_traces", True)

    engine = single_index.as_query_engine()

    def model(inputs):
        return [engine.query(question) for question in inputs["inputs"]]

    with qcflow.start_run() as run:
        eval_result = qcflow.evaluate(
            model,
            data=_EVAL_DATA,
            targets="ground_truth",
            extra_metrics=[latency()],
        )
    assert eval_result.metrics["latency/mean"] > 0

    # Traces should not be logged when disabled explicitly
    if is_trace_disabled:
        assert len(get_traces()) == 0
    else:
        assert len(get_traces()) == 2
        assert run.info.run_id == get_traces()[0].info.request_metadata[TraceMetadataKey.SOURCE_RUN]

    purge_traces()

    # Test original autolog configs is restored
    engine.query("text")
    assert len(get_traces()) == (1 if is_trace_enabled else 0)


@pytest.mark.parametrize("engine_type", ["query", "chat"])
@pytest.mark.usefixtures("reset_autolog_state")
def test_llama_index_pyfunc_evaluate(engine_type, single_index):
    with qcflow.start_run() as run:
        model_info = qcflow.llama_index.log_model(
            single_index,
            "llama_index",
            engine_type=engine_type,
        )

        eval_result = qcflow.evaluate(
            model_info.model_uri,
            data=_EVAL_DATA,
            targets="ground_truth",
            extra_metrics=[latency()],
        )
    assert eval_result.metrics["latency/mean"] > 0

    # Traces should be automatically enabled during evaluation
    assert len(get_traces()) == 2
    assert run.info.run_id == get_traces()[0].info.request_metadata[TraceMetadataKey.SOURCE_RUN]


@pytest.mark.parametrize("globally_disabled", [True, False])
@pytest.mark.usefixtures("reset_autolog_state")
def test_llama_index_evaluate_should_not_log_traces_when_disabled(single_index, globally_disabled):
    if globally_disabled:
        qcflow.autolog(disable=True)
    else:
        qcflow.llama_index.autolog(disable=True)
        qcflow.openai.autolog(disable=True)  # Our model contains OpenAI call as well

    def model(inputs):
        engine = single_index.as_query_engine()
        return [engine.query(question) for question in inputs["inputs"]]

    with qcflow.start_run():
        eval_result = qcflow.evaluate(
            model,
            data=_EVAL_DATA,
            targets="ground_truth",
            extra_metrics=[latency()],
        )
    assert eval_result.metrics["latency/mean"] > 0
    assert len(get_traces()) == 0
