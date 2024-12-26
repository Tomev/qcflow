qcflow_is_verbose <- function() {
  nchar(Sys.getenv("QCFLOW_VERBOSE")) > 0 || getOption("qcflow.verbose", FALSE)
}

qcflow_verbose_message <- function(...) {
  if (qcflow_is_verbose()) {
    message(...)
  }
}
