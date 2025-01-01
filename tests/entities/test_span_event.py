from qcflow.entities import SpanEvent
from qcflow.exceptions import QCFlowException


def test_from_exception():
    exception = QCFlowException("test")
    span_event = SpanEvent.from_exception(exception)
    assert span_event.name == "exception"
    assert span_event.attributes["exception.message"] == "test"
    assert span_event.attributes["exception.type"] == "QCFlowException"
    assert span_event.attributes["exception.stacktrace"] is not None
