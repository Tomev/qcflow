#' @importFrom utils browseURL
qcflow_view_url <- function(url) {
  getOption("page_viewer", browseURL)(url)

  invisible(url)
}

#' Run QCFlow User Interface
#'
#' Launches the QCFlow user interface.
#'
#' @examples
#' \dontrun{
#' library(qcflow)
#'
#' # launch qcflow ui locally
#' qcflow_ui()
#'
#' # launch qcflow ui for existing qcflow server
#' qcflow_set_tracking_uri("http://tracking-server:5000")
#' qcflow_ui()
#' }
#'
#' @template roxlate-client
#' @param ... Optional arguments passed to `qcflow_server()` when `x` is a path to a file store.
#' @export
qcflow_ui <- function(client, ...) {
  UseMethod("qcflow_ui")
}

#' @export
qcflow_ui.qcflow_client <- function(client, ...) {
  qcflow_view_url(client$get_host_creds()$host)
}

#' @export
qcflow_ui.NULL <- function(client, ...) {
  client <- qcflow_client()
  qcflow_ui(client)
}
