Deployment
==========

.. important::

    This page describes the toolset for deploying your in-house QCFlow Model. For information on the **LLM Deployment Server** (formerly known as AI Gateway), please refer to `QCFlow Deployment Server <../llms/deployments/index.html>`_.

After training your machine learning model and ensuring its performance, the next step is deploying it to a production environment.
This process can be complex, but QCFlow simplifies it by offering an easy toolset for deploying your ML models to various targets, including local environments, cloud services, and Kubernetes clusters.

.. figure:: ../_static/images/deployment/qcflow-deployment-overview.png
    :align: center
    :figwidth: 90%


By using QCFlow deployment toolset, you can enjoy the following benefits:

- **Effortless Deployment**: QCFlow provides a simple interface for deploying models to various targets, eliminating the need to write boilerplate code.
- **Dependency and Environment Management**: QCFlow ensures that the deployment environment mirrors the training environment, capturing all dependencies. This guarantees that models run consistently, regardless of where they're deployed.
- **Packaging Models and Code**: With QCFlow, not just the model, but any supplementary code and configurations are packaged along with the deployment container. This ensures that the model can be executed seamlessly without any missing components.
- **Avoid Vendor Lock-in**: QCFlow provides a standard format for packaging models and unified APIs for deployment. You can easily switch between deployment targets without having to rewrite your code.

Concepts
--------

`QCFlow Model <../models.html>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`QCFlow Model <../models.html>`_ is a standard format that packages a machine learning model with its metadata, such as dependencies and inference schema.
You typically create a model as a result of training execution using the `QCFlow Tracking APIs <../tracking.html>`_, for instance, :py:func:`qcflow.pyfunc.log_model`. 
Alternatively, models can be registered and retrieved via the `QCFlow Model Registry <../model-registry.html>`_.
To use QCFlow deployment, you must first create a model.

Container
~~~~~~~~~
Container plays a critical role for simplifying and standardizing the model deployment process. QCFlow uses Docker containers to package models with their dependencies,
enabling deployment to various destinations without environment compatibility issues. See :ref:`Building a Docker Image for QCFlow Model <build-docker-for-deployment>` for more details on how to deploy your model as a container.
If you're new to Docker, you can start learning at `"What is a Container" <https://www.docker.com/resources/what-container//>`_.

Deployment Target
~~~~~~~~~~~~~~~~~
Deployment target refers to the destination environment for your model. QCFlow supports various targets, including local environments, cloud services (AWS, Azure), Kubernetes clusters, and others.


How it works
------------
An `QCFlow Model <../models.html>`_ already packages your model and its dependencies, hence QCFlow can create either a virtual environment (for local deployment)
or a Docker container image containing everything needed to run your model. Subsequently, QCFlow launches an inference server with REST endpoints using
frameworks like `Flask <https://flask.palletsprojects.com/en/1.1.x/>`_, preparing it for deployment to various destinations to handle inference requests.
Detailed information about the server and endpoints is available in :ref:`Inference Server Specification <local-inference-server-spec>`.

QCFlow provides :ref:`CLI commands <deployment-cli>` and :ref:`Python APIs <deployment-python-api>` to facilitate the deployment process.
The required commands differ based on the deployment target, so please continue reading to the next section for more details about your specific target.


Supported Deployment Targets
----------------------------
QCFlow offers support for a variety of deployment targets. For detailed information and tutorials on each, please follow the respective links below.

.. toctree::
    :maxdepth: 1
    :hidden:

    deploy-model-locally
    deploy-model-to-sagemaker
    deploy-model-to-kubernetes/index

.. raw:: html

    <section>
        <article class="simple-grid">
            <div class="simple-card">
                <a href="deploy-model-locally.html">
                    <div class="header-with-image">
                        Deploying a Model Locally
                    </div>
                    <p>
                       Deploying a model locally as an inference server is straightforward with QCFlow, requiring just a single command <code>qcflow models serve</code>.
                    </p>
                </a>
            </div>
            <div class="simple-card">
                <a href="deploy-model-to-sagemaker.html">
                    <div class="header-with-image">
                        <img src="../_static/images/logos/amazon-sagemaker-logo.png" alt="Amazon SageMaker Logo" />
                    </div>
                    <p>
                        Amazon SageMaker is a fully managed service for scaling ML inference containers.
                        QCFlow simplifies the deployment process with easy-to-use commands, eliminating the need to write container definitions.
                    </p>
                </a>
            </div>
            <div class="simple-card">
                <a href="https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-qcflow-models">
                    <div class="header-with-image">
                        <img src="../_static/images/logos/azure-ml-logo.png" alt="AzureML Logo" style="width: 90%"/>
                    </div>
                    <p>
                        QCFlow integrates seamlessly with Azure ML. You can deploy QCFlow Model to the Azure ML managed online/batch endpoints,
                        or to Azure Container Instances (ACI) / Azure Kubernetes Service (AKS).
                    </p>
                </a>
            </div>
            <div class="simple-card">
                <a href="https://docs.databricks.com/en/qcflow/models.html">
                    <div class="header-with-image">
                        <img src="../_static/images/logos/databricks-logo.png" alt="Databricks Logo" style="width: 90%"/>
                    </div>
                    <p>
                        Databricks Model Serving offers a fully managed service for serving QCFlow models at scale,
                        with added benefits of performance optimizations and monitoring capabilities.
                    </p>
                </a>
            </div>
            <div class="simple-card">
                <a href="deploy-model-to-kubernetes/index.html">
                    <div class="header-with-image">
                        <img src="../_static/images/logos/kubernetes-logo.png" alt="Kubernetes Logo" style="width: 90%"/>
                    </div>
                    <p>
                       QCFlow Deployment integrates with Kubernetes-native ML serving frameworks
                       such as Seldon Core and KServe (formerly KFServing).
                     </p>
                </a>
            </div>
            <div class="simple-card">
                <a href="../plugins.html#deployment-plugins">
                    <div class="header-with-image">
                        Community Supported Targets
                    </div>
                    <p>
                        QCFlow also supports more deployment targets such as Ray Serve, Redis AI, Torch Serve, Oracle Cloud Infrastructure (OCI), through community-supported plugins.
                    </p>
                </a>
            </div>
        </article>
    </section>


API References
--------------

.. _deployment-cli:

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

Deployment-related commands are primarily categorized under two modules:

* `qcflow models <../cli.html#qcflow-models>`_ - typically used for local deployment.
* `qcflow deployments <../cli.html#qcflow-deployments>`_ - typically used for deploying to custom targets.

Note that these categories are not strictly separated and may overlap. Furthermore, certain targets require
custom modules or plugins, for example, `qcflow sagemaker <../cli.html#qcflow-sagemaker>`_ is used for Amazon
SageMaker deployments, and the `azureml-qcflow <https://pypi.org/project/azureml-qcflow/>`_ library is required for Azure ML.

Therefore, it is advisable to consult the specific documentation for your chosen target to identify the appropriate commands.

.. _deployment-python-api:

Python APIs
~~~~~~~~~~~

Almost all functionalities available in QCFlow deployment can also be accessed via Python APIs. For more details, refer to the following API references:

* `qcflow.models <../python_api/qcflow.models.html>`_
* `qcflow.deployments <../python_api/qcflow.deployments.html>`_
* `qcflow.sagemaker <../python_api/qcflow.sagemaker.html>`_


FAQ
---
If you encounter any dependency issues during model deployment, please refer to :ref:`Model Dependencies FAQ <model-dependencies-troubleshooting>`
for guidance on how to troubleshoot and validate fixes.
