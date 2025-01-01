from unittest import mock

from llama_index.core.instrumentation import get_dispatcher
from llama_index.core.instrumentation.event_handlers.base import BaseEventHandler
from llama_index.core.instrumentation.span_handlers.base import BaseSpanHandler
from llama_index.llms.openai import OpenAI

import qcflow

from tests.llama_index.test_llama_index_tracer import _get_all_traces


def test_autolog_enable_tracing(multi_index):
    qcflow.llama_index.autolog()

    query_engine = multi_index.as_query_engine()

    query_engine.query("Hello")
    query_engine.query("Hola")

    traces = _get_all_traces()
    assert len(traces) == 2

    # Enabling autolog multiple times should not create duplicate spans
    qcflow.llama_index.autolog()
    qcflow.llama_index.autolog()

    chat_engine = multi_index.as_chat_engine()
    chat_engine.chat("Hello again!")

    assert len(_get_all_traces()) == 3

    qcflow.llama_index.autolog(disable=True)
    query_engine.query("Hello again!")

    traces = _get_all_traces()
    assert len(_get_all_traces()) == 3


def test_autolog_preserve_user_provided_handlers():
    user_span_handler = mock.MagicMock(spec=BaseSpanHandler)
    user_event_handler = mock.MagicMock(spec=BaseEventHandler)

    dsp = get_dispatcher()
    dsp.add_span_handler(user_span_handler)
    dsp.add_event_handler(user_event_handler)

    qcflow.llama_index.autolog()

    llm = OpenAI()
    llm.complete("Hello")

    assert user_span_handler in dsp.span_handlers
    assert user_event_handler in dsp.event_handlers
    user_span_handler.span_enter.assert_called_once()
    user_span_handler.span_exit.assert_called_once()
    assert user_event_handler.handle.call_count == 2  # LLM start + end

    traces = _get_all_traces()
    assert len(traces) == 1

    user_span_handler.reset_mock()
    user_event_handler.reset_mock()

    qcflow.llama_index.autolog(disable=True)

    assert user_span_handler in dsp.span_handlers
    assert user_event_handler in dsp.event_handlers

    llm.complete("Hello, again!")

    user_span_handler.span_enter.assert_called_once()
    user_span_handler.span_exit.assert_called_once()
    assert user_event_handler.handle.call_count == 2

    traces = _get_all_traces()
    assert len(traces) == 1


def test_autolog_should_not_generate_traces_during_logging_loading(single_index):
    qcflow.llama_index.autolog()

    with qcflow.start_run():
        model_info = qcflow.llama_index.log_model(
            single_index, "model", input_example="Hello", engine_type="query"
        )
    loaded = qcflow.pyfunc.load_model(model_info.model_uri)

    assert len(_get_all_traces()) == 0

    loaded.predict("Hello")
    assert len(_get_all_traces()) == 1
