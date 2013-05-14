import os
from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'golive-sandbox1'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'django_example_sandbox'
DATABASES['default']['USER'] = 'django_example_sandbox'
DATABASES['default']['PASSWORD'] = os.environ['GOLIVE_DB_PASSWORD']
