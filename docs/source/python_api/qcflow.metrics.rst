qcflow.metrics
==============

The ``qcflow.metrics`` module helps you quantitatively and qualitatively measure your models. 

.. autoclass:: qcflow.metrics.EvaluationMetric

These :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>` are used by the :py:func:`qcflow.evaluate()` API, either computed automatically depending on the ``model_type`` or specified via the ``extra_metrics`` parameter.

The following code demonstrates how to use :py:func:`qcflow.evaluate()` with an  :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>`.

.. code-block:: python

    import qcflow
    from qcflow.metrics.genai import EvaluationExample, answer_similarity

    eval_df = pd.DataFrame(
        {
            "inputs": [
                "What is QCFlow?",
            ],
            "ground_truth": [
                "QCFlow is an open-source platform for managing the end-to-end machine learning lifecycle. It was developed by Databricks, a company that specializes in big data and machine learning solutions. QCFlow is designed to address the challenges that data scientists and machine learning engineers face when developing, training, and deploying machine learning models.",
            ],
        }
    )

    example = EvaluationExample(
        input="What is QCFlow?",
        output="QCFlow is an open-source platform for managing machine "
        "learning workflows, including experiment tracking, model packaging, "
        "versioning, and deployment, simplifying the ML lifecycle.",
        score=4,
        justification="The definition effectively explains what QCFlow is "
        "its purpose, and its developer. It could be more concise for a 5-score.",
        grading_context={
            "ground_truth": "QCFlow is an open-source platform for managing "
            "the end-to-end machine learning (ML) lifecycle. It was developed by Databricks, "
            "a company that specializes in big data and machine learning solutions. QCFlow is "
            "designed to address the challenges that data scientists and machine learning "
            "engineers face when developing, training, and deploying machine learning models."
        },
    )
    answer_similarity_metric = answer_similarity(examples=[example])
    results = qcflow.evaluate(
        logged_model.model_uri,
        eval_df,
        targets="ground_truth",
        model_type="question-answering",
        extra_metrics=[answer_similarity_metric],
    )

Information about how an :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>` is calculated, such as the grading prompt used is available via the ``metric_details`` property.

.. code-block:: python

    import qcflow
    from qcflow.metrics.genai import relevance

    my_relevance_metric = relevance()
    print(my_relevance_metric.metric_details)

Evaluation results are stored as :py:class:`MetricValue <qcflow.metrics.MetricValue>`. Aggregate results are logged to the QCFlow run as metrics, while per-example results are logged to the QCFlow run as artifacts in the form of an evaluation table.

.. autoclass:: qcflow.metrics.MetricValue

We provide the following builtin factory functions to create :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>` for evaluating models. These metrics are computed automatically depending on the ``model_type``. For more information on the ``model_type`` parameter, see :py:func:`qcflow.evaluate()` API.

Regressor Metrics
-----------------

.. autofunction:: qcflow.metrics.mae

.. autofunction:: qcflow.metrics.mape

.. autofunction:: qcflow.metrics.max_error

.. autofunction:: qcflow.metrics.mse

.. autofunction:: qcflow.metrics.rmse

.. autofunction:: qcflow.metrics.r2_score

Classifier Metrics
------------------

.. autofunction:: qcflow.metrics.precision_score

.. autofunction:: qcflow.metrics.recall_score

.. autofunction:: qcflow.metrics.f1_score

Text Metrics
------------

.. autofunction:: qcflow.metrics.ari_grade_level

.. autofunction:: qcflow.metrics.flesch_kincaid_grade_level

Question Answering Metrics
---------------------------

Includes all of the above **Text Metrics** as well as the following:

.. autofunction:: qcflow.metrics.exact_match

.. autofunction:: qcflow.metrics.rouge1

.. autofunction:: qcflow.metrics.rouge2

.. autofunction:: qcflow.metrics.rougeL

.. autofunction:: qcflow.metrics.rougeLsum

.. autofunction:: qcflow.metrics.toxicity

.. autofunction:: qcflow.metrics.token_count

.. autofunction:: qcflow.metrics.latency

.. autofunction:: qcflow.metrics.bleu

Retriever Metrics
-----------------

The following metrics are built-in metrics for the ``'retriever'`` model type, meaning they will be 
automatically calculated with a default ``retriever_k`` value of 3. 

