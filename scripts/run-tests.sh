#!/bin/bash

set -eux

# install tox
pip install --upgrade pip
pip install tox

# run tox
tox
