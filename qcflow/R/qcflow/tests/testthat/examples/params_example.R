library(qcflow)

# define parameters
my_int <- qcflow_param("my_int", 1, "integer")
my_num <- qcflow_param("my_num", 1.0, "numeric")
my_str <- qcflow_param("my_str", "a", "string")

# log parameters
qcflow_log_param("param_int", my_int)
qcflow_log_param("param_num", my_num)
qcflow_log_param("param_str", my_str)
