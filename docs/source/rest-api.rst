
.. _rest-api:

========
REST API
========


The QCFlow REST API allows you to create, list, and get experiments and runs, and log parameters, metrics, and artifacts.
The API is hosted under the ``/api`` route on the QCFlow tracking server. For example, to search for
experiments on a tracking server hosted at ``http://localhost:5000``, make a POST request to
``http://localhost:5000/api/2.0/qcflow/experiments/search``.

.. important::
    The QCFlow REST API requires content type ``application/json`` for all POST requests.

.. contents:: Table of Contents
    :local:
    :depth: 1

===========================


.. _qcflowMlflowServicecreateExperiment:

Create Experiment
=================


+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/experiments/create`` | ``POST``    |
+-----------------------------------+-------------+

Create an experiment with a name. Returns the ID of the newly created experiment.
Validates that another experiment with the same name does not already exist and fails
if another experiment with the same name already exists.


Throws ``RESOURCE_ALREADY_EXISTS`` if a experiment with the given name exists.




.. _qcflowCreateExperiment:

Request Structure
-----------------






+-------------------+----------------------------------------+------------------------------------------------------------------------------------------------+
|    Field Name     |                  Type                  |                                          Description                                           |
+===================+========================================+================================================================================================+
| name              | ``STRING``                             | Experiment name.                                                                               |
|                   |                                        | This field is required.                                                                        |
|                   |                                        |                                                                                                |
+-------------------+----------------------------------------+------------------------------------------------------------------------------------------------+
| artifact_location | ``STRING``                             | Location where all artifacts for the experiment are stored.                                    |
|                   |                                        | If not provided, the remote server will select an appropriate default.                         |
+-------------------+----------------------------------------+------------------------------------------------------------------------------------------------+
| tags              | An array of :ref:`qcflowexperimenttag` | A collection of tags to set on the experiment. Maximum tag size and number of tags per request |
|                   |                                        | depends on the storage backend. All storage backends are guaranteed to support tag keys up     |
|                   |                                        | to 250 bytes in size and tag values up to 5000 bytes in size. All storage backends are also    |
|                   |                                        | guaranteed to support up to 20 tags per request.                                               |
+-------------------+----------------------------------------+------------------------------------------------------------------------------------------------+

.. _qcflowCreateExperimentResponse:

Response Structure
------------------






+---------------+------------+---------------------------------------+
|  Field Name   |    Type    |              Description              |
+===============+============+=======================================+
| experiment_id | ``STRING`` | Unique identifier for the experiment. |
+---------------+------------+---------------------------------------+

===========================



.. _qcflowMlflowServicesearchExperiments:

Search Experiments
==================


+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/experiments/search`` | ``POST``    |
+-----------------------------------+-------------+






.. _qcflowSearchExperiments:

Request Structure
-----------------






+-------------+------------------------+--------------------------------------------------------------------------------------------+
| Field Name  |          Type          |                                        Description                                         |
+=============+========================+============================================================================================+
| max_results | ``INT64``              | Maximum number of experiments desired.                                                     |
|             |                        | Servers may select a desired default `max_results` value. All servers are                  |
|             |                        | guaranteed to support a `max_results` threshold of at least 1,000 but may                  |
|             |                        | support more. Callers of this endpoint are encouraged to pass max_results                  |
|             |                        | explicitly and leverage page_token to iterate through experiments.                         |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| page_token  | ``STRING``             | Token indicating the page of experiments to fetch                                          |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| filter      | ``STRING``             | A filter expression over experiment attributes and tags that allows returning a subset of  |
|             |                        | experiments. The syntax is a subset of SQL that supports ANDing together binary operations |
|             |                        | between an attribute or tag, and a constant.                                               |
|             |                        |                                                                                            |
|             |                        | Example: ``name LIKE 'test-%' AND tags.key = 'value'``                                     |
|             |                        |                                                                                            |
|             |                        | You can select columns with special characters (hyphen, space, period, etc.) by using      |
|             |                        | double quotes or backticks.                                                                |
|             |                        |                                                                                            |
|             |                        | Example: ``tags."extra-key" = 'value'`` or ``tags.`extra-key` = 'value'``                  |
|             |                        |                                                                                            |
|             |                        | Supported operators are ``=``, ``!=``, ``LIKE``, and ``ILIKE``.                            |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| order_by    | An array of ``STRING`` | List of columns for ordering search results, which can include experiment name and id      |
|             |                        | with an optional "DESC" or "ASC" annotation, where "ASC" is the default.                   |
|             |                        | Tiebreaks are done by experiment id DESC.                                                  |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| view_type   | :ref:`qcflowviewtype`  | Qualifier for type of experiments to be returned.                                          |
|             |                        | If unspecified, return only active experiments.                                            |
+-------------+------------------------+--------------------------------------------------------------------------------------------+

.. _qcflowSearchExperimentsResponse:

Response Structure
------------------






+-----------------+-------------------------------------+----------------------------------------------------------------------------+
|   Field Name    |                Type                 |                                Description                                 |
+=================+=====================================+============================================================================+
| experiments     | An array of :ref:`qcflowexperiment` | Experiments that match the search criteria                                 |
+-----------------+-------------------------------------+----------------------------------------------------------------------------+
| next_page_token | ``STRING``                          | Token that can be used to retrieve the next page of experiments.           |
|                 |                                     | An empty token means that no more experiments are available for retrieval. |
+-----------------+-------------------------------------+----------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicegetExperiment:

Get Experiment
==============


+--------------------------------+-------------+
|            Endpoint            | HTTP Method |
+================================+=============+
| ``2.0/qcflow/experiments/get`` | ``GET``     |
+--------------------------------+-------------+

Get metadata for an experiment. This method works on deleted experiments.




.. _qcflowGetExperiment:

Request Structure
-----------------






+---------------+------------+----------------------------------+
|  Field Name   |    Type    |           Description            |
+===============+============+==================================+
| experiment_id | ``STRING`` | ID of the associated experiment. |
|               |            | This field is required.          |
|               |            |                                  |
+---------------+------------+----------------------------------+

.. _qcflowGetExperimentResponse:

Response Structure
------------------






+------------+-------------------------+---------------------+
| Field Name |          Type           |     Description     |
+============+=========================+=====================+
| experiment | :ref:`qcflowexperiment` | Experiment details. |
+------------+-------------------------+---------------------+

===========================



.. _qcflowMlflowServicegetExperimentByName:

Get Experiment By Name
======================


+----------------------------------------+-------------+
|                Endpoint                | HTTP Method |
+========================================+=============+
| ``2.0/qcflow/experiments/get-by-name`` | ``GET``     |
+----------------------------------------+-------------+

Get metadata for an experiment.

This endpoint will return deleted experiments, but prefers the active experiment
if an active and deleted experiment share the same name. If multiple deleted
experiments share the same name, the API will return one of them.

Throws ``RESOURCE_DOES_NOT_EXIST`` if no experiment with the specified name exists.




.. _qcflowGetExperimentByName:

Request Structure
-----------------






+-----------------+------------+------------------------------------+
|   Field Name    |    Type    |            Description             |
+=================+============+====================================+
| experiment_name | ``STRING`` | Name of the associated experiment. |
|                 |            | This field is required.            |
|                 |            |                                    |
+-----------------+------------+------------------------------------+

.. _qcflowGetExperimentByNameResponse:

Response Structure
------------------






+------------+-------------------------+---------------------+
| Field Name |          Type           |     Description     |
+============+=========================+=====================+
| experiment | :ref:`qcflowexperiment` | Experiment details. |
+------------+-------------------------+---------------------+

===========================



.. _qcflowMlflowServicedeleteExperiment:

Delete Experiment
=================


+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/experiments/delete`` | ``POST``    |
+-----------------------------------+-------------+

Mark an experiment and associated metadata, runs, metrics, params, and tags for deletion.
If the experiment uses FileStore, artifacts associated with experiment are also deleted.




.. _qcflowDeleteExperiment:

Request Structure
-----------------






+---------------+------------+----------------------------------+
|  Field Name   |    Type    |           Description            |
+===============+============+==================================+
| experiment_id | ``STRING`` | ID of the associated experiment. |
|               |            | This field is required.          |
|               |            |                                  |
+---------------+------------+----------------------------------+

===========================



.. _qcflowMlflowServicerestoreExperiment:

Restore Experiment
==================


+------------------------------------+-------------+
|              Endpoint              | HTTP Method |
+====================================+=============+
| ``2.0/qcflow/experiments/restore`` | ``POST``    |
+------------------------------------+-------------+

Restore an experiment marked for deletion. This also restores
associated metadata, runs, metrics, params, and tags. If experiment uses FileStore, underlying
artifacts associated with experiment are also restored.

Throws ``RESOURCE_DOES_NOT_EXIST`` if experiment was never created or was permanently deleted.




.. _qcflowRestoreExperiment:

Request Structure
-----------------






+---------------+------------+----------------------------------+
|  Field Name   |    Type    |           Description            |
+===============+============+==================================+
| experiment_id | ``STRING`` | ID of the associated experiment. |
|               |            | This field is required.          |
|               |            |                                  |
+---------------+------------+----------------------------------+

===========================



.. _qcflowMlflowServiceupdateExperiment:

Update Experiment
=================


+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/experiments/update`` | ``POST``    |
+-----------------------------------+-------------+

Update experiment metadata.




.. _qcflowUpdateExperiment:

Request Structure
-----------------






+---------------+------------+---------------------------------------------------------------------------------------------+
|  Field Name   |    Type    |                                         Description                                         |
+===============+============+=============================================================================================+
| experiment_id | ``STRING`` | ID of the associated experiment.                                                            |
|               |            | This field is required.                                                                     |
|               |            |                                                                                             |
+---------------+------------+---------------------------------------------------------------------------------------------+
| new_name      | ``STRING`` | If provided, the experiment's name is changed to the new name. The new name must be unique. |
+---------------+------------+---------------------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicecreateRun:

