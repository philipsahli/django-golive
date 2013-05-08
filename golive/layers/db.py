from django.conf import settings
import datetime
import socket
from fabric.operations import run
from golive.layers.base import DjangoBaseTask, DebianPackageMixin, BaseTask, IPTablesSetup
from golive.stacks.stack import config, environment


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
    package_name = 'postgresql libpq-dev'
    ROLES = "DB_HOST"

    RULE = (environment.hosts, config['DB_HOST'], 5432)

    def init(self, update=True):
        DebianPackageMixin.init(self, update)

    def deploy(self):
        hosts = self._allowed_hosts()
        for host in hosts:
            self.append("/etc/postgresql/8.4/main/pg_hba.conf",
                               "host    all         all         %s/32          md5" % host)
        self.append("/etc/postgresql/8.4/main/postgresql.conf", "listen_addresses = '*'")
        self.execute(run, "sudo /etc/init.d/postgresql restart")

        IPTablesSetup._open(*self.__class__.RULE)

    def _allowed_hosts(self):
        return [socket.gethostbyname(x) for x in environment.get_role('WEB_HOST').hosts]

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


