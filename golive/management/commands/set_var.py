from django.core.management import BaseCommand
from fabric.state import output
import sys
from golive.stacks.stack import StackFactory
import yaml


class Command(BaseCommand):
    help = 'Set variables on the remote environment'
    output['stdout'] = False

    def get_config_value(self, key):
        return self.config[key]

    def handle(self, *args, **options):
        job = 'set_var'
        if len(args) < 3:
            self.stderr.write('Missing arguments\n')
            sys.exit(1)

        # load user config
        environment_configfile = open("golive.yml", 'r')
        stackname = self.environment_config_temp = yaml.load(environment_configfile)['CONFIG']['STACK']

        self.stack = StackFactory.get(stackname)
        self.stack.setup_environment(args[0])
        # execute
        self.stack.do(job, full_args=args)

    def end(self):
        self.stdout.write('Done\n')
