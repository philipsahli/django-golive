from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'golive-sandbox2'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'djangocelery_example_sandbox2'
ALLOWED_HOSTS = ['backend_golive-sandbox2', 'golive-sandbox2']
USE_X_FORWARDED_HOST = True

