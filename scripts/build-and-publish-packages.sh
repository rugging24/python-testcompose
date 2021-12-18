#!/bin/bash

set -xeu

SCRIPT_PATH=$(pwd)
export PYTHONPATH="${SCRIPT_PATH}"

pip install mkdocs-material mkdocs-git-revision-date-plugin \
    mkdocs-material mkdocs-material-extensions mkdocstrings \
    mkdocs-autorefs mkdocs markdown markupsafe twine wheel

# # python -c 'import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))'

python setup.py sdist bdist_wheel
twine check dist/*

python setup.py install
mkdocs build

twine upload dist/*

mkdocs gh-deploy --force
