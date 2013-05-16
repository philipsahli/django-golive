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
        INIT_USER: fatrix
        PROJECT_NAME: django_example
        PUBKEY: $HOME/user.pub
    TESTING:
        SERVERNAME: golive-sandbox1
        ROLES:
            APP_HOST:
                - testbox1
            DB_HOST:
                - testbox1
            WEB_HOST:
                - testbox1"""

    def handle(self, *args, **options):

        example_file = open(Stack.CONFIG, 'w')
        example_file.write(Command.example)
        example_file.close()

    def end(self):
        self.stdout.write('Done\n')