Create Run
==========


+----------------------------+-------------+
|          Endpoint          | HTTP Method |
+============================+=============+
| ``2.0/qcflow/runs/create`` | ``POST``    |
+----------------------------+-------------+

Create a new run within an experiment. A run is usually a single execution of a
machine learning or data ETL pipeline. QCFlow uses runs to track :ref:`qcflowParam`,
:ref:`qcflowMetric`, and :ref:`qcflowRunTag` associated with a single execution.




.. _qcflowCreateRun:

Request Structure
-----------------






+---------------+---------------------------------+----------------------------------------------------------------------------+
|  Field Name   |              Type               |                                Description                                 |
+===============+=================================+============================================================================+
| experiment_id | ``STRING``                      | ID of the associated experiment.                                           |
+---------------+---------------------------------+----------------------------------------------------------------------------+
| user_id       | ``STRING``                      | ID of the user executing the run.                                          |
|               |                                 | This field is deprecated as of QCFlow 1.0, and will be removed in a future |
|               |                                 | QCFlow release. Use 'qcflow.user' tag instead.                             |
+---------------+---------------------------------+----------------------------------------------------------------------------+
| run_name      | ``STRING``                      | Name of the run.                                                           |
+---------------+---------------------------------+----------------------------------------------------------------------------+
| start_time    | ``INT64``                       | Unix timestamp in milliseconds of when the run started.                    |
+---------------+---------------------------------+----------------------------------------------------------------------------+
| tags          | An array of :ref:`qcflowruntag` | Additional metadata for run.                                               |
+---------------+---------------------------------+----------------------------------------------------------------------------+

.. _qcflowCreateRunResponse:

Response Structure
------------------






+------------+------------------+------------------------+
| Field Name |       Type       |      Description       |
+============+==================+========================+
| run        | :ref:`qcflowrun` | The newly created run. |
+------------+------------------+------------------------+

===========================



.. _qcflowMlflowServicedeleteRun:

Delete Run
==========


+----------------------------+-------------+
|          Endpoint          | HTTP Method |
+============================+=============+
| ``2.0/qcflow/runs/delete`` | ``POST``    |
+----------------------------+-------------+

Mark a run for deletion.




.. _qcflowDeleteRun:

Request Structure
-----------------






+------------+------------+--------------------------+
| Field Name |    Type    |       Description        |
+============+============+==========================+
| run_id     | ``STRING`` | ID of the run to delete. |
|            |            | This field is required.  |
|            |            |                          |
+------------+------------+--------------------------+

===========================



.. _qcflowMlflowServicerestoreRun:

Restore Run
===========


+-----------------------------+-------------+
|          Endpoint           | HTTP Method |
+=============================+=============+
| ``2.0/qcflow/runs/restore`` | ``POST``    |
+-----------------------------+-------------+

Restore a deleted run.




.. _qcflowRestoreRun:

Request Structure
-----------------






+------------+------------+---------------------------+
| Field Name |    Type    |        Description        |
+============+============+===========================+
| run_id     | ``STRING`` | ID of the run to restore. |
|            |            | This field is required.   |
|            |            |                           |
+------------+------------+---------------------------+

===========================



.. _qcflowMlflowServicegetRun:

Get Run
=======


+-------------------------+-------------+
|        Endpoint         | HTTP Method |
+=========================+=============+
| ``2.0/qcflow/runs/get`` | ``GET``     |
+-------------------------+-------------+

Get metadata, metrics, params, and tags for a run. In the case where multiple metrics
with the same key are logged for a run, return only the value with the latest timestamp.
If there are multiple values with the latest timestamp, return the maximum of these values.




.. _qcflowGetRun:

Request Structure
-----------------






+------------+------------+--------------------------------------------------------------------------+
| Field Name |    Type    |                               Description                                |
+============+============+==========================================================================+
| run_id     | ``STRING`` | ID of the run to fetch. Must be provided.                                |
+------------+------------+--------------------------------------------------------------------------+
| run_uuid   | ``STRING`` | [Deprecated, use run_id instead] ID of the run to fetch. This field will |
|            |            | be removed in a future QCFlow version.                                   |
+------------+------------+--------------------------------------------------------------------------+

.. _qcflowGetRunResponse:

Response Structure
------------------






+------------+------------------+----------------------------------------------------------------------------+
| Field Name |       Type       |                                Description                                 |
+============+==================+============================================================================+
| run        | :ref:`qcflowrun` | Run metadata (name, start time, etc) and data (metrics, params, and tags). |
+------------+------------------+----------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicelogMetric:

Log Metric
==========


+--------------------------------+-------------+
|            Endpoint            | HTTP Method |
+================================+=============+
| ``2.0/qcflow/runs/log-metric`` | ``POST``    |
+--------------------------------+-------------+

Log a metric for a run. A metric is a key-value pair (string key, float value) with an
associated timestamp. Examples include the various metrics that represent ML model accuracy.
A metric can be logged multiple times.




.. _qcflowLogMetric:

Request Structure
-----------------






+------------+------------+-----------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                          Description                                          |
+============+============+===============================================================================================+
| run_id     | ``STRING`` | ID of the run under which to log the metric. Must be provided.                                |
+------------+------------+-----------------------------------------------------------------------------------------------+
| run_uuid   | ``STRING`` | [Deprecated, use run_id instead] ID of the run under which to log the metric. This field will |
|            |            | be removed in a future QCFlow version.                                                        |
+------------+------------+-----------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the metric.                                                                           |
|            |            | This field is required.                                                                       |
|            |            |                                                                                               |
+------------+------------+-----------------------------------------------------------------------------------------------+
| value      | ``DOUBLE`` | Double value of the metric being logged.                                                      |
|            |            | This field is required.                                                                       |
|            |            |                                                                                               |
+------------+------------+-----------------------------------------------------------------------------------------------+
| timestamp  | ``INT64``  | Unix timestamp in milliseconds at the time metric was logged.                                 |
|            |            | This field is required.                                                                       |
|            |            |                                                                                               |
+------------+------------+-----------------------------------------------------------------------------------------------+
| step       | ``INT64``  | Step at which to log the metric                                                               |
+------------+------------+-----------------------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicelogBatch:

Log Batch
=========


+-------------------------------+-------------+
|           Endpoint            | HTTP Method |
+===============================+=============+
| ``2.0/qcflow/runs/log-batch`` | ``POST``    |
+-------------------------------+-------------+

Log a batch of metrics, params, and tags for a run.
If any data failed to be persisted, the server will respond with an error (non-200 status code).
In case of error (due to internal server error or an invalid request), partial data may
be written.

You can write metrics, params, and tags in interleaving fashion, but within a given entity
type are guaranteed to follow the order specified in the request body. That is, for an API
request like

.. code-block:: json

  {
     "run_id": "2a14ed5c6a87499199e0106c3501eab8",
     "metrics": [
       {"key": "mae", "value": 2.5, "timestamp": 1552550804},
       {"key": "rmse", "value": 2.7, "timestamp": 1552550804},
     ],
     "params": [
       {"key": "model_class", "value": "LogisticRegression"},
     ]
  }

the server is guaranteed to write metric "rmse" after "mae", though it may write param
"model_class" before both metrics, after "mae", or after both metrics.

The overwrite behavior for metrics, params, and tags is as follows:

- Metrics: metric values are never overwritten. Logging a metric (key, value, timestamp) appends to the set of values for the metric with the provided key.

- Tags: tag values can be overwritten by successive writes to the same tag key. That is, if multiple tag values with the same key are provided in the same API request, the last-provided tag value is written. Logging the same tag (key, value) is permitted - that is, logging a tag is idempotent.

- Params: once written, param values cannot be changed (attempting to overwrite a param value will result in an error). However, logging the same param (key, value) is permitted - that is, logging a param is idempotent.

Request Limits
--------------
A single JSON-serialized API request may be up to 1 MB in size and contain:

- No more than 1000 metrics, params, and tags in total
- Up to 1000 metrics
- Up to 100 params
- Up to 100 tags

For example, a valid request might contain 900 metrics, 50 params, and 50 tags, but logging
900 metrics, 50 params, and 51 tags is invalid. The following limits also apply
to metric, param, and tag keys and values:

- Metric, param, and tag keys can be up to 250 characters in length
- Param and tag values can be up to 250 characters in length




.. _qcflowLogBatch:

Request Structure
-----------------






+------------+---------------------------------+---------------------------------------------------------------------------------+
| Field Name |              Type               |                                   Description                                   |
+============+=================================+=================================================================================+
| run_id     | ``STRING``                      | ID of the run to log under                                                      |
+------------+---------------------------------+---------------------------------------------------------------------------------+
| metrics    | An array of :ref:`qcflowmetric` | Metrics to log. A single request can contain up to 1000 metrics, and up to 1000 |
|            |                                 | metrics, params, and tags in total.                                             |
+------------+---------------------------------+---------------------------------------------------------------------------------+
| params     | An array of :ref:`qcflowparam`  | Params to log. A single request can contain up to 100 params, and up to 1000    |
|            |                                 | metrics, params, and tags in total.                                             |
+------------+---------------------------------+---------------------------------------------------------------------------------+
| tags       | An array of :ref:`qcflowruntag` | Tags to log. A single request can contain up to 100 tags, and up to 1000        |
|            |                                 | metrics, params, and tags in total.                                             |
+------------+---------------------------------+---------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicelogModel:

Log Model
=========


+-------------------------------+-------------+
|           Endpoint            | HTTP Method |
+===============================+=============+
| ``2.0/qcflow/runs/log-model`` | ``POST``    |
+-------------------------------+-------------+

.. note::
    Experimental: This API may change or be removed in a future release without warning.




