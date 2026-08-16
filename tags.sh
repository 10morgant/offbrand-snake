#!/bin/bash

cd collector

# fetch versions and metadata for the package names fetched above
uv run process https://pypi.org --downloaders 50 --skip-existing