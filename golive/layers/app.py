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


class DataExporter(BaseTask):
    pass


class DjangoSetup(BaseTask, DjangoBaseTask):
    ROLES = "APP_HOST"
    SUPERVISOR_TEMPLATE = "golive/supervisor_django.conf"

    def __init__(self):
        super(DjangoSetup, self).__init__()
        # TODO: create link from home-folder to the configfile
        self.supervisor_appname = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])

    def init(self):
        self.mkdir("/home/%s/code" % config['USER'])
        self.mkdir("/home/%s/log" % config['USER'])
        self.mkdir("/home/%s/static" % config['USER'])
        self.update()

    def update(self):
        env.remote_home = "/home/" + config['USER']
        env.project_name = config['PROJECT_NAME']
        self._configure_startup()
        #self._stop()
        self._sync()
        self._install_requirements()
        self._syncdb()
        self._collecstatic()
        self._start()
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
        supervisor.set_context_data(PYTHON="/home/%s/.virtualenvs/%s/bin/python" % (
            config['USER'], config['PROJECT_NAME']),
            PROJECT_DIR="/home/%s/code/%s" % (config['USER'], config['PROJECT_NAME']),
            PROJECT=config['PROJECT_NAME'],
            ENVIRONMENT=config['ENV_ID'],
            USER=config['USER'],
            APPNAME=self.supervisor_appname,
            SETTINGS=self._settings_modulestring()
        )

        supervisor.set_local_filename(self.__class__.SUPERVISOR_TEMPLATE)
        supervisor.set_destination_filename("/etc/supervisor/conf.d/%s.conf" % self.supervisor_appname)
        supervisor.init()

    def _sync(self):
        env.remote_home = "/home/" + env.user
        self.execute(rsync_project, "%s/code/" % env.remote_home, os.getcwd(), ["*.pyc", "*.log", "**.git/*"], True)

    def _install_requirements(self):
        env.remote_home = "/home/" + config['USER']
        # needed for private repos, local keys get forwarded
        env.forward_agent = True
        env.user = config['USER']
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                self.execute(run, "pip install --download-cache=/var/cache/pip -r requirements.txt")
                #self.execute(run, "pip install -r requirements.txt")

    @runs_once
    def _syncdb(self):
        self._prepare_db()
        #self.manage("syncdb --noinput --settings=%s.settings_%s" % (config['PROJECT_NAME'], config['ENV_ID']))
        self.manage("syncdb --noinput --settings=%s" % self._settings_modulestring())
        #self.manage("migrate --settings=settings_%s" % (config['ENV_ID']))

    def _prepare_db(self):
        with settings(warn_only=True):
            # get db node
            db_host = config['DB_HOST']
            # make db name
            #db_name = "%s" % (config['PROJECT_NAME'])
            db_name = "%s_%s" % (django.conf.settings.DATABASES['default']['NAME'], config['ENV_ID'])
            # create user (role)
            self.execute_once(run, ("createuser -h %s -U postgres -l -S -d -R %s" % (db_host, config['USER'])))
            # create database
            self.execute_once(run, ("createdb -U postgres -h %s -O %s -E UTF8 -T template0 %s" % (
                db_host,
                config['USER'],
                db_name)))


