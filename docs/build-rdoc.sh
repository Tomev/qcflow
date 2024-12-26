#!/usr/bin/env bash

set -ex

pushd ../qcflow/R/qcflow

image_name="qcflow-r-dev"

# Workaround for this issue:
# https://discuss.circleci.com/t/increased-rate-of-errors-when-pulling-docker-images-on-machine-executor/42094
n=0
until [ "$n" -ge 3 ]
do
  docker build -f Dockerfile.dev -t $image_name . --platform linux/amd64 && break
  n=$((n+1))
  sleep 5
done

docker run \
  --rm \
  -v $(pwd):/qcflow/qcflow/R/qcflow \
  -v $(pwd)/../../../docs/source:/qcflow/docs/source \
  $image_name \
  Rscript -e 'source(".build-doc.R", echo = TRUE)'

popd
