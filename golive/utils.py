import os
import pprint
import socket
import logging

from colorlog import ColoredFormatter
from django.core.exceptions import ImproperlyConfigured


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
    #"%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
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
#LEVEL = logging.DEBUG
LEVEL = logging.INFO
handler = logging.StreamHandler()
handler.setLevel(LEVEL)
handler.setFormatter(formatter)

# Get an instance of a logger
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LEVEL)
logger.addHandler(handler)


def logit(level, message):
    from golive.stacks.stack import config
    d = {'environment_name': config['ENV_ID']}

    if "*" not in message:
        message="**** "+str(message)

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


def info(message):
    logit(logging.INFO, message)


def debug(message):
    logit(logging.DEBUG, message)


def warn(message):
    logit(logging.WARN, message)


def error(message):
    logit(logging.ERROR, message)


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
