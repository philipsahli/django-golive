import os
from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'golive-sandbox1'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'djangocelery_example_sandbox'
DATABASES['default']['USER'] = 'djangocelery_example_sandbox'
#DATABASES['default']['PASSWORD'] = os.environ['GOLIVE_DB_PASSWORD']
DATABASES['default']['PASSWORD'] = "asdf"
ALLOWED_HOSTS = ['backend_golive-sandbox1', 'golive-sandbox1']
USE_X_FORWARDED_HOST = True
BROKER_URL = os.environ['GOLIVE_BROKER_URL']
