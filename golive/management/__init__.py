from optparse import make_option
from django.core.management import BaseCommand
from fabric.state import output
import sys
import time
from golive.collector import TaskCollector
from golive.utils import nprint


class CoreCommand(BaseCommand):
    env_id = '<env_id>'
    help = 'Manage the given environment'
    output['stdout'] = False
    option_list = BaseCommand.option_list + (
        make_option('--role',
                    dest='role',
                    default=None,
                    help='Operate on roles'),
        make_option('--host',
                    dest='host',
                    default=None,
                    help='Operate on hosts'),
        make_option('--task',
                    dest='task',
                    default=None,
                    help='Execute tasks only'),
    )

    def get_config_value(self, key):
        return self.config[key]

    def handle(self, *args, **options):
        job = sys.argv[1].upper()
        if len(args) < 1:
            self.stderr.write('Missing env_id\n')
            sys.exit(1)

        kwargs = {
            'env_id': args[0],
            'job': job
        }

        if 'role' in options and options['role']:
            kwargs.update({'role': options['role']})
        elif 'host' in options and options['host']:
            kwargs.update({'host': options['host']})
        else:
            kwargs.update({'job': job})

        if 'task' in options and options['task']:
            kwargs.update({'task': options['task']})
            print kwargs

        task_manager = TaskCollector.run(**kwargs)
        time.sleep(1)
        task_manager.run()

    def end(self):
        self.stdout.write('Done\n')
