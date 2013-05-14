#!/bin/bash

# simple django example
cd django_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox

# django with gunicorn example
cd ../djangogunicorn_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox

# mezzanine
cd ../mezzanine_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox

# django with celery
cd ../djangocelery_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox
