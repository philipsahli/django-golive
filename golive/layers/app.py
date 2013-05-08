import hashlib
from fabric.context_managers import cd, prefix
from fabric.contrib.project import rsync_project, os
from fabric.decorators import runs_once
from fabric.operations import run
from fabric.state import env
from base import *
from golive.stacks.stack import config

import django


class PythonSetup(BaseTask, DebianPackageMixin):
    ROLES = "APP_HOST"
    package_name = 'python-virtualenv python-pip virtualenvwrapper'

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        self.execute(run, "test -d .virtualenvs/%s || virtualenv --no-site-packages .virtualenvs/%s" %
                          (env.project_name,  env.project_name))


class DjangoSetup(BaseTask, DjangoBaseTask):
    ROLES = "APP_HOST"
    supervisor_conf_template = "golive/supervisor_django.conf"
    supervisor_run_template = "golive/supervisor_django.run"

    def __init__(self):
        super(DjangoSetup, self).__init__()
        # TODO: create link from home-folder to the configfile
        self.supervisor_appname = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])

    def init(self):
        self.mkdir("/home/%s/code" % config['USER'])
        self.mkdir("/home/%s/log" % config['USER'])
        self.mkdir("/home/%s/static" % config['USER'])

    def deploy(self):
        env.remote_home = "/home/" + config['USER']
        env.user = config['USER']
        env.project_name = config['PROJECT_NAME']
        self._configure_startup()
        self._stop()
        self._sync()
        self._install_requirements()
        self._syncdb()
        self._collecstatic()
        self._start()

        #
        RULE = (environment.get_role('WEB_HOST').hosts, None, self._port())
        IPTablesSetup._open(*RULE)
        self._status()

    def _stop(self):
        self.execute(sudo, "supervisorctl stop %s" % self.supervisor_appname)

    def _status(self):
        self.execute(sudo, "supervisorctl status %s" % self.supervisor_appname)

    def _start(self):
        self.execute(sudo, "supervisorctl start %s" % self.supervisor_appname)

    def _collecstatic(self):

        self.manage("collectstatic --noinput --settings=%s" % self._settings_modulestring())

    def _settings_modulestring(self):
        if "1.5" in django.get_version():
            settings_modulestring = "%s.settings_%s" % (config['PROJECT_NAME'], config['ENV_ID'])
        else:
            settings_modulestring = "settings_%s" % (config['ENV_ID'])
        return settings_modulestring

    def _configure_startup(self):
        supervisor = SupervisorSetup()

        # supervisor config
        supervisor.set_context_data(PYTHON="/home/%s/.virtualenvs/%s/bin/python" % (
            config['USER'], config['PROJECT_NAME']),
            PROJECT_DIR="/home/%s/code/%s" % (config['USER'], config['PROJECT_NAME']),
            PROJECT=config['PROJECT_NAME'],
            ENVIRONMENT=config['ENV_ID'],
            USER=config['USER'],
            APPNAME=self.supervisor_appname,
            SETTINGS=self._settings_modulestring(),
            PORT=self._port()
        )

        supervisor.set_local_filename(self.__class__.supervisor_conf_template)
        supervisor.set_destination_filename("/etc/supervisor/conf.d/%s.conf" % self.supervisor_appname)

        supervisor.init()
        supervisor.deploy()

        # run wrapper script
        supervisor.set_local_filename(self.__class__.supervisor_run_template)
        supervisor.set_destination_filename("/home/%s/%s.run" % (config['USER'], self.supervisor_appname))
        supervisor.init()
        supervisor.deploy()
        supervisor.post_deploy()

    def _port(self):
        """
        Unique port creation for listener port.
        """
        base_int = 8
        h = hashlib.sha256("%s_%s" % (config['PROJECT_NAME'], config['ENV_ID']))
        return "%i%s" % (base_int, str(int(h.hexdigest(), base=16))[:3])

    def _sync(self):
        """
        Synchronize the project to the remote server(s).
        """
        env.remote_home = "/home/" + env.user
        self.execute(rsync_project, "%s/code/" % env.remote_home, os.getcwd(), ["*.pyc", "*.log", "**.git/*"], True)

    def _install_requirements(self):
        # needed for private repos, local keys get forwarded
        env.forward_agent = True
        env.user = config['USER']
        env.remote_home = "/home/" + config['USER']

        # from requirements.txt
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                self.execute(run, "pip install --download-cache=/var/cache/pip -r requirements.txt")

        # from class variable
        if hasattr(self.__class__, "python_packages"):
            for package in self.__class__.python_packages.split(" "):
                with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
                    with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                        self.execute(run, "pip install --download-cache=/var/cache/pip %s" % package)

    @runs_once
    def _syncdb(self):
        self._prepare_db()
        self.manage("syncdb --noinput --settings=%s" % self._settings_modulestring())
        # TODO: migratedb if south installed

    def _prepare_db(self):
        # get db node
        #import pdb; pdb.set_trace()
        db_host = config['DB_HOST']
        # make db name
        db_name = "%s_%s" % (django.conf.settings.DATABASES['default']['NAME'], config['ENV_ID'])
        #db_password = os.environ['GOLIVE_DB_PASSWORD']
        db_password = get_remote_envvar('GOLIVE_DB_PASSWORD', db_host)
        # create user (role)
        user = config['USER']
        with settings(warn_only=True):
            execute(sudo, ("su - postgres -c \"createuser -U postgres -l -S -d -R %s\"" % (user)),
                    hosts=[db_host])
        # set password
        sql = "ALTER USER %s WITH UNENCRYPTED PASSWORD '%s';" % (user, db_password)
        self.execute_once(run, ("echo \"%s\" | sudo su - postgres -c psql" % sql))
        with settings(warn_only=True):
            # create database
            execute(sudo, ("su - postgres -c \"createdb -U postgres -O %s -E UTF8 -T template0 %s\"" % (
                config['USER'],
                db_name)), hosts=[db_host])


def get_remote_envvar(var, host):
    return execute(run, "echo $%s" % var, host=host).get(host, None)


class DjangoSetupGunicorn(DjangoSetup):
    python_packages = "gunicorn"

    supervisor_conf_template = "golive/supervisor_djangogunicorn.conf"
    supervisor_run_template = "golive/supervisor_djangogunicorn.run"
