import os
from golive.utils import get_var
from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'golive-sandbox1'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'django_example_sandbox'
DATABASES['default']['USER'] = 'django_example_sandbox'
DATABASES['default']['PASSWORD'] = get_var('DB_PASSWORD')

ALLOWED_HOSTS = ["backend_golive-sandbox1"]
print ALLOWED_HOSTS
USE_X_FORWARDED_HOST = True
