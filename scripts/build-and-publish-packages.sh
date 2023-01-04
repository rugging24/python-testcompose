#!/bin/bash

set -xeu

twine check dist/*

mkdocs build

poetry publish -u __token__ -p $TWINE_PASSWORD

mkdocs gh-deploy --force
