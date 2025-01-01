# Install QCFlow for R
files <- dir(".", full.names = TRUE)
package <- files[grepl("qcflow_.+\\.tar\\.gz$", files)]
install.packages(package)
