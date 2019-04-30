#!/usr/bin/env bash
set -e

cd $(dirname "$0")

./package-lambda.sh

# Update run code. Will only succeed on main account
aws lambda update-function-code \
  --function-name s3bi-run \
  --zip-file fileb://function.zip \
  --output json || true

# Update config code (required for all accounts).
aws lambda update-function-code \
  --function-name s3bi-config \
  --zip-file fileb://function.zip \
  --output json
