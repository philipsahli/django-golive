from django.contrib.sites.models import Site
from django.conf import settings
from fabric.contrib.files import sed, exists
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
from golive.utils import info, error, debug


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
            paths = [
                '/etc/postgresql/8.4/main/pg_hba.conf', 
                '/etc/postgresql/9.1/main/pg_hba.conf'
                ]
            pg_hba = self.first_file(paths, host)
            paths = [
                '/etc/postgresql/8.4/main/postgresql.conf', 
                '/etc/postgresql/9.1/main/postgresql.conf'
                ]
            postgresql = self.first_file(paths, host)
            self.append(pg_hba, 
                               "host    all         all         %s/32          md5" % host)
        self.append(postgresql, "listen_addresses = '*'")
        info("POSTGRES: restart")
        self.execute(run, self.CMD_RESTART)

        allow = [(environment.hosts, config['DB_HOST'], self.PORT)]
        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
        iptables.set_rules(self.__class__.__name__)
        iptables.activate()

    def _allowed_hosts(self):
        return [utils.resolve_host(x) for x in environment.get_role('APP_HOST').hosts]

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

    CONFIRM_YES = "yYjJ"
    CONFIRM_NO = "nN"

    def _drop_db(self, db_name):
        if prompt("Do you really want to drop the database '%s'? %s/%s" %
                (db_name, self.CONFIRM_YES, self.CONFIRM_NO)) in self.CONFIRM_YES:
            self.execute_once(run, "dropdb %s" % db_name)
            info("DB: dropped database %s" % db_name)
        else:
            info("DB: database %s not dropped" % db_name)

    def _cleanup(self):
        info("DB: start cleanup database")
        servername = config['SERVERNAME']
        SQLs = ["UPDATE \"django_site\" SET \"domain\" = E'%s', \"name\" = E'%s' "
                "WHERE \"django_site\".\"id\" = 1" % (servername, servername),
                "DELETE FROM django_session",
        ]
        # builtin
        for sql in SQLs:
            self._execute_dbshell(sql)

        # sql's from setting project settings
        for sql in settings.GOLIVE_CLEANUP_RESTORE:
            self._execute_dbshell(sql)
        info("DB: end cleanup database")

    def _restore(self):
        db_name = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])
        restore_file = config['BACKUP_DUMPFILE']

        # different source database
        source_env = config.get('SOURCE_ENV', None)
        db_name_source = "%s_%s" % (config['PROJECT_NAME'], source_env)
        source_differs = (db_name != db_name_source)

        # drop db if wished, could be normal behaviour, but let this decide the operator
        self._drop_db(db_name)

        # if restore from different environment, change database-/role name in dumpfile on
        # the server before restore
        args = (restore_file, "%s" % db_name_source, "%s" % db_name)
        debug("DB: Change string in dumpfile on server: %s to %s " % (args[1], args[2]))
        if config['ENV_ID'] == "local":
            self.execute_once(sed, *args)
        self.execute_once(sed, *args)

        # start restore
        output = self.execute_once(run, "psql -f %s postgres " % restore_file).values()[0]
        
        info("OUTPUT: \r\n%s" % output)

        # cleanup
        if source_differs:
            self._cleanup()

    def _execute_dbshell(self, sql):
        debug("DB: execute cleanup sql: %s" % sql)
        output = self.execute_once(run, "echo \"%s\" | psql " % sql).values()[0]
        info("OUTPUT: \r\n%s" % output)

    def status(self):
        env.user = config['USER']
        output = self.execute_once(run, self.CMD_DB_CHECK).values()[0]
        if self.DB_CHECK_EXPECT_STRING in output:
            info("DB: is OK")
        else:
            error("DB: is NOK")
            error(output)
