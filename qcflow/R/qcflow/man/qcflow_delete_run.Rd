% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/tracking-runs.R
\name{qcflow_delete_run}
\alias{qcflow_delete_run}
\title{Delete a Run}
\usage{
qcflow_delete_run(run_id, client = NULL)
}
\arguments{
\item{run_id}{Run ID.}

\item{client}{(Optional) An QCFlow client object returned from \link[qcflow]{qcflow_client}.
If specified, QCFlow will use the tracking server associated with the passed-in client. If
unspecified (the common case),
QCFlow will use the tracking server associated with the current tracking URI.}
}
\description{
Deletes the run with the specified ID.
}
