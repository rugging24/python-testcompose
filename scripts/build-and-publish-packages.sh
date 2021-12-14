#!/bin/bash

set -xeu


pip install mkdocs-material mkdocs-git-revision-date-plugin \
    mkdocs-material mkdocs-material-extensions mkdocstrings \
    mkdocs-autorefs mkdocs markdown markupsafe twine wheel

python -c 'import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))'

python setup.py sdist bdist_wheel
twine check dist/*
mkdocs build

twine upload dist/*
mkdocs gh-deploy --force
