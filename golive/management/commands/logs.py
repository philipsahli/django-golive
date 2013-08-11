import os
from django.core.management import BaseCommand
from fabric.state import output
import sys
from golive.stacks.stack import StackFactory
import yaml


class Command(BaseCommand):
    help = 'Tail all logfiles in directory \'log\' (remote)'
    output['stdout'] = False

    def _load_config(self, args):
        # load user config
        environment_configfile = open("golive.yml", 'r')
        stackname = self.environment_config_temp = yaml.load(environment_configfile)['CONFIG']['STACK']
        self.stack = StackFactory.get(stackname)
        self.stack.setup_environment(args[0])

    def handle(self, *args, **options):
        self._load_config(args)

        # execute
        hosts = self.stack.environment.hosts
        user = self.stack.environment_config['USER']
        if len(hosts) > 1:
            self.stderr.write('Multiple hosts possible\n')
            sys.exit(1)

        # tail
        os.execvp("ssh", ("ssh", "-x", "-l",  user, self.stack.environment.hosts[0], "tail", "-f", "log/*log"))