To evaluate document retrieval models, it is recommended to use a dataset with the following 
columns:

- Input queries
- Retrieved relevant doc IDs
- Ground-truth doc IDs

Alternatively, you can also provide a function through the ``model`` parameter to represent 
your retrieval model. The function should take a Pandas DataFrame containing input queries and 
ground-truth relevant doc IDs, and return a DataFrame with a column of retrieved relevant doc IDs.

A "doc ID" is a string or integer that uniquely identifies a document. Each row of the retrieved and
ground-truth doc ID columns should consist of a list or numpy array of doc IDs.

Parameters:

- ``targets``: A string specifying the column name of the ground-truth relevant doc IDs
- ``predictions``: A string specifying the column name of the retrieved relevant doc IDs in either 
  the static dataset or the Dataframe returned by the ``model`` function
- ``retriever_k``: A positive integer specifying the number of retrieved docs IDs to consider for 
  each input query. ``retriever_k`` defaults to 3. You can change ``retriever_k`` by using the 
  :py:func:`qcflow.evaluate` API:

    1. .. code-block:: python

        # with a model and using `evaluator_config`
        qcflow.evaluate(
            model=retriever_function,
            data=data,
            targets="ground_truth",
            model_type="retriever",
            evaluators="default",
            evaluator_config={"retriever_k": 5}
        )
    2. .. code-block:: python

        # with a static dataset and using `extra_metrics`
        qcflow.evaluate(
            data=data,
            predictions="predictions_param",
            targets="targets_param",
            model_type="retriever",
            extra_metrics = [
                qcflow.metrics.precision_at_k(5),
                qcflow.metrics.precision_at_k(6),
                qcflow.metrics.recall_at_k(5),
                qcflow.metrics.ndcg_at_k(5)
            ]   
        )
    
    NOTE: In the 2nd method, it is recommended to omit the ``model_type`` as well, or else 
    ``precision@3`` and ``recall@3`` will be  calculated in  addition to ``precision@5``, 
    ``precision@6``, ``recall@5``, and ``ndcg_at_k@5``.

.. autofunction:: qcflow.metrics.precision_at_k

.. autofunction:: qcflow.metrics.recall_at_k

.. autofunction:: qcflow.metrics.ndcg_at_k

Users create their own :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>` using the :py:func:`make_metric <qcflow.metrics.make_metric>` factory function

.. autofunction:: qcflow.metrics.make_metric

.. automodule:: qcflow.metrics
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: MetricValue, EvaluationMetric, make_metric, EvaluationExample, ari_grade_level, flesch_kincaid_grade_level, exact_match, rouge1, rouge2, rougeL, rougeLsum, toxicity, answer_similarity, answer_correctness, faithfulness, answer_relevance, mae, mape, max_error, mse, rmse, r2_score, precision_score, recall_score, f1_score, token_count, latency, precision_at_k, recall_at_k, ndcg_at_k, bleu

Generative AI Metrics
---------------------

We also provide generative AI ("genai") :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>`\s for evaluating text models. These metrics use an LLM to evaluate the quality of a model's output text. Note that your use of a third party LLM service (e.g., OpenAI) for evaluation may be subject to and governed by the LLM service's terms of use. The following factory functions help you customize the intelligent metric to your use case.

.. automodule:: qcflow.metrics.genai
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: EvaluationExample, make_genai_metric

You can also create your own generative AI :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>`\s using the :py:func:`make_genai_metric <qcflow.metrics.genai.make_genai_metric>` factory function.

.. autofunction:: qcflow.metrics.genai.make_genai_metric

When using generative AI :py:class:`EvaluationMetric <qcflow.metrics.EvaluationMetric>`\s, it is important to pass in an :py:class:`EvaluationExample <qcflow.metrics.genai.EvaluationExample>`

.. autoclass:: qcflow.metrics.genai.EvaluationExample

Users must set the appropriate environment variables for the LLM service they are using for 
evaluation. For example, if you are using OpenAI's API, you must set the ``OPENAI_API_KEY`` 
environment variable. If using Azure OpenAI, you must also set the ``OPENAI_API_TYPE``, 
``OPENAI_API_VERSION``, ``OPENAI_API_BASE``, and ``OPENAI_DEPLOYMENT_NAME`` environment variables. 
See `Azure OpenAI documentation <https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints>`_
Users do not need to set these environment variables if they are using a gateway route.
