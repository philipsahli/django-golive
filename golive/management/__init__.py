from django.core.management import BaseCommand
from fabric.state import output
import sys
from golive.stacks.stack import StackFactory
import yaml


class CoreCommand(BaseCommand):
    env_id = '<env_id>'
    help = 'Manage the given environment'
    output['stdout'] = False
    # option_list = BaseCommand.option_list + (
    #     make_option('--role',
    #                 dest='role',
    #                 default=None,
    #                 help='Operate on roles'),
    #     make_option('--host',
    #                 dest='host',
    #                 default=None,
    #                 help='Operate on hosts'),
    #     make_option('--task',
    #                 dest='task',
    #                 default=None,
    #                 help='Execute tasks only'),
    #)

    def get_config_value(self, key):
        return self.config[key]

    def handle(self, *args, **options):
        job = sys.argv[1]
        if len(args) < 1:
            self.stderr.write('Missing env_id\n')
            sys.exit(1)

        # load user config
        environment_configfile = open("golive.yml", 'r')
        stackname = self.environment_config_temp = yaml.load(environment_configfile)['CONFIG']['STACK']

        self.stack = StackFactory.get(stackname)
        self.stack.setup_environment(args[0])

        # task decision
        task = None
        if 'task' in options:
            task = options['task']
        # role decision
        role = None
        if options.has_key('role'):
            role = options['role']

        # execute
        self.stack.do(job, task=task, role=role)

    def end(self):
        self.stdout.write('Done\n')
