import os
from fabric.context_managers import prefix, cd
from fabric.operations import sudo, prompt, run
from fabric.state import env
from golive.addons import registry, SLOT_AFTER
from golive.layers.base import TemplateBasedSetup, DebianPackageMixin, BaseTask
from golive.stacks.stack import Stack
from golive.utils import info, error, get_remote_envvar

SLOT_BEFORE = 'BEFORE'
SLOT_INCLUDED = 'INCLUDED'


class Addon(BaseTask):
    # default for which tasks the addon can be used
    TASKS = []

    # execute before or after the task

    SLOT = SLOT_AFTER
    METHOD = Stack.DEPLOY

    def __init__(self):
        super(Addon, self).__init__()

    def with_tasks(self):
        return self.__class__.TASKS

    def slot(self):
        return self.__class__.SLOT


class NewRelicPythonAddon(Addon, TemplateBasedSetup):
    NAME = "NEW_RELIC_PYTHON"
    TASKS = ["golive.layers.app.DjangoSetup"]
    SLOT = SLOT_INCLUDED

    TEMPLATE = "golive/addons/newrelic/newrelic.ini"

    def deploy(self):
        from golive.stacks.stack import config, environment
        self.local_filename = self.TEMPLATE
        if self.local_filename is None:
            return
        # render
        try:
            self.context_data = {'APPNAME': "%s_%s" % (config['PROJECT_NAME'], config['ENV_ID']),
                                 'USER': config['USER'],
                                 'LICENSE_KEY':  get_remote_envvar("GOLIVE_NEWRELIC_LICENSE_KEY",
                                                                   environment.get_role("APP_HOST").hosts[0]),

            }

            info("NEW_RELIC: create newrelic configuration")
            tmp_file = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)

            # send file
            self.destination_filename = "newrelic_%s.ini" % (config['ENV_ID'])
            destination_filename_path = os.path.join("/home/%s/%s" % (config['USER'], "conf"), self.destination_filename)
            self.put_sudo(tmp_file, destination_filename_path)
            info("NEW_RELIC: %s saved to %s" % (self.local_filename, self.destination_filename))

            # install python package
            python_package = "newrelic"
            info("NEW_RELIC: install python package '%s'" % python_package)
            with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
                with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                    self.execute(run, "pip install --download-cache=/var/cache/pip %s" % python_package)

        except Exception, e:
            error(e)

registry.register(NewRelicPythonAddon)


class NewRelicServerAgentAddon(Addon, DebianPackageMixin):
    license_key = None
    package_name = "newrelic-sysmond"

    NAME = "NEW_RELIC_SERVERAGENT"
    TASKS = ["golive.layers.base.BaseSetup"]
    SLOT = SLOT_AFTER
    METHOD = Stack.INIT

    def init(self):
        info("NEW_RELIC: start setup server agent")

        # prepare apt for the newrelic repository
        self.append("/etc/apt/sources.list.d/newrelic.list", "deb http://apt.newrelic.com/debian/ newrelic non-free")
        self.execute(sudo, "wget -O- https://download.newrelic.com/548C16BF.gpg | apt-key add -")

        # install newrelic-sysmond
        DebianPackageMixin.init(self, update=True)

        # add license key, prompt only once for it, save the key on class level for
        # other nodes
        if not self.__class__.license_key:
            self.__class__.license_key = prompt("Please enter your newrelic license_key: ")

        # configure
        self.execute(sudo, "nrsysmond-config --set license_key=%s" % self.__class__.license_key)
        # start
        self.execute(sudo, "/etc/init.d/newrelic-sysmond start")

        info("NEW_RELIC: end setup server agent")

registry.register(NewRelicServerAgentAddon)