.. _qcflowLogModel:

Request Structure
-----------------






+------------+------------+------------------------------+
| Field Name |    Type    |         Description          |
+============+============+==============================+
| run_id     | ``STRING`` | ID of the run to log under   |
+------------+------------+------------------------------+
| model_json | ``STRING`` | MLmodel file in json format. |
+------------+------------+------------------------------+

===========================



.. _qcflowMlflowServicelogInputs:

Log Inputs
==========


+--------------------------------+-------------+
|            Endpoint            | HTTP Method |
+================================+=============+
| ``2.0/qcflow/runs/log-inputs`` | ``POST``    |
+--------------------------------+-------------+

.. note::
    Experimental: This API may change or be removed in a future release without warning.




.. _qcflowLogInputs:

Request Structure
-----------------



.. note::
    Experimental: This API may change or be removed in a future release without warning.


+------------+---------------------------------------+----------------------------+
| Field Name |                 Type                  |        Description         |
+============+=======================================+============================+
| run_id     | ``STRING``                            | ID of the run to log under |
|            |                                       | This field is required.    |
|            |                                       |                            |
+------------+---------------------------------------+----------------------------+
| datasets   | An array of :ref:`qcflowdatasetinput` | Dataset inputs             |
+------------+---------------------------------------+----------------------------+

===========================



.. _qcflowMlflowServicesetExperimentTag:

Set Experiment Tag
==================


+-----------------------------------------------+-------------+
|                   Endpoint                    | HTTP Method |
+===============================================+=============+
| ``2.0/qcflow/experiments/set-experiment-tag`` | ``POST``    |
+-----------------------------------------------+-------------+

Set a tag on an experiment. Experiment tags are metadata that can be updated.




.. _qcflowSetExperimentTag:

Request Structure
-----------------






+---------------+------------+-------------------------------------------------------------------------------------+
|  Field Name   |    Type    |                                     Description                                     |
+===============+============+=====================================================================================+
| experiment_id | ``STRING`` | ID of the experiment under which to log the tag. Must be provided.                  |
|               |            | This field is required.                                                             |
|               |            |                                                                                     |
+---------------+------------+-------------------------------------------------------------------------------------+
| key           | ``STRING`` | Name of the tag. Maximum size depends on storage backend.                           |
|               |            | All storage backends are guaranteed to support key values up to 250 bytes in size.  |
|               |            | This field is required.                                                             |
|               |            |                                                                                     |
+---------------+------------+-------------------------------------------------------------------------------------+
| value         | ``STRING`` | String value of the tag being logged. Maximum size depends on storage backend.      |
|               |            | All storage backends are guaranteed to support key values up to 5000 bytes in size. |
|               |            | This field is required.                                                             |
|               |            |                                                                                     |
+---------------+------------+-------------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicesetTag:

Set Tag
=======


+-----------------------------+-------------+
|          Endpoint           | HTTP Method |
+=============================+=============+
| ``2.0/qcflow/runs/set-tag`` | ``POST``    |
+-----------------------------+-------------+

Set a tag on a run. Tags are run metadata that can be updated during a run and after
a run completes.




.. _qcflowSetTag:

Request Structure
-----------------






+------------+------------+--------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                        Description                                         |
+============+============+============================================================================================+
| run_id     | ``STRING`` | ID of the run under which to log the tag. Must be provided.                                |
+------------+------------+--------------------------------------------------------------------------------------------+
| run_uuid   | ``STRING`` | [Deprecated, use run_id instead] ID of the run under which to log the tag. This field will |
|            |            | be removed in a future QCFlow version.                                                     |
+------------+------------+--------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the tag. Maximum size depends on storage backend.                                  |
|            |            | All storage backends are guaranteed to support key values up to 250 bytes in size.         |
|            |            | This field is required.                                                                    |
|            |            |                                                                                            |
+------------+------------+--------------------------------------------------------------------------------------------+
| value      | ``STRING`` | String value of the tag being logged. Maximum size depends on storage backend.             |
|            |            | All storage backends are guaranteed to support key values up to 5000 bytes in size.        |
|            |            | This field is required.                                                                    |
|            |            |                                                                                            |
+------------+------------+--------------------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicedeleteTag:

Delete Tag
==========


+--------------------------------+-------------+
|            Endpoint            | HTTP Method |
+================================+=============+
| ``2.0/qcflow/runs/delete-tag`` | ``POST``    |
+--------------------------------+-------------+

Delete a tag on a run. Tags are run metadata that can be updated during a run and after
a run completes.




.. _qcflowDeleteTag:

Request Structure
-----------------






+------------+------------+----------------------------------------------------------------+
| Field Name |    Type    |                          Description                           |
+============+============+================================================================+
| run_id     | ``STRING`` | ID of the run that the tag was logged under. Must be provided. |
|            |            | This field is required.                                        |
|            |            |                                                                |
+------------+------------+----------------------------------------------------------------+
| key        | ``STRING`` | Name of the tag. Maximum size is 255 bytes. Must be provided.  |
|            |            | This field is required.                                        |
|            |            |                                                                |
+------------+------------+----------------------------------------------------------------+

===========================



.. _qcflowMlflowServicelogParam:

Log Param
=========


+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/runs/log-parameter`` | ``POST``    |
+-----------------------------------+-------------+

Log a param used for a run. A param is a key-value pair (string key,
string value). Examples include hyperparameters used for ML model training and
constant dates and values used in an ETL pipeline. A param can be logged only once for a run.




.. _qcflowLogParam:

Request Structure
-----------------






+------------+------------+----------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                         Description                                          |
+============+============+==============================================================================================+
| run_id     | ``STRING`` | ID of the run under which to log the param. Must be provided.                                |
+------------+------------+----------------------------------------------------------------------------------------------+
| run_uuid   | ``STRING`` | [Deprecated, use run_id instead] ID of the run under which to log the param. This field will |
|            |            | be removed in a future QCFlow version.                                                       |
+------------+------------+----------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the param. Maximum size is 255 bytes.                                                |
|            |            | This field is required.                                                                      |
|            |            |                                                                                              |
+------------+------------+----------------------------------------------------------------------------------------------+
| value      | ``STRING`` | String value of the param being logged. Maximum size is 500 bytes.                           |
|            |            | This field is required.                                                                      |
|            |            |                                                                                              |
+------------+------------+----------------------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicegetMetricHistory:

Get Metric History
==================


+------------------------------------+-------------+
|              Endpoint              | HTTP Method |
+====================================+=============+
| ``2.0/qcflow/metrics/get-history`` | ``GET``     |
+------------------------------------+-------------+

Get a list of all values for the specified metric for a given run.




.. _qcflowGetMetricHistory:

Request Structure
-----------------






+-------------+------------+------------------------------------------------------------------------------------------------+
| Field Name  |    Type    |                                          Description                                           |
+=============+============+================================================================================================+
| run_id      | ``STRING`` | ID of the run from which to fetch metric values. Must be provided.                             |
+-------------+------------+------------------------------------------------------------------------------------------------+
| run_uuid    | ``STRING`` | [Deprecated, use run_id instead] ID of the run from which to fetch metric values. This field   |
|             |            | will be removed in a future QCFlow version.                                                    |
+-------------+------------+------------------------------------------------------------------------------------------------+
| metric_key  | ``STRING`` | Name of the metric.                                                                            |
|             |            | This field is required.                                                                        |
|             |            |                                                                                                |
+-------------+------------+------------------------------------------------------------------------------------------------+
| page_token  | ``STRING`` | Token indicating the page of metric history to fetch                                           |
+-------------+------------+------------------------------------------------------------------------------------------------+
| max_results | ``INT32``  | Maximum number of logged instances of a metric for a run to return per call.                   |
|             |            | Backend servers may restrict the value of `max_results` depending on performance requirements. |
|             |            | Requests that do not specify this value will behave as non-paginated queries where all         |
|             |            | metric history values for a given metric within a run are returned in a single response.       |
+-------------+------------+------------------------------------------------------------------------------------------------+

.. _qcflowGetMetricHistoryResponse:

Response Structure
------------------






+-----------------+---------------------------------+-------------------------------------------------------------------------------------+
|   Field Name    |              Type               |                                     Description                                     |
+=================+=================================+=====================================================================================+
| metrics         | An array of :ref:`qcflowmetric` | All logged values for this metric.                                                  |
+-----------------+---------------------------------+-------------------------------------------------------------------------------------+
| next_page_token | ``STRING``                      | Token that can be used to issue a query for the next page of metric history values. |
|                 |                                 | A missing token indicates that no additional metrics are available to fetch.        |
+-----------------+---------------------------------+-------------------------------------------------------------------------------------+

===========================



.. _qcflowMlflowServicesearchRuns:

Search Runs
===========


+----------------------------+-------------+
|          Endpoint          | HTTP Method |
+============================+=============+
| ``2.0/qcflow/runs/search`` | ``POST``    |
+----------------------------+-------------+

Search for runs that satisfy expressions. Search expressions can use :ref:`qcflowMetric` and
:ref:`qcflowParam` keys.




.. _qcflowSearchRuns:

Request Structure
-----------------






