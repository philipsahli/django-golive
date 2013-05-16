import pprint
import socket

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
