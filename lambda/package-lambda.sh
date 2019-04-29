#!/usr/bin/env bash
set -e

rm -f function.zip

# Package our lambda code without extra file attributes
zip -X function.zip *.py

# Fix zip determinism
strip-nondeterminism --type zip function.zip
