from qcflow.models import set_model
from qcflow.pyfunc import PythonModel


class MyModel(PythonModel):
    def predict(self, context, model_input):
        return f"This was the input: {model_input}"


set_model(MyModel())
