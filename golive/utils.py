import os
import pprint
import socket
import logging

from colorlog import ColoredFormatter
from django.core.exceptions import ImproperlyConfigured
from fabric.operations import run
from fabric.tasks import execute


def nprint(m):
    pprint.pprint(m)


def output(m):
    print "----------"
    print "m"
    print "----------"


def resolve_host(host):
    ip = socket.gethostbyname(host)
    return ip


# logging

LOGGER_NAME = "golive"
formatter = ColoredFormatter(
    '%(log_color)s%(asctime)-15s %(levelname)-6s %(environment_name)-8s %(message)s',
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red',
        }
)
LEVEL = logging.DEBUG
handler = logging.StreamHandler()
handler.setLevel(LEVEL)
handler.setFormatter(formatter)

# Get an instance of a logger
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LEVEL)
logger.addHandler(handler)


def logit(level, message, host=None):
    from golive.stacks.stack import config

    if config is not None:
        d = {'environment_name': config['ENV_ID']}
    else:
        d = {'environment_name': "----"}

    if host:
        d['host'] = host
    else:
        d['host'] = "----"

    if host:
        message = "%s: %s" % (host, message)
    if "*" not in message[0]:
        message = "**** " + str(message)

    if level == logging.INFO:
        logger.info(message, extra=d)
    elif level == logging.ERROR:
        logger.error(message, extra=d)
    elif level == logging.DEBUG:
        logger.debug(message, extra=d)
    elif level == logging.WARN:
        logger.warn(message, extra=d)
    else:
        raise Exception("Loglevel not configured")


def info(message, host=None):
    logit(logging.INFO, message, host)


def debug(message, host=None):
    logit(logging.DEBUG, message, host)


def warn(message, host=None):
    logit(logging.WARN, message, host)


def error(message, host=None):
    logit(logging.ERROR, message, host)


ENV_PREFIX = "GOLIVE_"


def get_var(var_name):
    """ Get the environment variable or return exception """
    # Taken from twoo scoops book, Thank you guys.
    # https://django.2scoops.org/
    try:
        return os.environ[ENV_PREFIX + var_name]
    except KeyError:
        error_msg = "Set the %s env variable with set_var" % var_name
        raise ImproperlyConfigured(error_msg)


def get_remote_envvar(var, host):
    out = execute(run, "echo $%s" % var, host=host).get(host, None)
    if not bool(out):
        error_msg = "Set the %s env variable with set_var" % var.replace(ENV_PREFIX, "")
        raise ImproperlyConfigured(error_msg)
    return out