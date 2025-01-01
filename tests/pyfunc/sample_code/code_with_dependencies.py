import os

import qcflow
from qcflow.models import set_model, set_retriever_schema
from qcflow.pyfunc import PythonModel

test_trace = os.environ.get("TEST_TRACE", "true").lower() == "true"


class MyModel(PythonModel):
    def _call_retriver(self, id):
        return f"Retriever called with ID: {id}. Output: 42."

    def predict(self, context, model_input):
        return f"Input: {model_input}. {self._call_retriver(model_input)}"

    def predict_stream(self, context, model_input, params=None):
        yield f"Input: {model_input}. {self._call_retriver(model_input)}"


class MyModelWithTrace(PythonModel):
    def _call_retriver(self, id):
        return f"Retriever called with ID: {id}. Output: 42."

    @qcflow.trace
    def predict(self, context, model_input):
        return f"Input: {model_input}. {self._call_retriver(model_input)}"

    @qcflow.trace
    def predict_stream(self, context, model_input, params=None):
        yield f"Input: {model_input}. {self._call_retriver(model_input)}"


model = MyModelWithTrace() if test_trace else MyModel()
set_model(model)
set_retriever_schema(
    primary_key="primary-key",
    text_column="text-column",
    doc_uri="doc-uri",
    other_columns=["column1", "column2"],
)
