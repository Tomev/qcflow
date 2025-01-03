#!/bin/bash
set -ex

# Install qcflow (assuming the repository root is mounted to the working directory)
if [ "$INSTALL_QCFLOW_FROM_REPO" = "true" ]; then
  pip install --no-deps -e .
fi

# For Microsoft SQL server, wait until the database is up and running
if [[ $QCFLOW_TRACKING_URI == mssql* ]]; then
  ./tests/db/init-mssql-db.sh
fi

# Execute the command
exec "$@"
