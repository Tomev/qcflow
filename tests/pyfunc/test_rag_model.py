import json
from dataclasses import asdict

import qcflow
from qcflow.models.model import Model
from qcflow.models.rag_signatures import (
    ChainCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
)
from qcflow.models.signature import ModelSignature

from tests.helper_functions import expect_status_code, pyfunc_serve_and_score_model


class TestRagModel(qcflow.pyfunc.PythonModel):
    def predict(self, context, model_input: ChatCompletionRequest):
        message = model_input.messages[0].content
        # return the message back
        return asdict(
            ChatCompletionResponse(
                choices=[ChainCompletionChoice(message=Message(role="assistant", content=message))]
                # NB: intentionally validating the default population of the object field
            )
        )


def test_rag_model_works_with_type_hint(tmp_path):
    model = TestRagModel()
    signature = ModelSignature(inputs=ChatCompletionRequest(), outputs=ChatCompletionResponse())
    input_example = {"messages": [{"role": "user", "content": "What is qcflow?"}]}
    qcflow.pyfunc.save_model(
        python_model=model, path=tmp_path, signature=signature, input_example=input_example
    )

    # test that the model can be loaded and invoked
    loaded_model = qcflow.pyfunc.load_model(tmp_path)

    response = loaded_model.predict(input_example)
    assert response["choices"][0]["message"]["content"] == "What is qcflow?"
    assert response["object"] == "chat.completion"

    # confirm the input example is set
    qcflow_model = Model.load(tmp_path)
    assert qcflow_model.load_input_example(tmp_path) == input_example

    # test that the model can be served
    response = pyfunc_serve_and_score_model(
        model_uri=tmp_path,
        data=json.dumps(input_example),
        content_type="application/json",
        extra_args=["--env-manager", "local"],
    )

    expect_status_code(response, 200)
    json_response = json.loads(response.content)
    assert json_response["choices"][0]["message"]["content"] == "What is qcflow?"
    assert json_response["object"] == "chat.completion"
