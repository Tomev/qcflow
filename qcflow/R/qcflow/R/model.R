#' Save Model for QCFlow
#'
#' Saves model in QCFlow format that can later be used for prediction and serving. This method is
#' generic to allow package authors to save custom model types.
#'
#' @param model The model that will perform a prediction.
#' @param path Destination path where this QCFlow compatible model
#'   will be saved.
#' @param model_spec QCFlow model config this model flavor is being added to.
#' @param ... Optional additional arguments.
#' @importFrom yaml write_yaml
#' @export
qcflow_save_model <- function(model, path, model_spec = list(), ...) {
  UseMethod("qcflow_save_model")
}

#' Log Model
#'
#' Logs a model for this run. Similar to `qcflow_save_model()`
#' but stores model as an artifact within the active run.
#'
#' @param model The model that will perform a prediction.
#' @param artifact_path Destination path where this QCFlow compatible model
#'   will be saved.
#' @param ... Optional additional arguments passed to `qcflow_save_model()` when persisting the
#'   model. For example, `conda_env = /path/to/conda.yaml` may be passed to specify a conda
#'   dependencies file for flavors (e.g. keras) that support conda environments.
#'
#' @export
qcflow_log_model <- function(model, artifact_path, ...) {
  temp_path <- fs::path_temp(artifact_path)
  model_spec <- qcflow_save_model(model, path = temp_path, model_spec = list(
    utc_time_created = qcflow_timestamp(),
    run_id = qcflow_get_active_run_id_or_start_run(),
    artifact_path = artifact_path,
    flavors = list()
  ), ...)
  res <- qcflow_log_artifact(path = temp_path, artifact_path = artifact_path)
  tryCatch({ qcflow_record_logged_model(model_spec) }, error = function(e) {
    warning(paste("Logging model metadata to the tracking server has failed, possibly due to older",
                  "server version. The model artifacts have been logged successfully.",
                  "In addition to exporting model artifacts, QCFlow clients 1.7.0 and above",
                  "attempt to record model metadata to the  tracking store. If logging to a",
                  "qcflow server via REST, consider  upgrading the server version to QCFlow",
                  "1.7.0 or above.", sep=" "))
  })
  res
}

qcflow_write_model_spec <- function(path, content) {
  write_yaml(
    purrr::compact(content),
    file.path(path, "MLmodel")
  )
}

qcflow_timestamp <- function() {
  withr::with_options(
    c(digits.secs = 2),
    format(
      as.POSIXlt(Sys.time(), tz = "GMT"),
      "%Y-%m-%d %H:%M:%OS6"
    )
  )
}

#' Load QCFlow Model
#'
#' Loads an QCFlow model. QCFlow models can have multiple model flavors. Not all flavors / models
#' can be loaded in R. This method by default searches for a flavor supported by R/QCFlow.
#'
#' @template roxlate-model-uri
#' @template roxlate-client
#' @param flavor Optional flavor specification (string). Can be used to load a particular flavor in
#' case there are multiple flavors available.
#' @export
qcflow_load_model <- function(model_uri, flavor = NULL, client = qcflow_client()) {
  model_path <- qcflow_download_artifacts_from_uri(model_uri, client = client)
  supported_flavors <- supported_model_flavors()
  spec <- yaml::read_yaml(fs::path(model_path, "MLmodel"))
  available_flavors <- intersect(names(spec$flavors), supported_flavors)

  if (length(available_flavors) == 0) {
    stop(
      "Model does not contain any flavor supported by qcflow/R. ",
      "Model flavors: ",
      paste(names(spec$flavors), collapse = ", "),
      ". Supported flavors: ",
      paste(supported_flavors, collapse = ", "))
  }

  if (!is.null(flavor)) {
    if (!flavor %in% supported_flavors) {
      stop("Invalid flavor.", paste("Supported flavors:",
                              paste(supported_flavors, collapse = ", ")))
    }
    if (!flavor %in% available_flavors) {
      stop("Model does not contain requested flavor. ",
           paste("Available flavors:", paste(available_flavors, collapse = ", ")))
    }
  } else {
    if (length(available_flavors) > 1) {
      warning(paste("Multiple model flavors available (", paste(available_flavors, collapse = ", "),
                    " ).  loading flavor '", available_flavors[[1]], "'", ""))
    }
    flavor <- available_flavors[[1]]
  }

  flavor <- qcflow_flavor(flavor, spec$flavors[[flavor]])
  qcflow_load_flavor(flavor, model_path)
}

