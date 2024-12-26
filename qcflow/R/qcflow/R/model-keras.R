#' @rdname qcflow_save_model
#' @param conda_env Path to Conda dependencies file.
#' @export
qcflow_save_model.keras.engine.training.Model <- function(model,
                                                          path,
                                                          model_spec = list(),
                                                          conda_env = NULL,
                                                          ...) {
  assert_pkg_installed("keras")

  if (dir.exists(path)) unlink(path, recursive = TRUE)
  dir.create(path)

  keras::save_model_hdf5(model, filepath = file.path(path, "model.h5"), include_optimizer = TRUE)
  version <- as.character(utils::packageVersion("keras"))

  pip_deps <- list("qcflow", paste("keras>=", version, sep = ""))
  conda_env <- create_default_conda_env_if_absent(path, conda_env, default_pip_deps = pip_deps)
  python_env <- create_python_env(path, dependencies = pip_deps)
  keras_conf <- list(
    keras = list(
      version = "2.2.2",
      data = "model.h5"))
  pyfunc_conf <- create_pyfunc_conf(
    loader_module = "qcflow.keras",
    data = "model.h5",
    env = list(conda = conda_env, virtualenv = python_env),
  )
  model_spec$flavors <- append(append(model_spec$flavors, keras_conf), pyfunc_conf)
  qcflow_write_model_spec(path, model_spec)

  model_spec
}

#' @export
qcflow_load_flavor.qcflow_flavor_keras <- function(flavor, model_path) {
  if (!requireNamespace("keras", quietly = TRUE)) {
    stop("The 'keras' package must be installed.")
  }

  keras::load_model_hdf5(file.path(model_path, "model.h5"))
}

#' @export
qcflow_predict.keras.engine.training.Model <- function(model, data, ...) {
  if (!requireNamespace("keras", quietly = TRUE)) {
    stop("The 'keras' package must be installed.")
  }

  stats::predict(model, as.matrix(data), ...)
}
