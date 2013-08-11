from optparse import make_option
from golive.management import CoreCommand
from django.core.management import BaseCommand


class Command(CoreCommand):
    option_list = BaseCommand.option_list + (
        make_option('--source_env',
                    action='store',
                    dest='source_env',
                    default=None,
                    help='Restore from environment'),
    )
