#!/usr/bin/env bash
# exit on error
set -o errexit

poetry install

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py importexercises
python manage.py importlanguages
python manage.py importwordtypes
python manage.py makesuperuser
