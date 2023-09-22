#!/usr/bin/env bash
# exit on error
set -o errexit

poetry install

python linguista/manage.py collectstatic --no-input
python linguista/manage.py migrate