.. _community-model-flavors:

=======================
Community Model Flavors
=======================

Other useful QCFlow flavors are developed and maintained by the
QCFlow community, enabling you to use QCFlow Models with an
even broader ecosystem of machine learning libraries. For more information,
check out the description of each community-developed flavor below.

.. contents::
  :local:
  :depth: 1

QCFlow VizMod
-------------

The `qcflow-vizmod <https://github.com/JHibbard/qcflow-vizmod/>`_ project allows data scientists
to be more productive with their visualizations. We treat visualizations as models - just like ML
models - thus being able to use the same infrastructure as QCFlow to track, create projects,
register, and deploy visualizations.

Installation:

.. code-block:: bash

    pip install qcflow-vizmod

Example:

.. code-block:: python

    from sklearn.datasets import load_iris
    import altair as alt
    import qcflow_vismod

    df_iris = load_iris(as_frame=True)

    viz_iris = (
        alt.Chart(df_iris)
        .mark_circle(size=60)
        .encode(x="x", y="y", color="z:N")
        .properties(height=375, width=575)
        .interactive()
    )

    qcflow_vismod.log_model(
        model=viz_iris,
        artifact_path="viz",
        style="vegalite",
        input_example=df_iris.head(5),
    )

BigML (``bigqcflow``)
---------------------

The `bigqcflow <https://github.com/bigmlcom/bigqcflow>`_ library implements
the ``bigml`` model flavor. It enables using
`BigML supervised models <https://bigml.readthedocs.io/en/latest/local_resources.html>`_
and offers the ``save_model()``, ``log_model()`` and ``load_model()`` methods.

Installing bigqcflow
^^^^^^^^^^^^^^^^^^^^

BigQCFlow can be installed from PyPI as follows:


.. code-block:: bash

    pip install bigqcflow

BigQCFlow usage
^^^^^^^^^^^^^^^

The ``bigqcflow`` module defines the flavor that implements the
``save_model()`` and ``log_model()`` methods. They can be used
to save BigML models and their related information in QCFlow Model format.

.. code-block:: python

    import json
    import qcflow
    import bigqcflow

    MODEL_FILE = "logistic_regression.json"
    with qcflow.start_run():
        with open(MODEL_FILE) as handler:
            model = json.load(handler)
            bigqcflow.log_model(
                model, artifact_path="model", registered_model_name="my_model"
            )

These methods also add the ``python_function`` flavor to the QCFlow Models
that they produce, allowing the models to be interpreted as generic Python
functions for inference via :py:func:`qcflow.pyfunc.load_model()`.
This loaded PyFunc model can only be scored with DataFrame inputs.

.. code-block:: python

    # saving the model
    save_model(model, path=model_path)
    # retrieving model
    pyfunc_model = pyfunc.load_model(model_path)
    pyfunc_predictions = pyfunc_model.predict(dataframe)

You can also use the ``bigqcflow.load_model()`` method to load QCFlow Models
with the ``bigqcflow`` model flavor as a BigML
`SupervisedModel <https://bigml.readthedocs.io/en/latest/local_resources.html#local-supervised-model>`_.

For more information, see the
`BigQCFlow documentation <https://bigqcflow.readthedocs.io/en/latest/>`_
and `BigML's blog <https://blog.bigml.com/2022/10/25/easily-operating-machine-learning-models/>`_.

Sktime
------

The ``sktime`` custom model flavor enables logging of `sktime <https://github.com/sktime/sktime>`_ models in QCFlow
format via the ``save_model()`` and ``log_model()`` methods. These methods also add the ``python_function`` flavor to the QCFlow Models that they produce, allowing the
model to be interpreted as generic Python functions for inference via :py:func:`qcflow.pyfunc.load_model()`.
This loaded PyFunc model can only be scored with a DataFrame input.
You can also use the ``load_model()`` method to load QCFlow Models with the ``sktime``
model flavor in native sktime formats.

Installing Sktime
^^^^^^^^^^^^^^^^^

Install sktime with qcflow dependency:

.. code-block:: bash

    pip install sktime[qcflow]

Usage example
^^^^^^^^^^^^^

Refer to the `sktime qcflow documentation <https://www.sktime.net/en/latest/api_reference/deployment.html>`_ for details on the interface for utilizing sktime models loaded as a pyfunc type and an `example notebook <https://github.com/sktime/sktime/blob/main/examples/qcflow.ipynb>`_ for extended code usage examples.

.. code-block:: python

    import pandas as pd

    from sktime.datasets import load_airline
    from sktime.forecasting.arima import AutoARIMA
    from sktime.utils import qcflow_sktime

    airline = load_airline()
    model_path = "model"


    auto_arima_model = AutoARIMA(sp=12, d=0, max_p=2, max_q=2, suppress_warnings=True).fit(
        airline, fh=[1, 2, 3]
    )

    qcflow_sktime.save_model(
        sktime_model=auto_arima_model,
        path=model_path,
    )

    loaded_model = qcflow_sktime.load_model(
        model_uri=model_path,
    )
    loaded_pyfunc = qcflow_sktime.pyfunc.load_model(
        model_uri=model_path,
    )

    print(loaded_model.predict())
    print(loaded_pyfunc.predict(pd.DataFrame()))

MLflavors
---------

The `MLflavors <https://github.com/ml-toolkits/mlflavors>`_ package adds QCFlow support for some
popular machine learning frameworks currently not considered for inclusion as QCFlow built-in
flavors. Similar to the built-in flavors, you can use this package to save your model as an QCFlow
artifact, load your model from QCFlow for batch inference, and deploy your model to a serving 
endpoint using QCFlow deployment tools.

