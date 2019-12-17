#!/usr/bin/env bash
set -e

cd $(dirname "$0")

rm -f function.zip

# Setup virtualenv
virtualenv --python=python3.7 v-env
source v-env/bin/activate
pip install requests
deactivate

# Package our lambda code without extra file attributes
zip -X -r function.zip *

# Fix zip determinism
strip-nondeterminism --type zip function.zip
