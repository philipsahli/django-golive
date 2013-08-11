import os
from golive.utils import get_var
from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'golive-sandbox2'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'django_example_sandbox2'
DATABASES['default']['USER'] = 'django_example_sandbox2'
DATABASES['default']['PASSWORD'] = get_var('DB_PASSWORD')
