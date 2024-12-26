#!/usr/bin/env bash

if grep -n 'com.databricks.qcflow.api.MlflowTrackingMessage' "$@"; then
  echo 'Remove com.databricks.qcflow.api.MlflowTrackingMessage'
  exit 1
fi
