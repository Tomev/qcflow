:orphan:

.. _quickstart_drilldown:

Quickstart options and troubleshooting
============================================================

..
    Eventually, these H2s will probably all be separate articles. For now, I'm 
    avoiding that so as not to create a bunch of super-skinny pages. 

.. _quickstart_drilldown_install:

Customize and troubleshoot QCFlow installation
---------------------------------------------------

Python library options
**********************

Rather than the default QCFlow library, you can install the following variations:

.. list-table::
   :widths: 10 20 70
   :header-rows: 1

   * - Name
     - ``pip install`` command
     - Description
   * - qcflow-skinny
     - ``pip install qcflow-skinny``
     - Lightweight QCFlow package without SQL storage, server, UI, or data science dependencies.
   * - qcflow[extras]
     - ``pip install qcflow[extras]``
     - QCFlow package with all dependencies needed to run various QCFlow flavors. These dependencies are listed in `this document <https://github.com/qcflow/qcflow/blob/master/requirements/extra-ml-requirements.txt>`__.
   * - In-development version
     - ``pip install git+https://github.com/qcflow/qcflow.git@master``
     - This is the latest version of QCFlow, which may be useful for getting hot-fixes or new features.


Python and Mac OS X
**********************

We strongly recommend using a virtual environment manager on Macs. We always recommend using virtual environments, but they are especially important on Mac OS X because the system ``python`` version varies depending on the installation and whether you've installed the Xcode command line tools. The default environment manager for QCFlow is ``virtualenv``. Other popular options are ``conda`` and ``venv``.


Python
******

We release QCFlow on:

- PyPI (``pip install qcflow``)
- conda-forge (``conda install -c conda-forge qcflow``)


R and Java
**********

We release QCFlow on:

- CRAN (``install.packages("qcflow")``)
- Maven Central (``qcflow-client``, ``qcflow-parent``, ``qcflow-scoring``, ``qcflow-spark``)

For R, see :ref:`installing QCFlow for R<R-api>` . For Java, see :ref:`java_api`.

.. _quickstart_drilldown_log_and_load_model:

Save and serve models
-------------------------

QCFlow includes a generic ``MLmodel`` format for saving **models** from a variety of tools in diverse
**flavors**. For example, many models can be served as Python functions, so an ``MLmodel`` file can
declare how each model should be interpreted as a Python function in order to let various tools
serve it. QCFlow also includes tools for running such models locally and exporting them to Docker
containers or commercial serving platforms.

To illustrate this functionality, the ``qcflow.sklearn`` flavor can log scikit-learn models as
QCFlow artifacts and then load them again for serving. There is an example training application in
`sklearn_logistic_regression/train.py <https://github.com/qcflow/qcflow/tree/master/examples/sklearn_logistic_regression>`__. To run it, switch to the QCFlow repository root and run:

.. code-block:: bash

    python examples/sklearn_logistic_regression/train.py

When you run the example, it outputs an QCFlow run ID for that experiment. If you look at the 
``qcflow ui``, you will also see that the run saved a **model** folder containing an ``MLmodel``
description file and a pickled scikit-learn model. You can pass the run ID and the path of the model
within the artifacts directory (here **model/**) to various tools. For example, QCFlow includes a
simple REST server for python-based models:

.. code-block:: bash

    qcflow models serve -m --env-manager local runs:/<RUN_ID>/model

.. note::

    By default the server runs on port 5000. If that port is already in use, use the `--port` option to
    specify a different port. For example: ``qcflow models serve -m runs:/<RUN_ID>/model --port 1234``

Once you have started the server, you can pass it some sample data and see the
predictions.

The following example uses ``curl`` to send a JSON-serialized pandas DataFrame with the ``split``
orientation to the model server. For more information about the input data formats accepted by
the pyfunc model server, see the :ref:`QCFlow deployment tools documentation <local_model_deployment>`.

.. code-block:: bash

    curl -d '{"dataframe_split": {"columns": ["x"], "data": [[1], [-1]]}}' -H 'Content-Type: application/json' -X POST localhost:5000/invocations

which returns::

    [1, 0]

For more information, see :doc:`models`.
