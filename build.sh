#!/usr/bin/env bash
# exit on error
set -o errexit

python -m pip install -r requirements.txt

source venv/bin/activate

cd src/

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py makesuperuser
python manage.py importlanguages --import_images
python manage.py importwordtypes
python manage.py importexercises
