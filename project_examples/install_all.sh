#!/bin/bash

# simple django example
#######################
cd django_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox

# django with gunicorn example
##############################
cd ../djangogunicorn_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox

# mezzanine
###########
cd ../mezzanine_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox

# django with celery
####################
cd ../djangocelery_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py set_var sandbox BROKER_USER 'worker1'
python manage.py set_var sandbox BROKER_PASSWORD 'worker1'
python manage.py set_var sandbox BROKER_URL 'amqp://worker1:worker1@golive-sandbox1:5672/'
python manage.py deploy sandbox
# TODO: create superuser for admin section (python manage.py createsuperuser)

