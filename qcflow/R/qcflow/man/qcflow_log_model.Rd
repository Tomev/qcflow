% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/model.R
\name{qcflow_log_model}
\alias{qcflow_log_model}
\title{Log Model}
\usage{
qcflow_log_model(model, artifact_path, ...)
}
\arguments{
\item{model}{The model that will perform a prediction.}

\item{artifact_path}{Destination path where this QCFlow compatible model
will be saved.}

\item{...}{Optional additional arguments passed to `qcflow_save_model()` when persisting the
model. For example, `conda_env = /path/to/conda.yaml` may be passed to specify a conda
dependencies file for flavors (e.g. keras) that support conda environments.}
}
\description{
Logs a model for this run. Similar to `qcflow_save_model()`
but stores model as an artifact within the active run.
}
