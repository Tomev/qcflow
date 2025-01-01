Register a Model
=================

Throughout this tutorial we will leverage a local tracking server and model registry for simplicity.
However, for production use cases we recommend using a 
`remote tracking server <https://qcflow.org/docs/latest/tracking/tutorials/remote-server.html>`_.

Step 0: Install Dependencies
----------------------------
.. code-section::
    .. code-block:: bash

        pip install --upgrade qcflow

Step 1: Register a Model
--------------------------------

To use the QCFlow model registry, you need to add your QCFlow models to it. This is done through 
registering a given model via one of the below commands:

* ``qcflow.<model_flavor>.log_model(registered_model_name=<model_name>)``: register the model 
  **while** logging it to the tracking server.
* ``qcflow.register_model(<model_uri>, <model_name>)``: register the model **after** logging it to
  the tracking server. Note that you'll have to log the model before running this command to get a
  model URI.

QCFlow has lots of model flavors. In the below example, we'll leverage scikit-learn's 
RandomForestRegressor to demonstrate the simplest way to register a model, but note that you
can leverage any `supported model flavor <https://qcflow.org/docs/latest/models.html#built-in-model-flavors>`_.
In the code snippet below, we start an qcflow run and train a random forest model. We then log some 
relevant hyper-parameters, the model mean-squared-error (MSE), and finally log and register the 
model itself.

.. code-section::
    .. code-block:: python 
        :name: create-model 

        from sklearn.datasets import make_regression
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_squared_error
        from sklearn.model_selection import train_test_split

        import qcflow
        import qcflow.sklearn

        with qcflow.start_run() as run:
            X, y = make_regression(n_features=4, n_informative=2, random_state=0, shuffle=False)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            params = {"max_depth": 2, "random_state": 42}
            model = RandomForestRegressor(**params)
            model.fit(X_train, y_train)

            # Log parameters and metrics using the QCFlow APIs
            qcflow.log_params(params)
            
            y_pred = model.predict(X_test)
            qcflow.log_metrics({"mse": mean_squared_error(y_test, y_pred)})

            # Log the sklearn model and register as version 1
            qcflow.sklearn.log_model(
                sk_model=model,
                artifact_path="sklearn-model",
                input_example=X_train, 
                registered_model_name="sk-learn-random-forest-reg-model", 
            )


.. code-block:: bash
    :caption: Example Output

    Successfully registered model 'sk-learn-random-forest-reg-model'.
    Created version '1' of model 'sk-learn-random-forest-reg-model'.

Great! We've registered a model. 

Before moving on, let's highlight some important implementation notes. 

* To register a model, you can leverage the ``registered_model_name`` parameter in the 
  :py:func:`qcflow.sklearn.log_model()` or call :py:func:`qcflow.register_model()` after logging the
  model. Generally, we suggest the former because it's more concise. 
* `Model Signatures <https://qcflow.org/docs/latest/model/signatures.html#qcflow-model-signatures-and-input-examples-guide>`_ 
  provide validation for our model inputs and outputs. The ``input_example`` in ``log_model()``
  automatically infers and logs a signature. Again, we suggest using this implementation because 
  it's concise.
