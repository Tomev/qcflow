#' @include tracking-observer.R
NULL

qcflow_push_active_run_id <- function(run_id) {
  .globals$active_run_stack <- c(.globals$active_run_stack, run_id)
  qcflow_register_tracking_event("active_run_id", list(run_id = run_id))
}

qcflow_pop_active_run_id <- function() {
  .globals$active_run_stack <- .globals$active_run_stack[1:length(.globals$active_run_stack) - 1]
}

qcflow_get_active_run_id <- function() {
  if (length(.globals$active_run_stack) == 0) {
    NULL
  } else {
    .globals$active_run_stack[length(.globals$active_run_stack)]
  }
}

qcflow_set_active_experiment_id <- function(experiment_id) {
  .globals$active_experiment_id <- experiment_id
  qcflow_register_tracking_event(
    "active_experiment_id", list(experiment_id = experiment_id)
  )
}

qcflow_get_active_experiment_id <- function() {
  .globals$active_experiment_id
}

#' Set Remote Tracking URI
#'
#' Specifies the URI to the remote QCFlow server that will be used
#' to track experiments.
#'
#' @param uri The URI to the remote QCFlow server.
#'
#' @export
qcflow_set_tracking_uri <- function(uri) {
  .globals$tracking_uri <- uri
  qcflow_register_tracking_event("tracking_uri", list(uri = uri))

  invisible(uri)
}

#' Get Remote Tracking URI
#'
#' Gets the remote tracking URI.
#'
#' @export
qcflow_get_tracking_uri <- function() {
  .globals$tracking_uri %||% {
    env_uri <- Sys.getenv("QCFLOW_TRACKING_URI")
    if (nchar(env_uri)) env_uri else paste("file://", fs::path_abs("mlruns"), sep = "")
  }
}
