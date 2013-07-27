import inspect
import os
import pprint
import socket
from django.core.exceptions import ImproperlyConfigured

__author__ = 'fatrix'


def nprint(m):
    pprint.pprint(m)


def output(m):
    print "----------"
    print "m"
    print "----------"


def resolve_host(host):
    ip = socket.gethostbyname(host)
    return ip

LOGGER_NAME = "golive"
ENV_PREFIX = "GOLIVE_"

# import the logging library

import logging
formatter = logging.Formatter('%(asctime)-15s %(levelname)-6s %(environment_name)-8s %(message)s')
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)

# Get an instance of a logger
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)
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


def get_var(var_name):
    """ Get the environment variable or return exception """
    # Taken from twoo scoops book, Thank you guys.
    # https://django.2scoops.org/
    try:
        return os.environ[ENV_PREFIX+var_name]
    except KeyError:
        error_msg = "Set the %s env variable with set_var" % var_name
        raise ImproperlyConfigured(error_msg)
