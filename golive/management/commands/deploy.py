from optparse import make_option
from golive.management import CoreCommand
from django.core.management import BaseCommand


class Command(CoreCommand):

    #option_list = CoreCommand.option_list + (
    #    make_option('--role',
    #                dest='role',
    #                default=None,
    #                help='Operate on roles'),
    #    make_option('--host',
    #                dest='host',
    #                default=None,
    #                help='Operate on hosts'),
    #    make_option('--task',
    #                dest='task',
    #                default=None,
    #                help='Execute tasks only'),
    #)
    option_list = BaseCommand.option_list + (
        make_option('--fast',
                    action='store_true',
                    dest='fast',
                    default=None,
                    help="Don't execute time intensiv tasks (pip/collectstatic)"),
    )

