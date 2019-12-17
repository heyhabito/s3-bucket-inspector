#!/usr/bin/env bash
set -e

cd $(dirname "$0")

rm -f function.zip

# Setup virtualenv
virtualenv --python=python3.7 v-env
source v-env/bin/activate
pip install requests
deactivate
OLDPWD=$(pwd)

# Package the libraries
cd v-env/lib/python3.7/site-packages
zip -r9 ${OLDPWD}/function.zip .

# Package our lambda code without extra file attributes
cd ${OLDPWD}
zip -X function.zip *.py

# Fix zip determinism
strip-nondeterminism --type zip function.zip
