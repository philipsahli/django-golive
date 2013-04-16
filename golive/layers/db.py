from fabric.operations import run
from fabric.state import env
from django.conf import settings
from fabric.tasks import execute
from golive.layers.base import DjangoBaseTask, DebianPackageMixin


class DbEngineFactory(object):
    @staticmethod
    def setup(impl=None):
        print "SETUP"
        engine = settings.DATABASES['defaults']['ENGINE']
        #if "sqlite3" in engine:
        #    return SqliteSetup()
        if "postgres" in engine:
            return PostgresSetup()
        raise Exception("Configuration problem")


#class SqliteSetup(DjangoBaseTask, DebianPackageMixin):
#    role = 'DB_HOST'
#
#    def update(self):
#        self.execute_role_only(run, 'date')


class PostgresSetup(DjangoBaseTask, DebianPackageMixin):
    package_name = 'postgresql'
    ROLES = "DB_HOST"

    def create(self):
        self.update()

    def update(self):
        env.remote_home = self.run("echo $HOME")
        execute(run, 'date', roles='DB_HOST')
        self.manage("syncdb")
        if "south" in settings.INSTALLED_APPS:
            self.manage("migrate")

