import json

from qcflow.environment_variables import QCFLOW_RUN_CONTEXT
from qcflow.tracking.context.abstract_context import RunContextProvider

# The constant QCFLOW_RUN_CONTEXT_ENV_VAR is marked as @developer_stable
QCFLOW_RUN_CONTEXT_ENV_VAR = QCFLOW_RUN_CONTEXT.name


class SystemEnvironmentContext(RunContextProvider):
    def in_context(self):
        return QCFLOW_RUN_CONTEXT.defined

    def tags(self):
        return json.loads(QCFLOW_RUN_CONTEXT.get())
