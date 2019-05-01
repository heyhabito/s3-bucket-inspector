#!/usr/bin/env bash
# This is to be run locally pre-commit
docker build -f Dockerfile.test -t s3bi-test . && \
  docker run --rm -v $(pwd):/app -it --user root s3bi-test /bin/bash -c \
    "black --target-version py37 *.py tests/*.py"
