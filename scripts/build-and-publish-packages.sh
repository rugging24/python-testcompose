#!/bin/bash

set -xeu

pip install mkdocs-material mkdocs-git-revision-date-plugin \
    mkdocs-material mkdocs-material-extensions mkdocstrings[python-legacy]>=0.18 \
    mkdocs-autorefs mkdocs markdown markupsafe twine wheel coverage

python setup.py sdist bdist_wheel
twine check dist/*

python setup.py install
mkdocs build

twine upload dist/*

mkdocs gh-deploy --force
