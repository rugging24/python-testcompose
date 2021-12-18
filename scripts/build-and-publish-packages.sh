#!/bin/bash

set -xeu

SCRIPT_PATH=$(pwd)

pip install mkdocs-material mkdocs-git-revision-date-plugin \
    mkdocs-material mkdocs-material-extensions mkdocstrings \
    mkdocs-autorefs mkdocs markdown markupsafe twine wheel

# # python -c 'import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))'

python setup.py sdist bdist_wheel
twine check dist/*

cd testcompose
mkdocs build --config-file "${SCRIPT_PATH}"/mkdocs.yml

mkdocs gh-deploy --force --config-file "${SCRIPT_PATH}"/mkdocs.yml --remote-branch gh-pages

cd "${SCRIPT_PATH}"
twine upload dist/*
