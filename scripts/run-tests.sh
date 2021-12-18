#!/bin/bash

set -eux

if [ "$#" -ne 1 ]; then
    echo "Test requires Python Version"
    exit 2
fi
VERSION="${1}"
# install tox
pip install tox

# run tox
# tox -e "py${VERSION/'.'/}"
echo "just running a test"

# # coverage
# export SOURCE_FILES="testcompose tests"

# coverage report --show-missing --skip-covered --fail-under=100
