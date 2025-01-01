unlink("man", recursive = TRUE)
roxygen2::roxygenise()
# remove qcflow-package doc temporarily because no rst doc should be generated for it.
file.remove("man/qcflow-package.Rd")
source("document.R", echo = TRUE)
# roxygenize again to make sure the previously removed qcflow-packge doc is available as R helpfile
roxygen2::roxygenise()
