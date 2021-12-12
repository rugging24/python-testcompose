#!/bin/bash

set -xeu


pip install mkdocs-material mkdocs-git-revision-date-plugin \
    mkdocs-material mkdocs-material-extensions mkdocstrings
    mkdocs-autorefs mkdocs markdown markupsafe twine wheel

python setup.py sdist bdist_wheel
twine check dist/*
mkdocs build

twine upload dist/*
mkdocs gh-deploy --force
