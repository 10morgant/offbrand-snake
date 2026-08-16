#!/bin/bash

cd collector

# fetch list of package names from the PyPI simple index
# uv run fetch https://pypi.org

# add list of names from file to database
uv run names https://pypi.org