#!/usr/bin/env bash
# Run this pre-commit to perform very basic linting
# If black fails, run format.sh
# If pylint or mypy fails, fix your code
docker build -f Dockerfile.test -t s3bi-test . && \
  docker run --rm -v $(pwd):/app:ro -it s3bi-test /bin/bash -c \
    "black --target-version py37 --check *.py && pylint *.py && mypy *.py && echo ALL GOOD"
