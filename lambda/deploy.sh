#!/usr/bin/env bash
set -e

cd $(dirname "$0")

./package-lambda.sh

# Update lambda code for all functions prefixed by s3bi-
aws lambda list-functions \
  --query Functions[].FunctionName \
  --output json | \
  jq .[] -r | \
  grep "^s3bi-" |
  xargs -I {} \
    aws lambda update-function-code \
      --function-name {} \
      --zip-file fileb://function.zip \
      --output json
