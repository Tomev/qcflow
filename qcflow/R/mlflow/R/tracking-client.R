
new_qcflow_client <- function(tracking_uri) {
  UseMethod("new_qcflow_client")
}

new_qcflow_uri <- function(raw_uri) {
  # Special case 'databricks'
  if (identical(raw_uri, "databricks")) {
    raw_uri <- paste0("databricks", "://")
  }

  if (!grepl("://", raw_uri)) {
    raw_uri <- paste0("file://", raw_uri)
  }
  parts <- strsplit(raw_uri, "://")[[1]]
  structure(
    list(scheme = parts[1], path = parts[2]),
    class = c(paste("qcflow_", parts[1], sep = ""), "qcflow_uri")
  )
}

new_qcflow_client_impl <- function(get_host_creds, get_cli_env = list, class = character()) {
  structure(
    list(get_host_creds = get_host_creds,
         get_cli_env = get_cli_env
    ),
    class = c(class, "qcflow_client")
  )
}

new_qcflow_host_creds <- function(host = NA, username = NA, password = NA, token = NA,
                                   insecure = "False") {
  insecure_arg <- if (is.null(insecure) || is.na(insecure)) {
    "False"
  } else {
    list(true = "True", false = "False")[[tolower(insecure)]]
  }
  structure(
    list(host = host, username = username, password = password, token = token,
         insecure = insecure_arg),
    class = "qcflow_host_creds"
  )
}

#' @export
print.qcflow_host_creds <- function(x, ...) {
  qcflow_host_creds <- x
  args <- list(
    host = if (is.na(qcflow_host_creds$host)) {
      ""
    } else {
      paste ("host = ", qcflow_host_creds$host, sep = "")
    },
    username = if (is.na(qcflow_host_creds$username)) {
      ""
    } else {
      paste ("username = ", qcflow_host_creds$username, sep = "")
    },
    password = if (is.na(qcflow_host_creds$password)) {
      ""
    } else {
      "password = *****"
    },
    token = if (is.na(qcflow_host_creds$token)) {
      ""
    } else {
      "token = *****"
    },
    insecure = paste("insecure = ", as.character(qcflow_host_creds$insecure),
                     sep = ""),
    sep = ", "
  )
  cat("qcflow_host_creds( ")
  do.call(cat, args[args != ""])
  cat(")\n")
}

new_qcflow_client.qcflow_file <- function(tracking_uri) {
  path <- tracking_uri$path
  server_url <- if (!is.null(qcflow_local_server(path)$server_url)) {
    qcflow_local_server(path)$server_url
  } else {
    local_server <- qcflow_server(file_store = path, port = qcflow_connect_port())
    qcflow_register_local_server(tracking_uri = path, local_server = local_server)
    local_server$server_url
  }
  new_qcflow_client_impl(get_host_creds = function () {
    new_qcflow_host_creds(host = server_url)
  }, class = "qcflow_file_client")
}

new_qcflow_client.default <- function(tracking_uri) {
  stop(paste("Unsupported scheme: '", tracking_uri$scheme, "'", sep = ""))
}

get_env_var <- function(x) {
  new_name <- paste("QCFLOW_TRACKING_", x, sep = "")
  res <- Sys.getenv(new_name, NA)
  if (is.na(res)) {
    old_name <- paste("QCFLOW_", x, sep = "")
    res <- Sys.getenv(old_name, NA)
    if (!is.na(res)) {
      warning(paste("'", old_name, "' is deprecated. Please use '", new_name, "' instead."),
                    sepc = "" )
    }
  }
  res
}

basic_http_client <- function(tracking_uri) {
  host <- paste(tracking_uri$scheme, tracking_uri$path, sep = "://")
  get_host_creds <- function () {
    new_qcflow_host_creds(
      host = host,
      username = get_env_var("USERNAME"),
      password = get_env_var("PASSWORD"),
      token = get_env_var("TOKEN"),
      insecure = get_env_var("INSECURE")
    )
  }
  cli_env <- function() {
    creds <- get_host_creds()
    res <- list(
      QCFLOW_TRACKING_USERNAME = creds$username,
      QCFLOW_TRACKING_PASSWORD = creds$password,
      QCFLOW_TRACKING_TOKEN = creds$token,
      QCFLOW_TRACKING_INSECURE = creds$insecure
    )
    res[!is.na(res)]
  }
  new_qcflow_client_impl(get_host_creds, cli_env, class = "qcflow_http_client")
}

new_qcflow_client.qcflow_http <- function(tracking_uri) {
  basic_http_client(tracking_uri)
}

new_qcflow_client.qcflow_https <- function(tracking_uri) {
  basic_http_client(tracking_uri)
}

#' Initialize an QCFlow Client
#'
#' Initializes and returns an QCFlow client that communicates with the tracking server or store
#' at the specified URI.
#'
#' @param tracking_uri The tracking URI. If not provided, defaults to the service
#'  set by `qcflow_set_tracking_uri()`.
#' @export
qcflow_client <- function(tracking_uri = NULL) {
  tracking_uri <- new_qcflow_uri(tracking_uri %||% qcflow_get_tracking_uri())
  client <- new_qcflow_client(tracking_uri)
  if (inherits(client, "qcflow_file_client")) qcflow_validate_server(client)
  client
}
