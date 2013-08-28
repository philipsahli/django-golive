import os
from django.core.management import BaseCommand
import subprocess
from fabric.operations import run
from fabric.state import output
import thread
from fabric.tasks import execute
import sys
import time
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

        try:
            for host in hosts:
                thread.daemon = True
                thread.start_new_thread(tail_logs, ("thread_name", host, user))
            while True:
                pass
        except (KeyboardInterrupt, SystemExit):
            print "Exiting"


def tail_logs(thread_name, host, user):
    cmd = ["ssh", "-x", "-l", user, host, "tail", "-F", "-f", "log/*log", "|",
           "while", "read", "line", ";", "do", "echo", host, "$line", ";", "done"
    ]
    subprocess.call(cmd, shell=False)
