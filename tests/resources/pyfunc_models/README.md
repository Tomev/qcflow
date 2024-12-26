# Historical Pyfunc Models

These serialized model files are used in backwards compatibility tests, so we can ensure that models logged with old versions of QCFlow are still able to be loaded in newer versions.

These files were created by running the following:

1. First, install the desired QCFlow version with `$ pip install qcflow=={version_number}`
2. Next, run the following script from QCFlow root:

```python
import qcflow


class MyModel(qcflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        return model_input


model = MyModel()

qcflow.pyfunc.save_model(
    python_model=model,
    path=f"tests/resources/pyfunc_models/{qcflow.__version__}",
)
```
