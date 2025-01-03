QCFlow PyTorch Flavor
======================


Introduction
------------

``PyTorch`` is an open-source machine learning library developed by Facebook's AI Research lab. It provides a flexible
and intuitive framework for deep learning and is particularly favored for its dynamic computation graph (eager mode),
which provides a more pythonic development flow compared to static graph frameworks (graph mode). PyTorch is
efficient for large-scale data processing and neural network training. Due to its ease of use and robust
community support, PyTorch has become a popular choice among researchers and developers in the AI field.

QCFlow has built-in support (we call it QCFlow PyTorch flavor) for PyTorch workflow, at a high level
in QCFlow we provide a set of APIs for:

- **Simplified Experiment Tracking**: Log parameters, metrics, and models during model training.
- **Experiments Management**: Store your PyTorch experiments in QCFlow server, and you can view and share them from QCFlow UI.
- **Effortless Deployment**: Deploy PyTorch models with simple API calls, catering to a variety of production environments.

5 Minute Quick Start with the QCFlow PyTorch Flavor
----------------------------------------------------

.. raw:: html

     <section>
        <article class="simple-grid">
            <div class="simple-card">
                <a href="quickstart/pytorch_quickstart.html">
                    <div class="header">
                        Quickstart with QCFlow PyTorch Flavor
                    </div>
                    <p>
                        Learn how to leverage QCFlow for tracking PyTorch experiments and models.
                    </p>
                </a>
            </div>
        </article>
    </section>

.. toctree::
    :maxdepth: 1
    :hidden:

    quickstart/pytorch_quickstart.ipynb


`Developer Guide of PyTorch with QCFlow <guide/index.html>`_
-------------------------------------------------------------

To learn more about the nuances of the ``pytorch`` flavor in QCFlow, please read the developer guide. It will walk you
through the following topics:

.. raw:: html

    <a href="guide/index.html" class="download-btn">View the Developer Guide</a>

- **Logging PyTorch Experiments with QCFlow**: How to log PyTorch experiments to QCFlow, including training metrics,
  model parameters, and training hyperparamers.
- **Log Your PyTorch Models with QCFlow**: How to log your PyTorch models with QCFlow and how to load them back
  for inference.


.. toctree::
    :maxdepth: 2
    :hidden:

    guide/index.rst
