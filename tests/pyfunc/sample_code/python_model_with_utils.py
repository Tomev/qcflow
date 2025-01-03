from qcflow.models import set_model
from qcflow.pyfunc import PythonModel


class MyModel(PythonModel):
    def predict(self, context, model_input):
        from utils import my_function

        return my_function(model_input)


set_model(MyModel())
