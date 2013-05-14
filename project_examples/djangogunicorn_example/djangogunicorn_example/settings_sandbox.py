import os
from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'golive-sandbox1'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'djangogunicorn_example_sandbox'
DATABASES['default']['PASSWORD'] = os.environ['GOLIVE_DB_PASSWORD']
ALLOWED_HOSTS = ['backend_golive-sandbox1', 'golive-sandbox1']
USE_X_FORWARDED_HOST = True
