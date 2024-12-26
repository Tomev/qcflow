#' @rdname qcflow_save_model
#' @export
qcflow_save_model.crate <- function(model, path, model_spec=list(), ...) {
  if (dir.exists(path)) unlink(path, recursive = TRUE)
  dir.create(path)

  serialized <- serialize(model, NULL)

  saveRDS(
    serialized,
    file.path(path, "crate.bin")
  )

  model_spec$flavors <- append(model_spec$flavors, list(
    crate = list(
      version = "0.1.0",
      model = "crate.bin"
    )
  ))
  qcflow_write_model_spec(path, model_spec)
  model_spec
}

#' @export
qcflow_load_flavor.qcflow_flavor_crate <- function(flavor, model_path) {
  unserialize(readRDS(file.path(model_path, "crate.bin")))
}

#' @export
qcflow_predict.crate <- function(model, data, ...) {
  do.call(model, list(data, ...))
}
