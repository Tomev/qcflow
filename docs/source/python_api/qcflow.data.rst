qcflow.data
============

The ``qcflow.data`` module helps you record your model training and evaluation datasets to
runs with QCFlow Tracking, as well as retrieve dataset information from runs. It provides the
following important interfaces:

* :py:class:`Dataset <qcflow.data.dataset.Dataset>`: Represents a dataset used in model training or
  evaluation, including features, targets, predictions, and metadata such as the dataset's name, digest (hash)
  schema, profile, and source. You can log this metadata to a run in QCFlow Tracking using
  the :py:func:`qcflow.log_input()` API. ``qcflow.data`` provides APIs for constructing
  :py:class:`Datasets <qcflow.data.dataset.Dataset>` from a variety of Python data objects, including
  Pandas DataFrames (:py:func:`qcflow.data.from_pandas()`), NumPy arrays
  (:py:func:`qcflow.data.from_numpy()`), Spark DataFrames (:py:func:`qcflow.data.from_spark()`
  / :py:func:`qcflow.data.load_delta()`), and more.

* :py:func:`DatasetSource <qcflow.data.dataset_source.DatasetSource>`: Represents the source of a
  dataset. For example, this may be a directory of files stored in S3, a Delta Table, or a web URL.
  Each :py:class:`Dataset <qcflow.data.dataset.Dataset>` references the source from which it was
  derived. A :py:class:`Dataset <qcflow.data.dataset.Dataset>`'s features and targets may differ
  from the source if transformations and filtering were applied. You can get the
  :py:func:`DatasetSource <qcflow.data.dataset_source.DatasetSource>` of a dataset logged to a
  run in QCFlow Tracking using the :py:func:`qcflow.data.get_source()` API.

The following example demonstrates how to use ``qcflow.data`` to log a training dataset to a run,
retrieve information about the dataset from the run, and load the dataset's source.

.. code-block:: python

    import qcflow.data
    import pandas as pd
    from qcflow.data.pandas_dataset import PandasDataset

    # Construct a Pandas DataFrame using iris flower data from a web URL
    dataset_source_url = "http://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
    df = pd.read_csv(dataset_source_url)
    # Construct an QCFlow PandasDataset from the Pandas DataFrame, and specify the web URL
    # as the source
    dataset: PandasDataset = qcflow.data.from_pandas(df, source=dataset_source_url)

    with qcflow.start_run():
        # Log the dataset to the QCFlow Run. Specify the "training" context to indicate that the
        # dataset is used for model training
        qcflow.log_input(dataset, context="training")

    # Retrieve the run, including dataset information
    run = qcflow.get_run(qcflow.last_active_run().info.run_id)
    dataset_info = run.inputs.dataset_inputs[0].dataset
    print(f"Dataset name: {dataset_info.name}")
    print(f"Dataset digest: {dataset_info.digest}")
    print(f"Dataset profile: {dataset_info.profile}")
    print(f"Dataset schema: {dataset_info.schema}")

    # Load the dataset's source, which downloads the content from the source URL to the local
    # filesystem
    dataset_source = qcflow.data.get_source(dataset_info)
    dataset_source.load()

.. autoclass:: qcflow.data.dataset.Dataset
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: qcflow.data.dataset_source.DatasetSource
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: from_json

    .. method:: from_json(cls, source_json: str) -> DatasetSource

.. autofunction:: qcflow.data.get_source


pandas
~~~~~~

.. autofunction:: qcflow.data.from_pandas

.. autoclass:: qcflow.data.pandas_dataset.PandasDataset()
    :members:
    :undoc-members:
    :exclude-members: to_pyfunc, to_evaluation_dataset


NumPy
~~~~~

.. autofunction:: qcflow.data.from_numpy

.. autoclass:: qcflow.data.numpy_dataset.NumpyDataset()
    :members:
    :undoc-members:
    :exclude-members: to_pyfunc, to_evaluation_dataset


Spark
~~~~~

.. autofunction:: qcflow.data.load_delta

.. autofunction:: qcflow.data.from_spark

.. autoclass:: qcflow.data.spark_dataset.SparkDataset()
    :members:
    :undoc-members:
    :exclude-members: to_pyfunc, to_evaluation_dataset


Hugging Face 
~~~~~~~~~~~~

.. autofunction:: qcflow.data.huggingface_dataset.from_huggingface

.. autoclass:: qcflow.data.huggingface_dataset.HuggingFaceDataset()
    :members:
    :undoc-members:
    :exclude-members: to_pyfunc


TensorFlow 
~~~~~~~~~~~~

.. autofunction:: qcflow.data.tensorflow_dataset.from_tensorflow

.. autoclass:: qcflow.data.tensorflow_dataset.TensorFlowDataset()
    :members:
    :undoc-members:
    :exclude-members: to_pyfunc, 

.. autoclass:: qcflow.data.evaluation_dataset.EvaluationDataset()
    :members:
    :undoc-members:


Dataset Sources 
~~~~~~~~~~~~~~~~

.. autoclass:: qcflow.data.filesystem_dataset_source.FileSystemDatasetSource()
    :members:
    :undoc-members:

.. autoclass:: qcflow.data.http_dataset_source.HTTPDatasetSource()
    :members:
    :undoc-members:
    
.. autoclass:: qcflow.data.huggingface_dataset_source.HuggingFaceDatasetSource()
    :members:
    :undoc-members:
    :exclude-members:

.. autoclass:: qcflow.data.delta_dataset_source.DeltaDatasetSource()
    :members:
    :undoc-members:

.. autoclass:: qcflow.data.spark_dataset_source.SparkDatasetSource()
    :members:
    :undoc-members:
