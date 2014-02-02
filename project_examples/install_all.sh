#!/bin/bash

# simple django example
#######################
cd django_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox
python manage.py status sandbox

# sandbox2
cd ../django_example ; python manage.py init sandbox2
python manage.py set_var sandbox2 DB_PASSWORD 'asdf'
python manage.py deploy sandbox2
python manage.py status sandbox2


# django with gunicorn example
##############################
cd ../djangogunicorn_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox
python manage.py status sandbox

# mezzanine
###########
cd ../mezzanine_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py deploy sandbox
python manage.py status sandbox

# django with celery
####################
cd ../djangocelery_example ; python manage.py init sandbox
python manage.py set_var sandbox DB_PASSWORD 'asdf'
python manage.py set_var sandbox BROKER_USER 'worker1'
python manage.py set_var sandbox BROKER_PASSWORD 'worker1'
python manage.py set_var sandbox BROKER_URL 'amqp://worker1:worker1@golive-sandbox1:5672/'
python manage.py deploy sandbox
python manage.py status sandbox
# TODO: create superuser for admin section (python manage.py createsuperuser)

