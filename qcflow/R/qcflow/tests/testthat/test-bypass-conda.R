context("Bypass conda")


test_that("QCFlow finds QCFLOW_PYTHON_BIN environment variable", {
  orig_global <- qcflow:::.globals$python_bin
  rm("python_bin", envir = qcflow:::.globals)
  orig <- Sys.getenv("QCFLOW_PYTHON_BIN")
  expected_path <- "/test/python"
  Sys.setenv(QCFLOW_PYTHON_BIN = expected_path)
  python_bin <- qcflow:::get_python_bin()
  expect_equal(python_bin, expected_path)
  # Clean up
  Sys.setenv(QCFLOW_PYTHON_BIN = orig)
  assign("python_bin", orig_global, envir = qcflow:::.globals)
})

test_that("QCFlow finds QCFLOW_BIN environment variable", {
  orig_global <- qcflow:::.globals$python_bin
  rm("python_bin", envir = qcflow:::.globals)
  orig_env <- Sys.getenv("QCFLOW_BIN")
  expected_path <- "/test/qcflow"
  Sys.setenv(QCFLOW_BIN = expected_path)
  qcflow_bin <- qcflow:::python_qcflow_bin()
  expect_equal(qcflow_bin, expected_path)
  # Clean up
  Sys.setenv(QCFLOW_BIN = orig_env)
  assign("python_bin", orig_global, envir = qcflow:::.globals)
})
