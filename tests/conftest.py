# -*- coding: utf-8 -*-

from mock_loginsight_server import MockedConnection
from pyloginsight.connection import Connection, Credentials
from pyloginsight.exceptions import ServerWarning, AlreadyBootstrapped

import sys
from collections import namedtuple
import logging
import pytest
from requests.adapters import HTTPAdapter

import socket
import urllib3
import warnings

ROOTLOGGER = True

if ROOTLOGGER:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logging.captureWarnings(True)


socket.setdefaulttimeout(1)
urllib3.disable_warnings()
warnings.simplefilter("ignore", ServerWarning)

ConnectionContainer = namedtuple("Connections", ["clazz", "hostname", "port", "auth", "verify"])


def pytest_addoption(parser):
    parser.addoption(
        "--server", action="store", metavar="SERVER:PORT", default="mockserverlocal:9543",
        help="Also run tests against https://SERVER:PORT, can be listed multiple times. Mock server @ mockserverlocal:9543")
    parser.addoption(
        "--username", action="store", default="admin",
        help="Used with --server")
    parser.addoption(
        "--password", action="store", default="VMware123!",
        help="Used with --server")
    parser.addoption(
        "--provider", action="store", default="Local",
        help="Used with --server")
    parser.addoption(
        "--license", action="store", required=False,
        help="Apply license to --server if needed")


def identifiers_for_server_list(val):
    return "{}({}:{})".format(str(val.clazz.__name__), val.hostname, val.port)


def pytest_generate_tests(metafunc):

    # Creates a "servers" fixture on the fly when another fixture uses it.
    if 'servers' in metafunc.fixturenames:

        configs = []

        s = metafunc.config.getoption('server')
        print("Running tests against server {}".format(s))

        hostname, port = s.split(":")

        # magic hostname
        if hostname == "mockserverlocal":
            clazz = MockedConnection
        else:
            clazz = Connection

        configs.append(
            ConnectionContainer(
                clazz,
                hostname,
                int(port),
                Credentials(
                    metafunc.config.getoption("username"),
                    metafunc.config.getoption("password"),
                    metafunc.config.getoption("provider"),
                ),
                False
            )
        )

        metafunc.parametrize("servers",
                             argvalues=configs,
                             ids=identifiers_for_server_list)


class SetHostHeaderAdapter(HTTPAdapter):
    def __init__(self, host_header, *args, **kwargs):
        self.host_header = host_header
        super(SetHostHeaderAdapter, self).__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        request.headers['Host'] = self.host_header
        return super(SetHostHeaderAdapter, self).send(request, **kwargs)


@pytest.fixture
def licensekey(pytestconfig):
    """License key which should be applied to the remote server(s)."""
    return pytestconfig.getoption('license')


@pytest.fixture
def connection(servers, licensekey):
    """A pyloginsight.connection to a remote server."""
    c = servers
    connection_instance = c.clazz(c.hostname, auth=c.auth, port=c.port, verify=c.verify)

    # Lie about port number
    if c.clazz is Connection:
        adapter = SetHostHeaderAdapter("%s:9543" % c.hostname)
        connection_instance._requestsession.mount(connection_instance._apiroot, adapter)

    ensure_server_bootstrapped_and_licensed(connection_instance, licensekey)
    return connection_instance


# Matrix of bad credentials multipled by server list
@pytest.fixture(params=[Credentials("fake", "fake", "fake"), None])
def wrong_credential_connection(servers, request, licensekey):
    """A pyloginsight.connection to a remote server, with non-functional credentials."""
    c = servers._replace(auth=request.param)
    connection_instance = c.clazz(c.hostname, auth=c.auth, port=c.port, verify=c.verify)
    # Lie about port number
    if c.clazz is Connection:
        adapter = SetHostHeaderAdapter("%s:9543" % c.hostname)
        connection_instance._requestsession.mount(connection_instance._apiroot, adapter)
    ensure_server_bootstrapped_and_licensed(connection_instance, licensekey)
    return connection_instance


def ensure_server_bootstrapped_and_licensed(connection, licensekey):
    """
    :param connection: a pyloginsight.Connection instance
    """
    return True

    # Only need to check once
    if connection._apiroot in ensure_server_bootstrapped_and_licensed.cache:
        return True

    try:
        connection.bootstrap(email="testbootstrapped@localhost")
    except AlreadyBootstrapped:
        pass

    connection.wait_until_started()

    if 'ACTIVE' != connection.server.license.licenseState:
        connection.server.license.append(str(licensekey))

    ensure_server_bootstrapped_and_licensed.cache.append(connection._apiroot)

ensure_server_bootstrapped_and_licensed.cache = []
