qcflow
======

.. automodule:: qcflow
    :members:
    :undoc-members:
    :exclude-members: QCFlowClient, trace, start_span, get_trace, search_traces, get_current_active_span, get_last_active_trace


.. _qcflow-tracing-fluent-python-apis:

QCFlow Tracing APIs
===================

The ``qcflow`` module provides a set of high-level APIs for `QCFlow Tracing <../llms/tracing/index.html>`_. For the detailed
guidance on how to use these tracing APIs, please refer to the `Tracing Fluent APIs Guide <../llms/tracing/index.html#tracing-fluent-apis>`_.

For some advanced use cases such as multi-threaded application, instrumentation via callbacks, you may need to use
the low-level tracing APIs :py:class:`QCFlowClient <qcflow.client.QCFlowClient>` provides.
For detailed guidance on how to use the low-level tracing APIs, please refer to the `Tracing Client APIs Guide <../llms/tracing/index.html#tracing-client-apis>`_.

.. autofunction:: qcflow.trace
.. autofunction:: qcflow.start_span
.. autofunction:: qcflow.get_trace
.. autofunction:: qcflow.search_traces
.. autofunction:: qcflow.get_current_active_span
.. autofunction:: qcflow.get_last_active_trace
.. automodule:: qcflow.tracing
    :members:
    :undoc-members:
    :noindex:
