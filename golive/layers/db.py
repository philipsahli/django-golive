import datetime
from fabric.operations import run, prompt, os
from fabric.state import env
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
from golive.utils import info, error


class PostgresSetup(BaseTask, DjangoBaseTask, DebianPackageMixin):
    package_name = 'postgresql libpq-dev'
    ROLES = "DB_HOST"

    CMD_RESTART = "sudo /etc/init.d/postgresql restart"
    CMD_DB_CHECK = 'echo "\dt"|psql'
    DB_CHECK_EXPECT_STRING = "List of relations"
    PORT = 5432

    def init(self, update=True):
        DebianPackageMixin.init(self, update)

    def deploy(self):
        hosts = self._allowed_hosts()
        info("POSTGRES: configure pg_hba.conf")
        for host in hosts:
            self.append("/etc/postgresql/8.4/main/pg_hba.conf",
                               "host    all         all         %s/32          md5" % host)
        self.append("/etc/postgresql/8.4/main/postgresql.conf", "listen_addresses = '*'")
        info("RESTART postgres")
        self.execute(run, self.CMD_RESTART)

        allow = [(environment.hosts, config['DB_HOST'], self.PORT)]
        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
        iptables.set_rules(self.__class__.__name__)
        iptables.activate()

    def _allowed_hosts(self):
        return [utils.resolve_host(x) for x in environment.get_role('WEB_HOST').hosts]

    def backup(self):
        self.ts = config['TS']
        env.user = config['USER']

        self.backup_dir = "$HOME/tmp_%s" % self.ts
        config['BACKUP_DIR'] = self.backup_dir
        self.mkdir(self.backup_dir)

        self._backup()

    def restore(self):
        self._restore()

    def _backup(self):
        # create tempfile
        db_name = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])
        dumpfile = "db_%s-%s.dump" % (db_name, self.ts)

        # create dumpfile
        info("DB: Dump database to file %s" % os.path.join(self.backup_dir, dumpfile))
        self.execute_once(run, "pg_dump --create %s > %s/%s" % (db_name, self.backup_dir, dumpfile))

    def _restore(self):

        db_name = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])
        if prompt("Do you really want to drop the database '%s'? Y/N" % db_name) == "Y":
            self.execute_once(run, "dropdb %s" % db_name)
            info("DB: dropped db %s" % db_name)
        info("DB: db %s not dropped" % db_name)
        restore_file = config['BACKUP_DUMPFILE']
        output = self.execute_once(run, "psql -f %s postgres " % restore_file).values()[0]
        info("OUTPUT: \r\n%s" % output)

    def status(self):
        env.user = config['USER']
        output = self.execute_once(run, self.CMD_DB_CHECK).values()[0]
        if self.DB_CHECK_EXPECT_STRING in output:
            info("DB: is OK")
        else:
            error("DB: is NOK")
            error(output)
