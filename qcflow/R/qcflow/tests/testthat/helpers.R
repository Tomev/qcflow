qcflow_clear_test_dir <- function(path) {
  purrr::safely(qcflow_end_run)()
  qcflow:::qcflow_set_active_experiment_id(NULL)
  if (dir.exists(path)) {
    unlink(path, recursive = TRUE)
  }
  deregister_local_servers()
}

deregister_local_servers <- function() {
  purrr::walk(as.list(qcflow:::.globals$url_mapping), ~ .x$handle$kill())
  rlang::env_unbind(qcflow:::.globals, "url_mapping")
}