The following open-source libraries are currently supported:

    .. list-table::

      * - **Framework**
        - **Tutorials**
        - **Category**
      * - `Orbit <https://github.com/uber/orbit>`_
        - `QCFlow-Orbit <https://mlflavors.readthedocs.io/en/latest/examples.html#orbit>`_
        - Time Series Forecasting
      * - `Sktime <https://github.com/sktime/sktime>`_
        - `QCFlow-Sktime <https://mlflavors.readthedocs.io/en/latest/examples.html#sktime>`_
        - Time Series Forecasting
      * - `StatsForecast <https://github.com/Nixtla/statsforecast>`_
        - `QCFlow-StatsForecast <https://mlflavors.readthedocs.io/en/latest/examples.html#statsforecast>`_
        - Time Series Forecasting
      * - `PyOD <https://github.com/yzhao062/pyod>`_
        - `QCFlow-PyOD <https://mlflavors.readthedocs.io/en/latest/examples.html#pyod>`_
        - Anomaly Detection
      * - `SDV <https://github.com/sdv-dev/SDV>`_
        - `QCFlow-SDV <https://mlflavors.readthedocs.io/en/latest/examples.html#sdv>`_
        - Synthetic Data Generation

The interface design for the supported frameworks is similar to many of the existing built-in
flavors. Particularly, the interface for utilizing the custom model loaded as a ``pyfunc`` flavor
for generating predictions uses a single-row Pandas DataFrame configuration argument to expose the
parameters of the flavor's inference API.

Documentation
^^^^^^^^^^^^^

Usage examples for all flavors and the API reference can be found in the package
`documenation <https://mlflavors.readthedocs.io/en/latest/index.html>`_.


Installation
^^^^^^^^^^^^

Installing from PyPI:

.. code-block:: bash

   $ pip install mlflavors

Quickstart
^^^^^^^^^^

This example trains a `PyOD <https://github.com/yzhao062/pyod>`_ KNN outlier detection
model using a synthetic dataset. A new QCFlow experiment is created to log the evaluation
metrics and the trained model as an artifact and anomaly scores are computed loading the
trained model in native flavor and ``pyfunc`` flavor. Finally, the model is served
for real-time inference using a local endpoint.

Saving the model as an QCFlow artifact
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json

    import qcflow
    import pandas as pd
    from pyod.models.knn import KNN
    from pyod.utils.data import generate_data
    from sklearn.metrics import roc_auc_score

    import mlflavors

    ARTIFACT_PATH = "model"

    with qcflow.start_run() as run:
        contamination = 0.1  # percentage of outliers
        n_train = 200  # number of training points
        n_test = 100  # number of testing points

        X_train, X_test, _, y_test = generate_data(
            n_train=n_train, n_test=n_test, contamination=contamination
        )

        # Train kNN detector
        clf = KNN()
        clf.fit(X_train)

        # Evaluate model
        y_test_scores = clf.decision_function(X_test)

        metrics = {
            "roc": roc_auc_score(y_test, y_test_scores),
        }

        print(f"Metrics: \n{json.dumps(metrics, indent=2)}")

        # Log metrics
        qcflow.log_metrics(metrics)

        # Log model using pickle serialization (default).
        mlflavors.pyod.log_model(
            pyod_model=clf,
            artifact_path=ARTIFACT_PATH,
            serialization_format="pickle",
        )
        model_uri = qcflow.get_artifact_uri(ARTIFACT_PATH)

    # Print the run id wich is used below for serving the model to a local REST API endpoint
    print(f"\nQCFlow run id:\n{run.info.run_id}")

Loading the model from QCFlow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make a prediction loading the model from QCFlow in native format:

.. code-block:: python

    loaded_model = mlflavors.pyod.load_model(model_uri=model_uri)
    print(loaded_model.decision_function(X_test))

Make a prediction loading the model from QCFlow in ``pyfunc`` format:

.. code-block:: python

    loaded_pyfunc = mlflavors.pyod.pyfunc.load_model(model_uri=model_uri)

    # Create configuration DataFrame
    predict_conf = pd.DataFrame(
        [
            {
                "X": X_test,
                "predict_method": "decision_function",
            }
        ]
    )

    print(loaded_pyfunc.predict(predict_conf)[0])

Serving the model using an endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To serve the model using a local REST API endpoint run the command below where you substitute
the run id printed above:

.. code-block:: bash

    qcflow models serve -m runs:/<run_id>/model --env-manager local --host 127.0.0.1

Similarly, you could serve the model using an endpoint in the cloud (e.g. Azure ML, AWS SageMaker,
etc.) using
`QCFlow deployment tools <https://qcflow.org/docs/latest/models.html#built-in-deployment-tools>`_.
Open a new terminal and run the below model scoring script to request a prediction from the served
model:

.. code-block:: python

    import pandas as pd
    import requests
    from pyod.utils.data import generate_data

    contamination = 0.1  # percentage of outliers
    n_train = 200  # number of training points
    n_test = 100  # number of testing points

    _, X_test, _, _ = generate_data(
        n_train=n_train, n_test=n_test, contamination=contamination
    )

    # Define local host and endpoint url
    host = "127.0.0.1"
    url = f"http://{host}:5000/invocations"

    # Convert to list for JSON serialization
    X_test_list = X_test.tolist()

    # Create configuration DataFrame
    predict_conf = pd.DataFrame(
        [
            {
                "X": X_test_list,
                "predict_method": "decision_function",
            }
        ]
    )

    # Create dictionary with pandas DataFrame in the split orientation
    json_data = {"dataframe_split": predict_conf.to_dict(orient="split")}

    # Score model
    response = requests.post(url, json=json_data)
    print(response.json())
