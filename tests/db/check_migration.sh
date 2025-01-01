#!/bin/bash
set -ex

cd tests/db

# Install the lastest version of qcflow from PyPI
pip install qcflow
python check_migration.py pre-migration
# Install qcflow from the repository
pip install -e ../..
qcflow db upgrade $QCFLOW_TRACKING_URI
python check_migration.py post-migration
