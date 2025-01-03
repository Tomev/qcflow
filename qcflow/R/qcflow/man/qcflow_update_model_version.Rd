% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/model-registry.R
\name{qcflow_update_model_version}
\alias{qcflow_update_model_version}
\title{Update model version}
\usage{
qcflow_update_model_version(name, version, description, client = NULL)
}
\arguments{
\item{name}{Name of the registered model.}

\item{version}{Model version number.}

\item{description}{Description of this model version.}

\item{client}{(Optional) An QCFlow client object returned from \link[qcflow]{qcflow_client}.
If specified, QCFlow will use the tracking server associated with the passed-in client. If
unspecified (the common case),
QCFlow will use the tracking server associated with the current tracking URI.}
}
\description{
Updates a model version
}
