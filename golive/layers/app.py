from fabric.context_managers import cd, prefix
from fabric.contrib.project import rsync_project, os
from fabric.operations import run
from fabric.state import env
from base import *


class PythonSetup(BaseTask, DebianPackageMixin):
    ROLES = "APP_HOST"
    package_name = 'python-virtualenv python-pip virtualenvwrapper'

    def install(self, update=True):
        self.execute(run, "virtualenv --no-site-packages .virtualenvs/%s" % env.project_name)


class ProjectDeployment(BaseTask):
    ROLES = "APP_HOST"

    def install(self):
        self.mkdir("$HOME/code")
        self.update()
        self._configure_startup()

    def update(self):
        env.remote_home = "/home/"+env.user
        env.project_name = self.config['PROJECT_NAME']
        self._sync()
        self._install_requirements()
        self._configure_startup()

    def _configure_startup(self):
        supervisor = SupervisorSetup(self.config)
        supervisor.set_context_data(PYTHON="/home/%s/.virtualenvs/%s/bin/python" % (self.config['USER'],
                                                                        self.config['PROJECT_NAME']),
                                    PROJECT_DIR="/home/%s/code/%s" % (self.config['USER'],
                                                                      self.config['PROJECT_NAME']),
                                    PROJECT=self.config['PROJECT_NAME'],
                                    ENVIRONMENT=self.config['ENV_ID']
                                    )
        supervisor.set_filename("golive/supervisord_django.conf")
        supervisor.install()

    def _sync(self):
        env.remote_home = "/home/"+env.user
        self.execute(rsync_project, "%s/code/" % env.remote_home, os.getcwd(), ["*.pyc", "*.log", "**.git/*"], True)

    def _install_requirements(self):
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                self.execute(run, "pip install -r requirements.txt")

    def _uninstall_requirements(self):
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                self.execute(run, "pip uninstall -y -r requirements.txt")

    def remove(self):
        self._uninstall_requirements()
        self.rmdir("$HOME/code")
