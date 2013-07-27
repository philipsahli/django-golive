import os
from django.core.management import BaseCommand
from fabric.state import output
import sys
from golive.stacks.stack import StackFactory, config
import yaml


class Command(BaseCommand):
    help = 'Set variables on the remote environment'
    output['stdout'] = False

    def get_config_value(self, key):
        return self.config[key]

    def handle(self, *args, **options):
        # load user config
        environment_configfile = open("golive.yml", 'r')
        stackname = self.environment_config_temp = yaml.load(environment_configfile)['CONFIG']['STACK']

        self.stack = StackFactory.get(stackname)
        self.stack.setup_environment(args[0])

        # execute
        hosts = self.stack.environment.hosts
        user = self.stack.environment_config['USER']
        print user
        if len(hosts) > 1:
            self.stderr.write('Multiple hosts possible\n')
            sys.exit(1)

        # login
        os.execvp("ssh", ("ssh", "-x", "-l",  user, self.stack.environment.hosts[0]))
