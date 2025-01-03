% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/model-registry.R
\name{qcflow_create_registered_model}
\alias{qcflow_create_registered_model}
\title{Create registered model}
\usage{
qcflow_create_registered_model(
  name,
  tags = NULL,
  description = NULL,
  client = NULL
)
}
\arguments{
\item{name}{The name of the model to create.}

\item{tags}{Additional metadata for the registered model (Optional).}

\item{description}{Description for the registered model (Optional).}

\item{client}{(Optional) An QCFlow client object returned from \link[qcflow]{qcflow_client}.
If specified, QCFlow will use the tracking server associated with the passed-in client. If
unspecified (the common case),
QCFlow will use the tracking server associated with the current tracking URI.}
}
\description{
Creates a new registered model in the model registry
}
