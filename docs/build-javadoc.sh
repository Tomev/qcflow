#!/usr/bin/env bash

# Builds the QCFlow Javadoc and places it into build/html/java_api/

set -ex
pushd ../qcflow/java/client/
mvn clean javadoc:javadoc -q
popd
rm -rf build/html/java_api/
mkdir -p build/html/java_api/
cp -r ../qcflow/java/client/target/site/apidocs/* build/html/java_api/
echo "Copied JavaDoc into docs/build/html/java_api/"
