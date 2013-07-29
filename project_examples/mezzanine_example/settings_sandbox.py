from settings import *
# STATIC_ROOT should be monkey-patched
STATIC_ROOT = "/home/mezzanine_example_sandbox/static"

DATABASES['default']['HOST'] = 'golive-sandbox3'
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'mezzanine_example_sandbox'
DATABASES['default']['USER'] = 'mezzanine_example_sandbox'
DATABASES['default']['PASSWORD'] = os.environ['GOLIVE_DB_PASSWORD']