+----------------+------------------------+------------------------------------------------------------------------------------------------------+
|   Field Name   |          Type          |                                             Description                                              |
+================+========================+======================================================================================================+
| experiment_ids | An array of ``STRING`` | List of experiment IDs to search over.                                                               |
+----------------+------------------------+------------------------------------------------------------------------------------------------------+
| filter         | ``STRING``             | A filter expression over params, metrics, and tags, that allows returning a subset of                |
|                |                        | runs. The syntax is a subset of SQL that supports ANDing together binary operations                  |
|                |                        | between a param, metric, or tag and a constant.                                                      |
|                |                        |                                                                                                      |
|                |                        | Example: ``metrics.rmse < 1 and params.model_class = 'LogisticRegression'``                          |
|                |                        |                                                                                                      |
|                |                        | You can select columns with special characters (hyphen, space, period, etc.) by using double quotes: |
|                |                        | ``metrics."model class" = 'LinearRegression' and tags."user-name" = 'Tomas'``                        |
|                |                        |                                                                                                      |
|                |                        | Supported operators are ``=``, ``!=``, ``>``, ``>=``, ``<``, and ``<=``.                             |
+----------------+------------------------+------------------------------------------------------------------------------------------------------+
| run_view_type  | :ref:`qcflowviewtype`  | Whether to display only active, only deleted, or all runs.                                           |
|                |                        | Defaults to only active runs.                                                                        |
+----------------+------------------------+------------------------------------------------------------------------------------------------------+
| max_results    | ``INT32``              | Maximum number of runs desired. If unspecified, defaults to 1000.                                    |
|                |                        | All servers are guaranteed to support a `max_results` threshold of at least 50,000                   |
|                |                        | but may support more. Callers of this endpoint are encouraged to pass max_results                    |
|                |                        | explicitly and leverage page_token to iterate through experiments.                                   |
+----------------+------------------------+------------------------------------------------------------------------------------------------------+
| order_by       | An array of ``STRING`` | List of columns to be ordered by, including attributes, params, metrics, and tags with an            |
|                |                        | optional "DESC" or "ASC" annotation, where "ASC" is the default.                                     |
|                |                        | Example: ["params.input DESC", "metrics.alpha ASC", "metrics.rmse"]                                  |
|                |                        | Tiebreaks are done by start_time DESC followed by run_id for runs with the same start time           |
|                |                        | (and this is the default ordering criterion if order_by is not provided).                            |
+----------------+------------------------+------------------------------------------------------------------------------------------------------+
| page_token     | ``STRING``             |                                                                                                      |
+----------------+------------------------+------------------------------------------------------------------------------------------------------+

.. _qcflowSearchRunsResponse:

Response Structure
------------------






+-----------------+------------------------------+--------------------------------------+
|   Field Name    |             Type             |             Description              |
+=================+==============================+======================================+
| runs            | An array of :ref:`qcflowrun` | Runs that match the search criteria. |
+-----------------+------------------------------+--------------------------------------+
| next_page_token | ``STRING``                   |                                      |
+-----------------+------------------------------+--------------------------------------+

===========================



.. _qcflowMlflowServicelistArtifacts:

List Artifacts
==============


+-------------------------------+-------------+
|           Endpoint            | HTTP Method |
+===============================+=============+
| ``2.0/qcflow/artifacts/list`` | ``GET``     |
+-------------------------------+-------------+

List artifacts for a run. Takes an optional ``artifact_path`` prefix which if specified,
the response contains only artifacts with the specified prefix.




.. _qcflowListArtifacts:

Request Structure
-----------------






+------------+------------+-----------------------------------------------------------------------------------------+
| Field Name |    Type    |                                       Description                                       |
+============+============+=========================================================================================+
| run_id     | ``STRING`` | ID of the run whose artifacts to list. Must be provided.                                |
+------------+------------+-----------------------------------------------------------------------------------------+
| run_uuid   | ``STRING`` | [Deprecated, use run_id instead] ID of the run whose artifacts to list. This field will |
|            |            | be removed in a future QCFlow version.                                                  |
+------------+------------+-----------------------------------------------------------------------------------------+
| path       | ``STRING`` | Filter artifacts matching this path (a relative path from the root artifact directory). |
+------------+------------+-----------------------------------------------------------------------------------------+
| page_token | ``STRING`` | Token indicating the page of artifact results to fetch                                  |
+------------+------------+-----------------------------------------------------------------------------------------+

.. _qcflowListArtifactsResponse:

Response Structure
------------------






+-----------------+-----------------------------------+----------------------------------------------------------------------+
|   Field Name    |               Type                |                             Description                              |
+=================+===================================+======================================================================+
| root_uri        | ``STRING``                        | Root artifact directory for the run.                                 |
+-----------------+-----------------------------------+----------------------------------------------------------------------+
| files           | An array of :ref:`qcflowfileinfo` | File location and metadata for artifacts.                            |
+-----------------+-----------------------------------+----------------------------------------------------------------------+
| next_page_token | ``STRING``                        | Token that can be used to retrieve the next page of artifact results |
+-----------------+-----------------------------------+----------------------------------------------------------------------+

===========================



.. _qcflowMlflowServiceupdateRun:

Update Run
==========


+----------------------------+-------------+
|          Endpoint          | HTTP Method |
+============================+=============+
| ``2.0/qcflow/runs/update`` | ``POST``    |
+----------------------------+-------------+

Update run metadata.




.. _qcflowUpdateRun:

Request Structure
-----------------






+------------+------------------------+----------------------------------------------------------------------------+
| Field Name |          Type          |                                Description                                 |
+============+========================+============================================================================+
| run_id     | ``STRING``             | ID of the run to update. Must be provided.                                 |
+------------+------------------------+----------------------------------------------------------------------------+
| run_uuid   | ``STRING``             | [Deprecated, use run_id instead] ID of the run to update.. This field will |
|            |                        | be removed in a future QCFlow version.                                     |
+------------+------------------------+----------------------------------------------------------------------------+
| status     | :ref:`qcflowrunstatus` | Updated status of the run.                                                 |
+------------+------------------------+----------------------------------------------------------------------------+
| end_time   | ``INT64``              | Unix timestamp in milliseconds of when the run ended.                      |
+------------+------------------------+----------------------------------------------------------------------------+
| run_name   | ``STRING``             | Updated name of the run.                                                   |
+------------+------------------------+----------------------------------------------------------------------------+

.. _qcflowUpdateRunResponse:

Response Structure
------------------






+------------+----------------------+------------------------------+
| Field Name |         Type         |         Description          |
+============+======================+==============================+
| run_info   | :ref:`qcflowruninfo` | Updated metadata of the run. |
+------------+----------------------+------------------------------+

===========================



.. _qcflowModelRegistryServicecreateRegisteredModel:

Create RegisteredModel
======================


+-----------------------------------------+-------------+
|                Endpoint                 | HTTP Method |
+=========================================+=============+
| ``2.0/qcflow/registered-models/create`` | ``POST``    |
+-----------------------------------------+-------------+

Throws ``RESOURCE_ALREADY_EXISTS`` if a registered model with the given name exists.




.. _qcflowCreateRegisteredModel:

Request Structure
-----------------






+-------------+---------------------------------------------+--------------------------------------------+
| Field Name  |                    Type                     |                Description                 |
+=============+=============================================+============================================+
| name        | ``STRING``                                  | Register models under this name            |
|             |                                             | This field is required.                    |
|             |                                             |                                            |
+-------------+---------------------------------------------+--------------------------------------------+
| tags        | An array of :ref:`qcflowregisteredmodeltag` | Additional metadata for registered model.  |
+-------------+---------------------------------------------+--------------------------------------------+
| description | ``STRING``                                  | Optional description for registered model. |
+-------------+---------------------------------------------+--------------------------------------------+

.. _qcflowCreateRegisteredModelResponse:

Response Structure
------------------






+------------------+------------------------------+-------------+
|    Field Name    |             Type             | Description |
+==================+==============================+=============+
| registered_model | :ref:`qcflowregisteredmodel` |             |
+------------------+------------------------------+-------------+

===========================



.. _qcflowModelRegistryServicegetRegisteredModel:

Get RegisteredModel
===================


+--------------------------------------+-------------+
|               Endpoint               | HTTP Method |
+======================================+=============+
| ``2.0/qcflow/registered-models/get`` | ``GET``     |
+--------------------------------------+-------------+






.. _qcflowGetRegisteredModel:

Request Structure
-----------------






+------------+------------+------------------------------------------+
| Field Name |    Type    |               Description                |
+============+============+==========================================+
| name       | ``STRING`` | Registered model unique name identifier. |
|            |            | This field is required.                  |
|            |            |                                          |
+------------+------------+------------------------------------------+

.. _qcflowGetRegisteredModelResponse:

Response Structure
------------------






+------------------+------------------------------+-------------+
|    Field Name    |             Type             | Description |
+==================+==============================+=============+
| registered_model | :ref:`qcflowregisteredmodel` |             |
+------------------+------------------------------+-------------+

===========================



.. _qcflowModelRegistryServicerenameRegisteredModel:

Rename RegisteredModel
======================


+-----------------------------------------+-------------+
|                Endpoint                 | HTTP Method |
+=========================================+=============+
| ``2.0/qcflow/registered-models/rename`` | ``POST``    |
+-----------------------------------------+-------------+






.. _qcflowRenameRegisteredModel:

Request Structure
-----------------






+------------+------------+--------------------------------------------------------------+
| Field Name |    Type    |                         Description                          |
+============+============+==============================================================+
| name       | ``STRING`` | Registered model unique name identifier.                     |
|            |            | This field is required.                                      |
|            |            |                                                              |
+------------+------------+--------------------------------------------------------------+
| new_name   | ``STRING`` | If provided, updates the name for this ``registered_model``. |
+------------+------------+--------------------------------------------------------------+

.. _qcflowRenameRegisteredModelResponse:

Response Structure
------------------






+------------------+------------------------------+-------------+
|    Field Name    |             Type             | Description |
+==================+==============================+=============+
| registered_model | :ref:`qcflowregisteredmodel` |             |
+------------------+------------------------------+-------------+

===========================



.. _qcflowModelRegistryServiceupdateRegisteredModel:

Update RegisteredModel
======================


+-----------------------------------------+-------------+
|                Endpoint                 | HTTP Method |
+=========================================+=============+
| ``2.0/qcflow/registered-models/update`` | ``PATCH``   |
+-----------------------------------------+-------------+






.. _qcflowUpdateRegisteredModel:

