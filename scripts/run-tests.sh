#!/bin/bash

set -eux

if [ "$#" -ne 1 ]; then
    echo "Test requires Python Version"
    exit 1
fi
VERSION="${1}"
# install tox
pip install --upgrade pip
pip install tox

# run tox
tox -e "py${VERSION/'.'/}"
