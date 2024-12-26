library(qcflow)

# read parameters
column <- qcflow_log_param("column", 1)

# log total rows
qcflow_log_metric("rows", nrow(iris))

# train model
model <- lm(Sepal.Width ~ iris[[column]], iris)

# log models intercept
qcflow_log_metric("intercept", model$coefficients[["(Intercept)"]])
