#!/usr/bin/env bash

if grep -n 'com.databricks.qcflow.api.QCFlowTrackingMessage' "$@"; then
  echo 'Remove com.databricks.qcflow.api.QCFlowTrackingMessage'
  exit 1
fi
