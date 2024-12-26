# Runs a generic QCFlow command through the command-line interface.
#
# @param ... The parameters to pass to the command line.
# @param background Should this command be triggered as a background task?
#   Defaults to \code{FALSE}.
# @param echo Print the standard output and error to the screen? Defaults to
#   \code{TRUE}, does not apply to background tasks.
# @param stderr_callback \code{NULL} (the default), or a function to call for 
#   every chunk of the standard error, passed to \code{\link[=processx:run]{processx::run()}}.
# @param client QCFlow client to provide environment for the cli process.
#
# @return A \code{processx} task.
#' @importFrom processx run
#' @importFrom processx process
#' @importFrom withr with_envvar
qcflow_cli <- function(...,
                       background = FALSE,
                       echo = TRUE,
                       stderr_callback = NULL,
                       client = qcflow_client()) {
  env <- if (is.null(client)) list() else client$get_cli_env()
  args <- list(...)
  verbose <- qcflow_is_verbose()
  python <- dirname(python_bin())
  qcflow_bin <- python_qcflow_bin()
  env <- modifyList(list(
    PATH = paste(python, Sys.getenv("PATH"), sep = ":"),
    QCFLOW_TRACKING_URI = qcflow_get_tracking_uri(),
    QCFLOW_BIN = qcflow_bin,
    QCFLOW_PYTHON_BIN = python_bin()
  ), env)
  QCFLOW_CONDA_HOME <- Sys.getenv("QCFLOW_CONDA_HOME", NA)
  if (!is.na(QCFLOW_CONDA_HOME)) {
    env$QCFLOW_CONDA_HOME <- QCFLOW_CONDA_HOME
  }
  with_envvar(env, {
    if (background) {
      result <- process$new(qcflow_bin, args = unlist(args), echo_cmd = verbose, supervise = TRUE)
    } else {
      result <- run(qcflow_bin, args = unlist(args), echo = echo, echo_cmd = verbose, stderr_callback = stderr_callback)
    }
  })
  invisible(result)
}

qcflow_cli_file_output <- function(response) {
  temp_file <- tempfile(fileext = ".txt")
  writeLines(response$stdout, temp_file)
  temp_file
}