Request Structure
-----------------






+-------------+------------+---------------------------------------------------------------------+
| Field Name  |    Type    |                             Description                             |
+=============+============+=====================================================================+
| name        | ``STRING`` | Registered model unique name identifier.                            |
|             |            | This field is required.                                             |
|             |            |                                                                     |
+-------------+------------+---------------------------------------------------------------------+
| description | ``STRING`` | If provided, updates the description for this ``registered_model``. |
+-------------+------------+---------------------------------------------------------------------+

.. _qcflowUpdateRegisteredModelResponse:

Response Structure
------------------






+------------------+------------------------------+-------------+
|    Field Name    |             Type             | Description |
+==================+==============================+=============+
| registered_model | :ref:`qcflowregisteredmodel` |             |
+------------------+------------------------------+-------------+

===========================



.. _qcflowModelRegistryServicedeleteRegisteredModel:

Delete RegisteredModel
======================


+-----------------------------------------+-------------+
|                Endpoint                 | HTTP Method |
+=========================================+=============+
| ``2.0/qcflow/registered-models/delete`` | ``DELETE``  |
+-----------------------------------------+-------------+






.. _qcflowDeleteRegisteredModel:

Request Structure
-----------------






+------------+------------+------------------------------------------+
| Field Name |    Type    |               Description                |
+============+============+==========================================+
| name       | ``STRING`` | Registered model unique name identifier. |
|            |            | This field is required.                  |
|            |            |                                          |
+------------+------------+------------------------------------------+

===========================



.. _qcflowModelRegistryServicegetLatestVersions:

Get Latest ModelVersions
========================

.. warning:: Model Stages are deprecated and will be removed in a future major release. To learn more about this deprecation, see our :ref:`migration guide<migrating-from-stages>`.

+------------------------------------------------------+-------------+
|                       Endpoint                       | HTTP Method |
+======================================================+=============+
| ``2.0/qcflow/registered-models/get-latest-versions`` | ``GET``     |
+------------------------------------------------------+-------------+






.. _qcflowGetLatestVersions:

Request Structure
-----------------






+------------+------------------------+------------------------------------------+
| Field Name |          Type          |               Description                |
+============+========================+==========================================+
| name       | ``STRING``             | Registered model unique name identifier. |
|            |                        | This field is required.                  |
|            |                        |                                          |
+------------+------------------------+------------------------------------------+
| stages     | An array of ``STRING`` | List of stages.                          |
+------------+------------------------+------------------------------------------+

.. _qcflowGetLatestVersionsResponse:

Response Structure
------------------






+----------------+---------------------------------------+--------------------------------------------------------------------------------------------------+
|   Field Name   |                 Type                  |                                           Description                                            |
+================+=======================================+==================================================================================================+
| model_versions | An array of :ref:`qcflowmodelversion` | Latest version models for each requests stage. Only return models with current ``READY`` status. |
|                |                                       | If no ``stages`` provided, returns the latest version for each stage, including ``"None"``.      |
+----------------+---------------------------------------+--------------------------------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicecreateModelVersion:

Create ModelVersion
===================


+--------------------------------------+-------------+
|               Endpoint               | HTTP Method |
+======================================+=============+
| ``2.0/qcflow/model-versions/create`` | ``POST``    |
+--------------------------------------+-------------+






.. _qcflowCreateModelVersion:

Request Structure
-----------------






+-------------+------------------------------------------+----------------------------------------------------------------------------------------+
| Field Name  |                   Type                   |                                      Description                                       |
+=============+==========================================+========================================================================================+
| name        | ``STRING``                               | Register model under this name                                                         |
|             |                                          | This field is required.                                                                |
|             |                                          |                                                                                        |
+-------------+------------------------------------------+----------------------------------------------------------------------------------------+
| source      | ``STRING``                               | URI indicating the location of the model artifacts.                                    |
|             |                                          | This field is required.                                                                |
|             |                                          |                                                                                        |
+-------------+------------------------------------------+----------------------------------------------------------------------------------------+
| run_id      | ``STRING``                               | QCFlow run ID for correlation, if ``source`` was generated by an experiment run in     |
|             |                                          | QCFlow tracking server                                                                 |
+-------------+------------------------------------------+----------------------------------------------------------------------------------------+
| tags        | An array of :ref:`qcflowmodelversiontag` | Additional metadata for model version.                                                 |
+-------------+------------------------------------------+----------------------------------------------------------------------------------------+
| run_link    | ``STRING``                               | QCFlow run link - this is the exact link of the run that generated this model version, |
|             |                                          | potentially hosted at another instance of QCFlow.                                      |
+-------------+------------------------------------------+----------------------------------------------------------------------------------------+
| description | ``STRING``                               | Optional description for model version.                                                |
+-------------+------------------------------------------+----------------------------------------------------------------------------------------+

.. _qcflowCreateModelVersionResponse:

Response Structure
------------------






+---------------+---------------------------+-----------------------------------------------------------------+
|  Field Name   |           Type            |                           Description                           |
+===============+===========================+=================================================================+
| model_version | :ref:`qcflowmodelversion` | Return new version number generated for this model in registry. |
+---------------+---------------------------+-----------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicegetModelVersion:

Get ModelVersion
================


+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/model-versions/get`` | ``GET``     |
+-----------------------------------+-------------+






.. _qcflowGetModelVersion:

Request Structure
-----------------






+------------+------------+------------------------------+
| Field Name |    Type    |         Description          |
+============+============+==============================+
| name       | ``STRING`` | Name of the registered model |
|            |            | This field is required.      |
|            |            |                              |
+------------+------------+------------------------------+
| version    | ``STRING`` | Model version number         |
|            |            | This field is required.      |
|            |            |                              |
+------------+------------+------------------------------+

.. _qcflowGetModelVersionResponse:

Response Structure
------------------






+---------------+---------------------------+-------------+
|  Field Name   |           Type            | Description |
+===============+===========================+=============+
| model_version | :ref:`qcflowmodelversion` |             |
+---------------+---------------------------+-------------+

===========================



.. _qcflowModelRegistryServiceupdateModelVersion:

Update ModelVersion
===================


+--------------------------------------+-------------+
|               Endpoint               | HTTP Method |
+======================================+=============+
| ``2.0/qcflow/model-versions/update`` | ``PATCH``   |
+--------------------------------------+-------------+






.. _qcflowUpdateModelVersion:

Request Structure
-----------------






+-------------+------------+---------------------------------------------------------------------+
| Field Name  |    Type    |                             Description                             |
+=============+============+=====================================================================+
| name        | ``STRING`` | Name of the registered model                                        |
|             |            | This field is required.                                             |
|             |            |                                                                     |
+-------------+------------+---------------------------------------------------------------------+
| version     | ``STRING`` | Model version number                                                |
|             |            | This field is required.                                             |
|             |            |                                                                     |
+-------------+------------+---------------------------------------------------------------------+
| description | ``STRING`` | If provided, updates the description for this ``registered_model``. |
+-------------+------------+---------------------------------------------------------------------+

.. _qcflowUpdateModelVersionResponse:

Response Structure
------------------






+---------------+---------------------------+-----------------------------------------------------------------+
|  Field Name   |           Type            |                           Description                           |
+===============+===========================+=================================================================+
| model_version | :ref:`qcflowmodelversion` | Return new version number generated for this model in registry. |
+---------------+---------------------------+-----------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicedeleteModelVersion:

Delete ModelVersion
===================


+--------------------------------------+-------------+
|               Endpoint               | HTTP Method |
+======================================+=============+
| ``2.0/qcflow/model-versions/delete`` | ``DELETE``  |
+--------------------------------------+-------------+






.. _qcflowDeleteModelVersion:

Request Structure
-----------------






+------------+------------+------------------------------+
| Field Name |    Type    |         Description          |
+============+============+==============================+
| name       | ``STRING`` | Name of the registered model |
|            |            | This field is required.      |
|            |            |                              |
+------------+------------+------------------------------+
| version    | ``STRING`` | Model version number         |
|            |            | This field is required.      |
|            |            |                              |
+------------+------------+------------------------------+

===========================



.. _qcflowModelRegistryServicesearchModelVersions:

Search ModelVersions
====================


+--------------------------------------+-------------+
|               Endpoint               | HTTP Method |
+======================================+=============+
| ``2.0/qcflow/model-versions/search`` | ``GET``     |
+--------------------------------------+-------------+






.. _qcflowSearchModelVersions:

Request Structure
-----------------






+-------------+------------------------+----------------------------------------------------------------------------------------------+
| Field Name  |          Type          |                                         Description                                          |
+=============+========================+==============================================================================================+
| filter      | ``STRING``             | String filter condition, like "name='my-model-name'". Must be a single boolean condition,    |
|             |                        | with string values wrapped in single quotes.                                                 |
+-------------+------------------------+----------------------------------------------------------------------------------------------+
| max_results | ``INT64``              | Maximum number of models desired. Max threshold is 200K. Backends may choose a lower default |
|             |                        | value and maximum threshold.                                                                 |
+-------------+------------------------+----------------------------------------------------------------------------------------------+
| order_by    | An array of ``STRING`` | List of columns to be ordered by including model name, version, stage with an                |
|             |                        | optional "DESC" or "ASC" annotation, where "ASC" is the default.                             |
|             |                        | Tiebreaks are done by latest stage transition timestamp, followed by name ASC, followed by   |
|             |                        | version DESC.                                                                                |
+-------------+------------------------+----------------------------------------------------------------------------------------------+
| page_token  | ``STRING``             | Pagination token to go to next page based on previous search query.                          |
+-------------+------------------------+----------------------------------------------------------------------------------------------+

.. _qcflowSearchModelVersionsResponse:

Response Structure
------------------






