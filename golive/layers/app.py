import hashlib

from fabric.context_managers import cd, prefix
from fabric.contrib.project import rsync_project, os
from fabric.decorators import runs_once
from fabric.operations import run
from fabric.state import env
import django
from django.core.exceptions import ImproperlyConfigured

from base import *
from golive import registry
from golive.addons.newrelic import NewRelicPythonAddon
from golive.stacks.stack import config, environment
from golive.utils import get_remote_envvar


class PythonSetup(BaseTask, DebianPackageMixin):
    ROLES = "APP_HOST"
    package_name = 'python-virtualenv python-pip virtualenvwrapper libxml2-dev libxslt-dev'

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        env.user = config['USER']
        info("PYTHON: create virtualenv")
        self.execute(run, "test -d .virtualenvs/%s || virtualenv --no-site-packages .virtualenvs/%s" %
                          (env.project_name,  env.project_name))


class DjangoBaseTask():
    def manage(self, command):
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                debug("DJANGO: start management command %s" % command)
                return self.run(". %s/.golive.rc && python manage.py %s" % (env.remote_home, command))


class DjangoSetup(BaseTask, DjangoBaseTask):
    ROLES = "APP_HOST"
    supervisor_conf_template = "golive/supervisor_django.conf"
    supervisor_run_template = "golive/supervisor_django.run"

    def __init__(self):
        super(DjangoSetup, self).__init__()
        env.user = config['USER']
        self.set_supervisor_appname()

    def set_supervisor_appname(self):
        self.supervisor_appname = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])

    def init(self):
        info("DJANGO: create basic directories in $HOME")
        self.mkdir("/home/%s/code" % config['USER'])
        self.mkdir("/home/%s/conf" % config['USER'])
        self.mkdir("/home/%s/log" % config['USER'])
        self.mkdir("/home/%s/static" % config['USER'])

    def deploy(self):
        env.remote_home = "/home/" + config['USER']
        env.user = config['USER']
        env.project_name = config['PROJECT_NAME']
        # startup
        self._configure_startup()

        self._stop()
        self._sync()
        if config.get("OPTIONS") and not config['OPTIONS']['fast']:
            self._install_requirements()
        self._syncdb()
        if config.get("OPTIONS") and not config['OPTIONS']['fast']:
            self._collecstatic()
        self._start()

        allow = [(environment.get_role('WEB_HOST').hosts, IPTablesSetup.DESTINATION_ALL, self._port())]
        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
        iptables.set_rules(self.__class__.__name__)
        iptables.activate()

        self._status()

    def update(self):
        env.remote_home = "/home/" + config['USER']
        env.user = config['USER']
        env.project_name = config['PROJECT_NAME']

        self._stop()
        self._sync()
        if not config['OPTIONS']['fast']:
            self._install_requirements()
        self._syncdb()
        if not config['OPTIONS']['fast']:
            self._collecstatic()
        self._start()

    def _stop(self):
        info("DJANGO: stop procs with supervisorctl")
        self.execute(sudo, "supervisorctl stop %s" % self.supervisor_appname)

    def _status(self):
        out = self.execute(sudo, "supervisorctl status %s" % self.supervisor_appname)
        self._check_output(out, "RUNNING", "PROCESS")

    def _start(self):
        info("DJANGO: start procs with supervisorctl")
        self.execute(sudo, "supervisorctl start %s" % self.supervisor_appname)

    def _collecstatic(self):
        info("DJANGO: manage collectstatic")
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
            ADDONS=registry.objects_active_name,
            APPNAME=self.supervisor_appname,
            SETTINGS=self._settings_modulestring(),
            PORT=self._port()
        )

        # file for supervisor
        supervisor.set_local_filename(self.__class__.supervisor_conf_template)
        supervisor.set_destination_filename("/etc/supervisor/conf.d/%s.conf" % self.supervisor_appname)
        supervisor.init()
        supervisor.deploy()

        # set user for fabric
        env.user = config['USER']

        # addon's
        if registry.is_active(NewRelicPythonAddon.NAME):
            # create ini file for new relic
            newrelic = NewRelicPythonAddon()
            newrelic.deploy()
            # we need to extend the template with newrelic stuff
            self.__class__.supervisor_run_template = \
                self.__class__.supervisor_run_template.replace(".run", "_newrelic.run").\
                    replace("golive", "golive/addons/newrelic")

            supervisor.set_context_data( PRE_EXECUTABLE="/home/%s/.virtualenvs/%s/bin/newrelic-admin run-program" %
                                   (config['USER'], config['PROJECT_NAME'])
            )


        # run wrapper script
        supervisor.set_context_data(ADDONS=registry.objects_active)
        supervisor.set_local_filename(self.__class__.supervisor_run_template)
        supervisor.set_destination_filename("/home/%s/%s.run" % (config['USER'], self.supervisor_appname))
        supervisor.init()
        supervisor.deploy()
        supervisor.post_deploy()

    def status(self):
        self._status()

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
        env.user = config['USER']
        env.remote_home = "/home/" + env.user
        self.execute(rsync_project, "%s/code/" % env.remote_home, os.getcwd(), ["*.pyc", "*.log", "**.git/*"], True)

    def _install_requirements(self):
        # needed for private repos, local keys get forwarded
        env.forward_agent = True
        env.user = config['USER']
        env.remote_home = "/home/" + config['USER']

        virtualenv_dir = '%s/.virtualenvs/%s' % (env.remote_home, env.project_name)
        pip_mirror = "http://c.pypi.python.org/simple"

        info("DJANGO: install python modules in virtualenv %s" % virtualenv_dir)
        # from requirements.txt
        with prefix('. %s/bin/activate' % virtualenv_dir):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                cmd = "pip install -i http://c.pypi.python.org/simple " \
                      "--download-cache=/var/cache/pip " \
                      "-r requirements.txt"
                debug("PIP: " + cmd)
                debug(self.execute(run, cmd))

        # from class variable
        if hasattr(self.__class__, "python_packages"):
            for package in self.__class__.python_packages.split(" "):
                with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
                    with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                        self.execute(run, "pip install -i %s --download-cache=/var/cache/pip %s" % (pip_mirror, package))

    @runs_once
    def _syncdb(self):
        info("DJANGO: synchronize database schema")
        self._prepare_db()

        # sync
        out = self.manage("syncdb --noinput --settings=%s" % self._settings_modulestring())
        host, value = out.popitem()
        info("DJANGO SYNC: %s" % value)

        # migrate
        if self._use_south():
            out = self.manage("migrate --noinput --settings=%s" % self._settings_modulestring())
            host, value = out.popitem()
            info("DJANGO MIGRATE: %s" % value)

    def _use_south(self):
        db_host = config['DB_HOST']
        db_name = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])
        sql = "SELECT COUNT(*) FROM south_migrationhistory;"
        out = execute(run, ("echo \"%s\" | sudo su - postgres -c \"psql -d %s 2>&1 1>/dev/null\"; echo $?" % (sql, db_name)), hosts=[db_host])
        return out[db_host] == '0'

    def _prepare_db(self):
        # get db node
        db_host = config['DB_HOST']
        # make db name
        db_name = "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'])
        db_password = get_remote_envvar('GOLIVE_DB_PASSWORD', db_host)
        # create user (role)
        user = config['USER']
        with settings(warn_only=True):
            execute(sudo, ("su - postgres -c \"createuser -U postgres -l -S -d -R %s\"" % (user)),
                    hosts=[db_host])
        # set password
        sql = "ALTER USER %s WITH ENCRYPTED PASSWORD '%s';" % (user, db_password)
        self.execute_once(run, ("echo \"%s\" | sudo su - postgres -c psql" % sql))
        with settings(warn_only=True):
            # create database
            info("DJANGO: create database %s" % db_name)
            execute(sudo, ("su - postgres -c \"createdb -U postgres -O %s -E UTF8 -T template0 %s\"" % (
                config['USER'],
                db_name)), hosts=[db_host])


class DjangoSetupGunicorn(DjangoSetup):
    python_packages = "gunicorn supervisor"
    supervisor_conf_template = "golive/supervisor_djangogunicorn.conf"
    supervisor_run_template = "golive/supervisor_djangogunicorn.run"


class WorkerSetup(DjangoSetup):
    supervisor_conf_template = "golive/supervisor_celery_worker.conf"
    supervisor_run_template = "golive/supervisor_celery_worker.run"

    def set_supervisor_appname(self):
        super(WorkerSetup, self).set_supervisor_appname()
        self.supervisor_appname += "_worker"


class WorkerCamSetup(DjangoSetup):
    supervisor_conf_template = "golive/supervisor_celery_worker_cam.conf"
    supervisor_run_template = "golive/supervisor_celery_worker_cam.run"

    def set_supervisor_appname(self):
        super(WorkerCamSetup, self).set_supervisor_appname()
        self.supervisor_appname += "_worker_cam"



