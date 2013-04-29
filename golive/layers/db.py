from django.conf import settings
import datetime
from fabric.operations import run
from golive.layers.base import DjangoBaseTask, DebianPackageMixin, BaseTask
from golive.stacks.stack import config


#class DbEngineFactory(object):
#    @staticmethod
#    def setup(impl=None):
#        engine = settings.DATABASES['defaults']['ENGINE']
#        #if "sqlite3" in engine:
#        #    return SqliteSetup()
#        if "postgres" in engine:
#            return PostgresSetup()
#        raise Exception("Configuration problem")


class PostgresSetup(BaseTask, DjangoBaseTask, DebianPackageMixin):
    package_name = 'postgresql'
    ROLES = "DB_HOST"

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        self.append("/etc/postgresql/8.4/main/pg_hba.conf",
                                  "host    all         all         192.168.0.0/16          trust")
        self.append("/etc/postgresql/8.4/main/pg_hba.conf",
                    "host    all         all         10.211.0.0/16          trust")
        #self.append("/etc/postgresql/8.4/main/postgresql.conf",
        #                          "listen_addresses = '%s'" % config['DB_HOST'])
        self.append("/etc/postgresql/8.4/main/postgresql.conf",
                    "listen_addresses = '*'")
        # TODO: add security
        # TODO: only restart when needed
        self.execute(run, "sudo /etc/init.d/postgresql restart")

    def _backup(self):
        db_name = "%s" % config['PROJECT_NAME']
        # create tempfile
        now = datetime.datetime.now()
        #self.execute_once("dumpfile=`mktemp` && pg_dump %s > $dumpfile" % db_name)
        dumpfile = "%s_%s" % (db_name, now.strftime("%Y%m%d%H%M%S"))
        dumpdir = "$HOME"
        self.execute_once("pg_dump %s > %s/%s" % (db_name, dumpdir, dumpfile))

    def _restore(self):
        pass


