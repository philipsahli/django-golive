from optparse import make_option
from golive.management import SelectiveCommand


class Command(SelectiveCommand):
    option_list = SelectiveCommand.option_list + (
        make_option('--fast',
                    action='store_true',
                    dest='fast',
                    default=None,
                    help="Don't execute time intensiv tasks (pip/collectstatic)"),
    )