+-----------------+---------------------------------------+----------------------------------------------------------------------------+
|   Field Name    |                 Type                  |                                Description                                 |
+=================+=======================================+============================================================================+
| model_versions  | An array of :ref:`qcflowmodelversion` | Models that match the search criteria                                      |
+-----------------+---------------------------------------+----------------------------------------------------------------------------+
| next_page_token | ``STRING``                            | Pagination token to request next page of models for the same search query. |
+-----------------+---------------------------------------+----------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicegetModelVersionDownloadUri:

Get Download URI For ModelVersion Artifacts
===========================================


+------------------------------------------------+-------------+
|                    Endpoint                    | HTTP Method |
+================================================+=============+
| ``2.0/qcflow/model-versions/get-download-uri`` | ``GET``     |
+------------------------------------------------+-------------+






.. _qcflowGetModelVersionDownloadUri:

Request Structure
-----------------






+------------+------------+------------------------------+
| Field Name |    Type    |         Description          |
+============+============+==============================+
| name       | ``STRING`` | Name of the registered model |
|            |            | This field is required.      |
|            |            |                              |
+------------+------------+------------------------------+
| version    | ``STRING`` | Model version number         |
|            |            | This field is required.      |
|            |            |                              |
+------------+------------+------------------------------+

.. _qcflowGetModelVersionDownloadUriResponse:

Response Structure
------------------






+--------------+------------+-------------------------------------------------------------------------+
|  Field Name  |    Type    |                               Description                               |
+==============+============+=========================================================================+
| artifact_uri | ``STRING`` | URI corresponding to where artifacts for this model version are stored. |
+--------------+------------+-------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicetransitionModelVersionStage:

Transition ModelVersion Stage
=============================

.. warning:: Model Stages are deprecated and will be removed in a future major release. To learn more about this deprecation, see our :ref:`migration guide<migrating-from-stages>`.

+------------------------------------------------+-------------+
|                    Endpoint                    | HTTP Method |
+================================================+=============+
| ``2.0/qcflow/model-versions/transition-stage`` | ``POST``    |
+------------------------------------------------+-------------+






.. _qcflowTransitionModelVersionStage:

Request Structure
-----------------






+---------------------------+------------+-------------------------------------------------------------------------------------------+
|        Field Name         |    Type    |                                        Description                                        |
+===========================+============+===========================================================================================+
| name                      | ``STRING`` | Name of the registered model                                                              |
|                           |            | This field is required.                                                                   |
|                           |            |                                                                                           |
+---------------------------+------------+-------------------------------------------------------------------------------------------+
| version                   | ``STRING`` | Model version number                                                                      |
|                           |            | This field is required.                                                                   |
|                           |            |                                                                                           |
+---------------------------+------------+-------------------------------------------------------------------------------------------+
| stage                     | ``STRING`` | Transition `model_version` to new stage.                                                  |
|                           |            | This field is required.                                                                   |
|                           |            |                                                                                           |
+---------------------------+------------+-------------------------------------------------------------------------------------------+
| archive_existing_versions | ``BOOL``   | When transitioning a model version to a particular stage, this flag dictates whether all  |
|                           |            | existing model versions in that stage should be atomically moved to the "archived" stage. |
|                           |            | This ensures that at-most-one model version exists in the target stage.                   |
|                           |            | This field is *required* when transitioning a model versions's stage                      |
|                           |            | This field is required.                                                                   |
|                           |            |                                                                                           |
+---------------------------+------------+-------------------------------------------------------------------------------------------+

.. _qcflowTransitionModelVersionStageResponse:

Response Structure
------------------






+---------------+---------------------------+-----------------------+
|  Field Name   |           Type            |      Description      |
+===============+===========================+=======================+
| model_version | :ref:`qcflowmodelversion` | Updated model version |
+---------------+---------------------------+-----------------------+

===========================



.. _qcflowModelRegistryServicesearchRegisteredModels:

Search RegisteredModels
=======================


+-----------------------------------------+-------------+
|                Endpoint                 | HTTP Method |
+=========================================+=============+
| ``2.0/qcflow/registered-models/search`` | ``GET``     |
+-----------------------------------------+-------------+






.. _qcflowSearchRegisteredModels:

Request Structure
-----------------






+-------------+------------------------+--------------------------------------------------------------------------------------------+
| Field Name  |          Type          |                                        Description                                         |
+=============+========================+============================================================================================+
| filter      | ``STRING``             | String filter condition, like "name LIKE 'my-model-name'".                                 |
|             |                        | Interpreted in the backend automatically as "name LIKE '%my-model-name%'".                 |
|             |                        | Single boolean condition, with string values wrapped in single quotes.                     |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| max_results | ``INT64``              | Maximum number of models desired. Default is 100. Max threshold is 1000.                   |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| order_by    | An array of ``STRING`` | List of columns for ordering search results, which can include model name and last updated |
|             |                        | timestamp with an optional "DESC" or "ASC" annotation, where "ASC" is the default.         |
|             |                        | Tiebreaks are done by model name ASC.                                                      |
+-------------+------------------------+--------------------------------------------------------------------------------------------+
| page_token  | ``STRING``             | Pagination token to go to the next page based on a previous search query.                  |
+-------------+------------------------+--------------------------------------------------------------------------------------------+

.. _qcflowSearchRegisteredModelsResponse:

Response Structure
------------------






+-------------------+------------------------------------------+------------------------------------------------------+
|    Field Name     |                   Type                   |                     Description                      |
+===================+==========================================+======================================================+
| registered_models | An array of :ref:`qcflowregisteredmodel` | Registered Models that match the search criteria.    |
+-------------------+------------------------------------------+------------------------------------------------------+
| next_page_token   | ``STRING``                               | Pagination token to request the next page of models. |
+-------------------+------------------------------------------+------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicesetRegisteredModelTag:

Set Registered Model Tag
========================


+------------------------------------------+-------------+
|                 Endpoint                 | HTTP Method |
+==========================================+=============+
| ``2.0/qcflow/registered-models/set-tag`` | ``POST``    |
+------------------------------------------+-------------+






.. _qcflowSetRegisteredModelTag:

Request Structure
-----------------






+------------+------------+----------------------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                               Description                                                |
+============+============+==========================================================================================================+
| name       | ``STRING`` | Unique name of the model.                                                                                |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the tag. Maximum size depends on storage backend.                                                |
|            |            | If a tag with this name already exists, its preexisting value will be replaced by the specified `value`. |
|            |            | All storage backends are guaranteed to support key values up to 250 bytes in size.                       |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+
| value      | ``STRING`` | String value of the tag being logged. Maximum size depends on storage backend.                           |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicesetModelVersionTag:

Set Model Version Tag
=====================


+---------------------------------------+-------------+
|               Endpoint                | HTTP Method |
+=======================================+=============+
| ``2.0/qcflow/model-versions/set-tag`` | ``POST``    |
+---------------------------------------+-------------+






.. _qcflowSetModelVersionTag:

Request Structure
-----------------






+------------+------------+----------------------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                               Description                                                |
+============+============+==========================================================================================================+
| name       | ``STRING`` | Unique name of the model.                                                                                |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+
| version    | ``STRING`` | Model version number.                                                                                    |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the tag. Maximum size depends on storage backend.                                                |
|            |            | If a tag with this name already exists, its preexisting value will be replaced by the specified `value`. |
|            |            | All storage backends are guaranteed to support key values up to 250 bytes in size.                       |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+
| value      | ``STRING`` | String value of the tag being logged. Maximum size depends on storage backend.                           |
|            |            | This field is required.                                                                                  |
|            |            |                                                                                                          |
+------------+------------+----------------------------------------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicedeleteRegisteredModelTag:

Delete Registered Model Tag
===========================


+---------------------------------------------+-------------+
|                  Endpoint                   | HTTP Method |
+=============================================+=============+
| ``2.0/qcflow/registered-models/delete-tag`` | ``DELETE``  |
+---------------------------------------------+-------------+






.. _qcflowDeleteRegisteredModelTag:

Request Structure
-----------------






+------------+------------+-------------------------------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                                    Description                                                    |
+============+============+===================================================================================================================+
| name       | ``STRING`` | Name of the registered model that the tag was logged under.                                                       |
|            |            | This field is required.                                                                                           |
|            |            |                                                                                                                   |
+------------+------------+-------------------------------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the tag. The name must be an exact match; wild-card deletion is not supported. Maximum size is 250 bytes. |
|            |            | This field is required.                                                                                           |
|            |            |                                                                                                                   |
+------------+------------+-------------------------------------------------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicedeleteModelVersionTag:

Delete Model Version Tag
========================


+------------------------------------------+-------------+
|                 Endpoint                 | HTTP Method |
+==========================================+=============+
| ``2.0/qcflow/model-versions/delete-tag`` | ``DELETE``  |
+------------------------------------------+-------------+






.. _qcflowDeleteModelVersionTag:

Request Structure
-----------------






+------------+------------+-------------------------------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                                    Description                                                    |
+============+============+===================================================================================================================+
| name       | ``STRING`` | Name of the registered model that the tag was logged under.                                                       |
|            |            | This field is required.                                                                                           |
|            |            |                                                                                                                   |
+------------+------------+-------------------------------------------------------------------------------------------------------------------+
| version    | ``STRING`` | Model version number that the tag was logged under.                                                               |
|            |            | This field is required.                                                                                           |
|            |            |                                                                                                                   |
+------------+------------+-------------------------------------------------------------------------------------------------------------------+
| key        | ``STRING`` | Name of the tag. The name must be an exact match; wild-card deletion is not supported. Maximum size is 250 bytes. |
|            |            | This field is required.                                                                                           |
|            |            |                                                                                                                   |
+------------+------------+-------------------------------------------------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicedeleteRegisteredModelAlias:

Delete Registered Model Alias
=============================