new_qcflow_flavor <- function(class = character(0), spec = NULL) {
  flavor <- structure(character(0), class = c(class, "qcflow_flavor"))
  attributes(flavor)$spec <- spec

  flavor
}

# Create an QCFlow Flavor Object
#
# This function creates an `qcflow_flavor` object that can be used to dispatch
#   the `qcflow_load_flavor()` method.
#
# @param flavor The name of the flavor.
# @keywords internal
qcflow_flavor <- function(flavor, spec) {
  new_qcflow_flavor(class = paste0("qcflow_flavor_", flavor), spec = spec)
}

#' Load QCFlow Model Flavor
#'
#' Loads an QCFlow model using a specific flavor. This method is called internally by
#' \link[qcflow]{qcflow_load_model}, but is exposed for package authors to extend the supported
#' QCFlow models. See https://qcflow.org/docs/latest/models.html#storage-format for more
#' info on QCFlow model flavors.
#'
#' @param flavor An QCFlow flavor object loaded by \link[qcflow]{qcflow_load_model}, with class
#' loaded from the flavor field in an MLmodel file.
#' @param model_path The path to the QCFlow model wrapped in the correct
#'   class.
#'
#' @export
qcflow_load_flavor <- function(flavor, model_path) {
  UseMethod("qcflow_load_flavor")
}

#' Generate Prediction with QCFlow Model
#'
#' Performs prediction over a model loaded using
#' \code{qcflow_load_model()}, to be used by package authors
#' to extend the supported QCFlow models.
#'
#' @param model The loaded QCFlow model flavor.
#' @param data A data frame to perform scoring.
#' @param ... Optional additional arguments passed to underlying predict
#'   methods.
#'
#' @export
qcflow_predict <- function(model, data, ...) {
  UseMethod("qcflow_predict")
}


# Generate predictions using a saved R QCFlow model.
# Input and output are read from and written to a specified input / output file or stdin / stdout.
#
# @param input_path Path to 'JSON' or 'CSV' file to be used for prediction. If not specified data is
#                   read from the stdin.
# @param output_path 'JSON' file where the prediction will be written to. If not specified,
#                     data is written out to stdout.

qcflow_rfunc_predict <- function(model_path, input_path = NULL, output_path = NULL,
                                 content_type = NULL) {
  model <- qcflow_load_model(model_path)
  input_path <- input_path %||% "stdin"
  output_path <- output_path %||% stdout()

  data <- switch(
    content_type %||% "json",
    json = parse_json(input_path),
    csv = utils::read.csv(input_path),
    stop("Unsupported input file format.")
  )
  model <- qcflow_load_model(model_path)
  prediction <- qcflow_predict(model, data)
  jsonlite::write_json(prediction, output_path, digits = NA)
  invisible(NULL)
}

supported_model_flavors <- function() {
  purrr::map(utils::methods(generic.function = qcflow_load_flavor),
             ~ gsub("qcflow_load_flavor\\.qcflow_flavor_", "", .x))
}

# Helper function to parse data frame from json.
parse_json <- function(input_path) {
  json <- jsonlite::fromJSON(input_path, simplifyVector = TRUE)
  data_fields <- intersect(names(json), c("dataframe_split", "dataframe_records"))
  if (length(data_fields) != 1) {
    stop(paste(
      "Invalid input. The input must contain 'dataframe_split' or 'dataframe_records' but not both.",
      "Got input fields", names(json))
    )
  }
  switch(data_fields[[1]],
    dataframe_split = {
      elms <- names(json$dataframe_split)
      if (length(setdiff(elms, c("columns", "index", "data"))) != 0
      || length(setdiff(c("data"), elms) != 0)) {
        stop(paste("Invalid input. Make sure the input json data is in 'split' format.", elms))
      }
      data <- if (any(class(json$dataframe_split$data) == "list")) {
        max_len <- max(sapply(json$dataframe_split$data, length))
        fill_nas <- function(row) {
          append(row, rep(NA, max_len - length(row)))
        }
        rows <- lapply(json$dataframe_split$data, fill_nas)
        Reduce(rbind, rows)
      } else {
        json$dataframe_split$data
      }

      df <- data.frame(data, row.names=json$dataframe_split$index)
      names(df) <- json$dataframe_split$columns
      df
    },
    dataframe_records = json$dataframe_records,
    stop(paste("Unsupported JSON format"))
  )
}
