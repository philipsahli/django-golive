from django.core.management import BaseCommand
from fabric.state import output
import sys
from golive.stacks.stack import StackFactory, Stack
import yaml


class Command(BaseCommand):
    help = 'Creates a basic exampe configuration file'
    output['stdout'] = False

    example = """CONFIG:
    PLATFORM: DEDICATED
    STACK: CLASSIC

ENVIRONMENTS:
    DEFAULTS:
        INIT_USER: root
        PROJECT_NAME: djangoproject
        PUBKEY: $HOME/.ssh/id_dsa.pub
    TESTING:
        SERVERNAME: testserver
        ROLES:
            APP_HOST:
                - testserver
            DB_HOST:
                - testserver
            WEB_HOST:
                - testserver"""

    def handle(self, *args, **options):

        example_file = open(Stack.CONFIG, 'w')
        example_file.write(Command.example)
        example_file.close()

    def end(self):
        self.stdout.write('Done\n')
