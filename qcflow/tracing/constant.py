# NB: These keys are placeholders and subject to change
class TraceMetadataKey:
    INPUTS = "qcflow.traceInputs"
    OUTPUTS = "qcflow.traceOutputs"
    SOURCE_RUN = "qcflow.sourceRun"


class TraceTagKey:
    TRACE_NAME = "qcflow.traceName"
    EVAL_REQUEST_ID = "eval.requestId"
    TRACE_SPANS = "qcflow.traceSpans"


# A set of reserved attribute keys
class SpanAttributeKey:
    EXPERIMENT_ID = "qcflow.experimentId"
    REQUEST_ID = "qcflow.traceRequestId"
    INPUTS = "qcflow.spanInputs"
    OUTPUTS = "qcflow.spanOutputs"
    SPAN_TYPE = "qcflow.spanType"
    FUNCTION_NAME = "qcflow.spanFunctionName"
    START_TIME_NS = "qcflow.spanStartTimeNs"
    # these attributes are for standardized chat messages and tool definitions
    # in CHAT_MODEL and LLM spans. they are used for rendering the rich chat
    # display in the trace UI, as well as downstream consumers of trace data
    # such as evaluation
    CHAT_MESSAGES = "qcflow.chat.messages"
    CHAT_TOOLS = "qcflow.chat.tools"


# All storage backends are guaranteed to support key values up to 250 characters
MAX_CHARS_IN_TRACE_INFO_METADATA_AND_TAGS = 250
TRUNCATION_SUFFIX = "..."

# Trace request ID must have the prefix "tr-" appended to the OpenTelemetry trace ID
TRACE_REQUEST_ID_PREFIX = "tr-"

# Schema version of traces and spans.
TRACE_SCHEMA_VERSION = 2

# Key for the trace schema version in the trace. This key is also used in
# Databricks model serving to be careful when modifying it.
TRACE_SCHEMA_VERSION_KEY = "qcflow.trace_schema.version"
