#!/usr/bin/env bash
set -e

cd $(dirname "$0")

rm -f function.zip

# Install dependencies
pip install --system requests  -t ./

# Create deployment package
zip -X -r function.zip *

# Fix zip determinism
strip-nondeterminism --type zip function.zip
