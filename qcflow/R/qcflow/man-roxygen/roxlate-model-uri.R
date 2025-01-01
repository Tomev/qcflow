#' @param model_uri The location, in URI format, of the QCFlow model.
#' @details The URI scheme must be supported by QCFlow - i.e. there has to be an QCFlow artifact
#'          repository corresponding to the scheme of the URI. The content is expected to point to a
#'          directory containing MLmodel. The following are examples of valid model uris:
#'
#'                  - ``file:///absolute/path/to/local/model``
#'                  - ``file:relative/path/to/local/model``
#'                  - ``s3://my_bucket/path/to/model``
#'                  - ``runs:/<qcflow_run_id>/run-relative/path/to/model``
#'                  - ``models:/<model_name>/<model_version>``
#'                  - ``models:/<model_name>/<stage>``
#'
#'  For more information about supported URI schemes, see the Artifacts Documentation at
#'  https://www.qcflow.org/docs/latest/tracking.html#artifact-stores.
