#!/usr/bin/env bash

set -ex

qcflow_envs=$(
  conda env list |                 # list (env name, env path) pairs
  cut -d' ' -f1 |                  # extract env names
  grep "^qcflow-[a-z0-9]\{40\}\$"  # filter envs created by qcflow
) || true

if [ ! -z "$qcflow_envs" ]; then
  for env in $qcflow_envs
  do
    conda remove --all --yes --name $env
  done
fi

conda clean --all --yes
conda env list

set +ex
