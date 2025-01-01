import functools

from qcflow.exceptions import QCFlowTracingException


def raise_as_trace_exception(f):
    """
    A decorator to make sure that the decorated function only raises QCFlowTracingException.

    Any exceptions are caught and translated to QCFlowTracingException before exiting the function.
    This is helpful for upstream functions to handle tracing related exceptions properly.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            raise QCFlowTracingException(e) from e

    return wrapper