+----------------------------------------+-------------+
|                Endpoint                | HTTP Method |
+========================================+=============+
| ``2.0/qcflow/registered-models/alias`` | ``DELETE``  |
+----------------------------------------+-------------+






.. _qcflowDeleteRegisteredModelAlias:

Request Structure
-----------------






+------------+------------+---------------------------------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                                     Description                                                     |
+============+============+=====================================================================================================================+
| name       | ``STRING`` | Name of the registered model.                                                                                       |
|            |            | This field is required.                                                                                             |
|            |            |                                                                                                                     |
+------------+------------+---------------------------------------------------------------------------------------------------------------------+
| alias      | ``STRING`` | Name of the alias. The name must be an exact match; wild-card deletion is not supported. Maximum size is 256 bytes. |
|            |            | This field is required.                                                                                             |
|            |            |                                                                                                                     |
+------------+------------+---------------------------------------------------------------------------------------------------------------------+

===========================



.. _qcflowModelRegistryServicegetModelVersionByAlias:

Get Model Version by Alias
==========================


+----------------------------------------+-------------+
|                Endpoint                | HTTP Method |
+========================================+=============+
| ``2.0/qcflow/registered-models/alias`` | ``GET``     |
+----------------------------------------+-------------+






.. _qcflowGetModelVersionByAlias:

Request Structure
-----------------






+------------+------------+-----------------------------------------------+
| Field Name |    Type    |                  Description                  |
+============+============+===============================================+
| name       | ``STRING`` | Name of the registered model.                 |
|            |            | This field is required.                       |
|            |            |                                               |
+------------+------------+-----------------------------------------------+
| alias      | ``STRING`` | Name of the alias. Maximum size is 256 bytes. |
|            |            | This field is required.                       |
|            |            |                                               |
+------------+------------+-----------------------------------------------+

.. _qcflowGetModelVersionByAliasResponse:

Response Structure
------------------






+---------------+---------------------------+-------------+
|  Field Name   |           Type            | Description |
+===============+===========================+=============+
| model_version | :ref:`qcflowmodelversion` |             |
+---------------+---------------------------+-------------+

===========================



.. _qcflowModelRegistryServicesetRegisteredModelAlias:

Set Registered Model Alias
==========================


+----------------------------------------+-------------+
|                Endpoint                | HTTP Method |
+========================================+=============+
| ``2.0/qcflow/registered-models/alias`` | ``POST``    |
+----------------------------------------+-------------+






.. _qcflowSetRegisteredModelAlias:

Request Structure
-----------------






+------------+------------+---------------------------------------------------------------------------------------------------------------+
| Field Name |    Type    |                                                  Description                                                  |
+============+============+===============================================================================================================+
| name       | ``STRING`` | Name of the registered model.                                                                                 |
|            |            | This field is required.                                                                                       |
|            |            |                                                                                                               |
+------------+------------+---------------------------------------------------------------------------------------------------------------+
| alias      | ``STRING`` | Name of the alias. Maximum size depends on storage backend.                                                   |
|            |            | If an alias with this name already exists, its preexisting value will be replaced by the specified `version`. |
|            |            | All storage backends are guaranteed to support alias name values up to 256 bytes in size.                     |
|            |            | This field is required.                                                                                       |
|            |            |                                                                                                               |
+------------+------------+---------------------------------------------------------------------------------------------------------------+
| version    | ``STRING`` | Model version number.                                                                                         |
|            |            | This field is required.                                                                                       |
|            |            |                                                                                                               |
+------------+------------+---------------------------------------------------------------------------------------------------------------+

.. _RESTadd:

Data Structures
===============



.. _qcflowDataset:

Dataset
-------



.. note::
    Experimental: This API may change or be removed in a future release without warning.

Dataset. Represents a reference to data used for training, testing, or evaluation during
the model development process.


+-------------+------------+----------------------------------------------------------------------------------------------+
| Field Name  |    Type    |                                         Description                                          |
+=============+============+==============================================================================================+
| name        | ``STRING`` | The name of the dataset. E.g. ?my.uc.table@2? ?nyc-taxi-dataset?, ?fantastic-elk-3?          |
|             |            | This field is required.                                                                      |
|             |            |                                                                                              |
+-------------+------------+----------------------------------------------------------------------------------------------+
| digest      | ``STRING`` | Dataset digest, e.g. an md5 hash of the dataset that uniquely identifies it                  |
|             |            | within datasets of the same name.                                                            |
|             |            | This field is required.                                                                      |
|             |            |                                                                                              |
+-------------+------------+----------------------------------------------------------------------------------------------+
| source_type | ``STRING`` | Source information for the dataset. Note that the source may not exactly reproduce the       |
|             |            | dataset if it was transformed / modified before use with QCFlow.                             |
|             |            | This field is required.                                                                      |
|             |            |                                                                                              |
+-------------+------------+----------------------------------------------------------------------------------------------+
| source      | ``STRING`` | The type of the dataset source, e.g. ?databricks-uc-table?, ?DBFS?, ?S3?, ...                |
|             |            | This field is required.                                                                      |
|             |            |                                                                                              |
+-------------+------------+----------------------------------------------------------------------------------------------+
| schema      | ``STRING`` | The schema of the dataset. E.g., QCFlow ColSpec JSON for a dataframe, QCFlow TensorSpec JSON |
|             |            | for an ndarray, or another schema format.                                                    |
+-------------+------------+----------------------------------------------------------------------------------------------+
| profile     | ``STRING`` | The profile of the dataset. Summary statistics for the dataset, such as the number of rows   |
|             |            | in a table, the mean / std / mode of each column in a table, or the number of elements       |
|             |            | in an array.                                                                                 |
+-------------+------------+----------------------------------------------------------------------------------------------+

.. _qcflowDatasetInput:

DatasetInput
------------



.. note::
    Experimental: This API may change or be removed in a future release without warning.

DatasetInput. Represents a dataset and input tags.


+------------+-----------------------------------+----------------------------------------------------------------------------------+
| Field Name |               Type                |                                   Description                                    |
+============+===================================+==================================================================================+
| tags       | An array of :ref:`qcflowinputtag` | A list of tags for the dataset input, e.g. a ?context? tag with value ?training? |
+------------+-----------------------------------+----------------------------------------------------------------------------------+
| dataset    | :ref:`qcflowdataset`              | The dataset being used as a Run input.                                           |
|            |                                   | This field is required.                                                          |
|            |                                   |                                                                                  |
+------------+-----------------------------------+----------------------------------------------------------------------------------+

.. _qcflowExperiment:

Experiment
----------



Experiment


+-------------------+----------------------------------------+--------------------------------------------------------------------+
|    Field Name     |                  Type                  |                            Description                             |
+===================+========================================+====================================================================+
| experiment_id     | ``STRING``                             | Unique identifier for the experiment.                              |
+-------------------+----------------------------------------+--------------------------------------------------------------------+
| name              | ``STRING``                             | Human readable name that identifies the experiment.                |
+-------------------+----------------------------------------+--------------------------------------------------------------------+
| artifact_location | ``STRING``                             | Location where artifacts for the experiment are stored.            |
+-------------------+----------------------------------------+--------------------------------------------------------------------+
| lifecycle_stage   | ``STRING``                             | Current life cycle stage of the experiment: "active" or "deleted". |
|                   |                                        | Deleted experiments are not returned by APIs.                      |
+-------------------+----------------------------------------+--------------------------------------------------------------------+
| last_update_time  | ``INT64``                              | Last update time                                                   |
+-------------------+----------------------------------------+--------------------------------------------------------------------+
| creation_time     | ``INT64``                              | Creation time                                                      |
+-------------------+----------------------------------------+--------------------------------------------------------------------+
| tags              | An array of :ref:`qcflowexperimenttag` | Tags: Additional metadata key-value pairs.                         |
+-------------------+----------------------------------------+--------------------------------------------------------------------+

.. _qcflowExperimentTag:

ExperimentTag
-------------



Tag for an experiment.


+------------+------------+----------------+
| Field Name |    Type    |  Description   |
+============+============+================+
| key        | ``STRING`` | The tag key.   |
+------------+------------+----------------+
| value      | ``STRING`` | The tag value. |
+------------+------------+----------------+

.. _qcflowFileInfo:

FileInfo
--------






+------------+------------+---------------------------------------------------+
| Field Name |    Type    |                    Description                    |
+============+============+===================================================+
| path       | ``STRING`` | Path relative to the root artifact directory run. |
+------------+------------+---------------------------------------------------+
| is_dir     | ``BOOL``   | Whether the path is a directory.                  |
+------------+------------+---------------------------------------------------+
| file_size  | ``INT64``  | Size in bytes. Unset for directories.             |
+------------+------------+---------------------------------------------------+

.. _qcflowInputTag:

InputTag
--------



.. note::
    Experimental: This API may change or be removed in a future release without warning.

Tag for an input.


+------------+------------+-------------------------+
| Field Name |    Type    |       Description       |
+============+============+=========================+
| key        | ``STRING`` | The tag key.            |
|            |            | This field is required. |
|            |            |                         |
+------------+------------+-------------------------+
| value      | ``STRING`` | The tag value.          |
|            |            | This field is required. |
|            |            |                         |
+------------+------------+-------------------------+

.. _qcflowMetric:

Metric
------



Metric associated with a run, represented as a key-value pair.


+------------+------------+--------------------------------------------------+
| Field Name |    Type    |                   Description                    |
+============+============+==================================================+
| key        | ``STRING`` | Key identifying this metric.                     |
+------------+------------+--------------------------------------------------+
| value      | ``DOUBLE`` | Value associated with this metric.               |
+------------+------------+--------------------------------------------------+
| timestamp  | ``INT64``  | The timestamp at which this metric was recorded. |
+------------+------------+--------------------------------------------------+
| step       | ``INT64``  | Step at which to log the metric.                 |
+------------+------------+--------------------------------------------------+

