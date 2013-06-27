import datetime
from fabric.operations import run
from golive import utils
from golive.layers.app import DjangoBaseTask
from golive.layers.base import DebianPackageMixin, BaseTask, IPTablesSetup
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

    def init(self, update=True):
        DebianPackageMixin.init(self, update)

    def deploy(self):
        hosts = self._allowed_hosts()
        for host in hosts:
            self.append("/etc/postgresql/8.4/main/pg_hba.conf",
                               "host    all         all         %s/32          md5" % host)
        self.append("/etc/postgresql/8.4/main/postgresql.conf", "listen_addresses = '*'")
        self.execute(run, "sudo /etc/init.d/postgresql restart")

        allow = [(environment.hosts, config['DB_HOST'], 5432)]
        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
        iptables.set_rules(self.__class__.__name__)
        iptables.activate()

    def _allowed_hosts(self):
        return [utils.resolve_host(x) for x in environment.get_role('WEB_HOST').hosts]

    def _backup(self):
        db_name = "%s" % config['PROJECT_NAME']
        # create tempfile
        now = datetime.datetime.now()
        dumpfile = "%s_%s" % (db_name, now.strftime("%Y%m%d%H%M%S"))
        dumpdir = "$HOME"
        self.execute_once("pg_dump %s > %s/%s" % (db_name, dumpdir, dumpfile))

    def _restore(self):
        pass


