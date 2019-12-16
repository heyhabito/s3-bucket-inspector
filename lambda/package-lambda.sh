#!/usr/bin/env bash
set -e

cd $(dirname "$0")

rm -f function.zip

# Package our lambda code without extra file attributes
zip -X -r function.zip *

# Fix zip determinism
strip-nondeterminism --type zip function.zip