.. _qcflowModelVersion:

ModelVersion
------------






+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
|       Field Name       |                   Type                   |                                                  Description                                                   |
+========================+==========================================+================================================================================================================+
| name                   | ``STRING``                               | Unique name of the model                                                                                       |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| version                | ``STRING``                               | Model's version number.                                                                                        |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| creation_timestamp     | ``INT64``                                | Timestamp recorded when this ``model_version`` was created.                                                    |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| last_updated_timestamp | ``INT64``                                | Timestamp recorded when metadata for this ``model_version`` was last updated.                                  |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| user_id                | ``STRING``                               | User that created this ``model_version``.                                                                      |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| current_stage          | ``STRING``                               | Current stage for this ``model_version``.                                                                      |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| description            | ``STRING``                               | Description of this ``model_version``.                                                                         |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| source                 | ``STRING``                               | URI indicating the location of the source model artifacts, used when creating ``model_version``                |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| run_id                 | ``STRING``                               | QCFlow run ID used when creating ``model_version``, if ``source`` was generated by an                          |
|                        |                                          | experiment run stored in QCFlow tracking server.                                                               |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| status                 | :ref:`qcflowmodelversionstatus`          | Current status of ``model_version``                                                                            |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| status_message         | ``STRING``                               | Details on current ``status``, if it is pending or failed.                                                     |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| tags                   | An array of :ref:`qcflowmodelversiontag` | Tags: Additional metadata key-value pairs for this ``model_version``.                                          |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| run_link               | ``STRING``                               | Run Link: Direct link to the run that generated this version. This field is set at model version creation time |
|                        |                                          | only for model versions whose source run is from a tracking server that is different from the registry server. |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+
| aliases                | An array of ``STRING``                   | Aliases pointing to this ``model_version``.                                                                    |
+------------------------+------------------------------------------+----------------------------------------------------------------------------------------------------------------+

.. _qcflowModelVersionTag:

ModelVersionTag
---------------



Tag for a model version.


+------------+------------+----------------+
| Field Name |    Type    |  Description   |
+============+============+================+
| key        | ``STRING`` | The tag key.   |
+------------+------------+----------------+
| value      | ``STRING`` | The tag value. |
+------------+------------+----------------+

.. _qcflowParam:

Param
-----



Param associated with a run.


+------------+------------+-----------------------------------+
| Field Name |    Type    |            Description            |
+============+============+===================================+
| key        | ``STRING`` | Key identifying this param.       |
+------------+------------+-----------------------------------+
| value      | ``STRING`` | Value associated with this param. |
+------------+------------+-----------------------------------+

.. _qcflowRegisteredModel:

RegisteredModel
---------------






+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
|       Field Name       |                     Type                      |                                   Description                                    |
+========================+===============================================+==================================================================================+
| name                   | ``STRING``                                    | Unique name for the model.                                                       |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| creation_timestamp     | ``INT64``                                     | Timestamp recorded when this ``registered_model`` was created.                   |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| last_updated_timestamp | ``INT64``                                     | Timestamp recorded when metadata for this ``registered_model`` was last updated. |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| user_id                | ``STRING``                                    | User that created this ``registered_model``                                      |
|                        |                                               | NOTE: this field is not currently returned.                                      |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| description            | ``STRING``                                    | Description of this ``registered_model``.                                        |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| latest_versions        | An array of :ref:`qcflowmodelversion`         | Collection of latest model versions for each stage.                              |
|                        |                                               | Only contains models with current ``READY`` status.                              |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| tags                   | An array of :ref:`qcflowregisteredmodeltag`   | Tags: Additional metadata key-value pairs for this ``registered_model``.         |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+
| aliases                | An array of :ref:`qcflowregisteredmodelalias` | Aliases pointing to model versions associated with this ``registered_model``.    |
+------------------------+-----------------------------------------------+----------------------------------------------------------------------------------+

.. _qcflowRegisteredModelAlias:

RegisteredModelAlias
--------------------



Alias for a registered model


+------------+------------+----------------------------------------------------+
| Field Name |    Type    |                    Description                     |
+============+============+====================================================+
| alias      | ``STRING`` | The name of the alias.                             |
+------------+------------+----------------------------------------------------+
| version    | ``STRING`` | The model version number that the alias points to. |
+------------+------------+----------------------------------------------------+

.. _qcflowRegisteredModelTag:

RegisteredModelTag
------------------



Tag for a registered model


+------------+------------+----------------+
| Field Name |    Type    |  Description   |
+============+============+================+
| key        | ``STRING`` | The tag key.   |
+------------+------------+----------------+
| value      | ``STRING`` | The tag value. |
+------------+------------+----------------+

.. _qcflowRun:

Run
---



A single run.


+------------+------------------------+---------------+
| Field Name |          Type          |  Description  |
+============+========================+===============+
| info       | :ref:`qcflowruninfo`   | Run metadata. |
+------------+------------------------+---------------+
| data       | :ref:`qcflowrundata`   | Run data.     |
+------------+------------------------+---------------+
| inputs     | :ref:`qcflowruninputs` | Run inputs.   |
+------------+------------------------+---------------+

.. _qcflowRunData:

RunData
-------



Run data (metrics, params, and tags).


+------------+---------------------------------+--------------------------------------+
| Field Name |              Type               |             Description              |
+============+=================================+======================================+
| metrics    | An array of :ref:`qcflowmetric` | Run metrics.                         |
+------------+---------------------------------+--------------------------------------+
| params     | An array of :ref:`qcflowparam`  | Run parameters.                      |
+------------+---------------------------------+--------------------------------------+
| tags       | An array of :ref:`qcflowruntag` | Additional metadata key-value pairs. |
+------------+---------------------------------+--------------------------------------+

.. _qcflowRunInfo:

RunInfo
-------



Metadata of a single run.


+-----------------+------------------------+----------------------------------------------------------------------------------+
|   Field Name    |          Type          |                                   Description                                    |
+=================+========================+==================================================================================+
| run_id          | ``STRING``             | Unique identifier for the run.                                                   |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| run_uuid        | ``STRING``             | [Deprecated, use run_id instead] Unique identifier for the run. This field will  |
|                 |                        | be removed in a future QCFlow version.                                           |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| run_name        | ``STRING``             | The name of the run.                                                             |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| experiment_id   | ``STRING``             | The experiment ID.                                                               |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| user_id         | ``STRING``             | User who initiated the run.                                                      |
|                 |                        | This field is deprecated as of QCFlow 1.0, and will be removed in a future       |
|                 |                        | QCFlow release. Use 'qcflow.user' tag instead.                                   |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| status          | :ref:`qcflowrunstatus` | Current status of the run.                                                       |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| start_time      | ``INT64``              | Unix timestamp of when the run started in milliseconds.                          |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| end_time        | ``INT64``              | Unix timestamp of when the run ended in milliseconds.                            |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| artifact_uri    | ``STRING``             | URI of the directory where artifacts should be uploaded.                         |
|                 |                        | This can be a local path (starting with "/"), or a distributed file system (DFS) |
|                 |                        | path, like ``s3://bucket/directory`` or ``dbfs:/my/directory``.                  |
|                 |                        | If not set, the local ``./mlruns`` directory is  chosen.                         |
+-----------------+------------------------+----------------------------------------------------------------------------------+
| lifecycle_stage | ``STRING``             | Current life cycle stage of the experiment : OneOf("active", "deleted")          |
+-----------------+------------------------+----------------------------------------------------------------------------------+

.. _qcflowRunInputs:

RunInputs
---------



.. note::
    Experimental: This API may change or be removed in a future release without warning.

Run inputs.


+----------------+---------------------------------------+----------------------------+
|   Field Name   |                 Type                  |        Description         |
+================+=======================================+============================+
| dataset_inputs | An array of :ref:`qcflowdatasetinput` | Dataset inputs to the Run. |
+----------------+---------------------------------------+----------------------------+

.. _qcflowRunTag:

RunTag
------



Tag for a run.


+------------+------------+----------------+
| Field Name |    Type    |  Description   |
+============+============+================+
| key        | ``STRING`` | The tag key.   |
+------------+------------+----------------+
| value      | ``STRING`` | The tag value. |
+------------+------------+----------------+

.. _qcflowModelVersionStatus:

ModelVersionStatus
------------------




+----------------------+-----------------------------------------------------------------------------------------+
|         Name         |                                       Description                                       |
+======================+=========================================================================================+
| PENDING_REGISTRATION | Request to register a new model version is pending as server performs background tasks. |
+----------------------+-----------------------------------------------------------------------------------------+
| FAILED_REGISTRATION  | Request to register a new model version has failed.                                     |
+----------------------+-----------------------------------------------------------------------------------------+
| READY                | Model version is ready for use.                                                         |
+----------------------+-----------------------------------------------------------------------------------------+

.. _qcflowRunStatus:

RunStatus
---------


Status of a run.

+-----------+------------------------------------------+
|   Name    |               Description                |
+===========+==========================================+
| RUNNING   | Run has been initiated.                  |
+-----------+------------------------------------------+
| SCHEDULED | Run is scheduled to run at a later time. |
+-----------+------------------------------------------+
| FINISHED  | Run has completed.                       |
+-----------+------------------------------------------+
| FAILED    | Run execution failed.                    |
+-----------+------------------------------------------+
| KILLED    | Run killed by user.                      |
+-----------+------------------------------------------+

.. _qcflowViewType:

ViewType
--------


View type for ListExperiments query.

+--------------+------------------------------------------+
|     Name     |               Description                |
+==============+==========================================+
| ACTIVE_ONLY  | Default. Return only active experiments. |
+--------------+------------------------------------------+
| DELETED_ONLY | Return only deleted experiments.         |
+--------------+------------------------------------------+
| ALL          | Get all experiments.                     |
+--------------+------------------------------------------+
