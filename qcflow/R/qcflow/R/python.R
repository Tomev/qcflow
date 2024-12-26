# Computes path to Python executable from the QCFLOW_PYTHON_BIN environment variable.
get_python_bin <- function() {
  in_env <- Sys.getenv("QCFLOW_PYTHON_BIN")
  if (in_env != "") {
    return(in_env)
  }
  # QCFLOW_PYTHON_EXECUTABLE is an environment variable that's defined in a Databricks notebook
  # environment.
  qcflow_python_executable <- Sys.getenv("QCFLOW_PYTHON_EXECUTABLE")
  if (qcflow_python_executable != "") {
    stdout <- system(paste(qcflow_python_executable, '-c "import sys; print(sys.executable)"'),
                     intern = TRUE,
                     ignore.stderr = TRUE)
    return(paste(stdout, collapse = ""))
  }
  python_bin <- Sys.which("python")
  if (python_bin != "") {
    return(python_bin)
  }
  stop(paste("QCFlow not configured, please run `pip install qcflow` or ",
             "set QCFLOW_PYTHON_BIN and QCFLOW_BIN environment variables.", sep = ""))
}

# Returns path to Python executable
python_bin <- function() {
  if (is.null(.globals$python_bin)) {
    python <- get_python_bin()
    .globals$python_bin <- path.expand(python)
  }

  .globals$python_bin
}

# Returns path to QCFlow CLI, assumed to be in the same bin/ directory as the
# Python executable
python_qcflow_bin <- function() {
  in_env <- Sys.getenv("QCFLOW_BIN")
  if (in_env != "") {
    return(in_env)
  }
  qcflow_bin <- Sys.which("qcflow")
  if (qcflow_bin != "") {
    return(qcflow_bin)
  }
  python_bin_dir <- dirname(python_bin())
  if (.Platform$OS.type == "windows") {
    file.path(python_bin_dir, "Scripts", "qcflow")
  } else {
    file.path(python_bin_dir, "qcflow")
  }
}
