QCFlow Tensorflow Integration
==============================

Introduction
------------

TensorFlow is an end-to-end open source platform for machine learning. It has a comprehensive, flexible
ecosystem of tools, libraries, and community resources that lets researchers push the state-of-the-art
in ML and developers easily build and deploy ML-powered applications.

QCFlow has built-in support (we call it QCFlow Tensorflow flavor) for Tensorflow workflow, at a high level
in QCFlow we provide a set of APIs for:

- **Simplified Experiment Tracking**: Log parameters, metrics, and models during model training.
- **Experiments Management**: Store your Tensorflow experiments in QCFlow server, and you can view and share them from QCFlow UI.
- **Effortless Deployment**: Deploy Tensorflow models with simple API calls, catering to a variety of production environments.

5 Minute Quick Start with the QCFlow Tensorflow Flavor
-------------------------------------------------------

.. raw:: html

     <section>
        <article class="simple-grid">
            <div class="simple-card">
                <a href="quickstart/quickstart_tensorflow.html">
                    <div class="header">
                        Quickstart with QCFlow Tensorflow Flavor
                    </div>
                    <p>
                        Learn how to leverage QCFlow for tracking Tensorflow experiments and models.
                    </p>
                </a>
            </div>
        </article>
    </section>


.. toctree::
    :maxdepth: 1
    :hidden:

    quickstart/quickstart_tensorflow.ipynb

`Developer Guide of Tensorflow with QCFlow <guide/index.html>`_
----------------------------------------------------------------

To learn more about the nuances of the `tensorflow` flavor in QCFlow, please read the developer guide. It will walk you
through the following topics:

.. raw:: html

    <a href="guide/index.html" class="download-btn">View the Developer Guide</a>

- **Autologging Tensorflow Experiments with QCFlow**: How to left QCFlow autolog Tensorflow experiments, and what
  metrics are logged.
- **Control QCFlow Logging with Keras Callback**: For people who don't like autologging, we offer an option to log
  experiments to QCFlow using a custom Keras callback.
- **Log Your Tensorflow Models with QCFlow**: How to log your Tensorflow models with QCFlow and how to load them back
  for inference.


.. toctree::
    :maxdepth: 2
    :hidden:

    guide/index.rst
