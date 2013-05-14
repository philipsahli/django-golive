from settings import *

DEBUG = True

DATABASES['default']['HOST'] = 'xcore3'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'

print DATABASES
