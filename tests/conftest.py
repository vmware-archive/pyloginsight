from mock_loginsight_server import MockedConnection
from pyloginsight.connection import Connection, Credentials
import socket
from collections import namedtuple
import logging


logger = logging.getLogger(__name__)


socket.setdefaulttimeout(1)
ConnectionContainer = namedtuple("Connections", ["clazz", "hostname", "goodcredentials", "verify"])

usemockserver = True
useliveserver = False
useinternet = False

live_server = ConnectionContainer(Connection, "real.server.example.com", Credentials("admin", "secret", "Local"), False)
live_server = None  # Disable entirely unless desired; consider making a pytest argument


def pytest_generate_tests(metafunc):
    """Called by pytest to parametize tests."""
    global usemockserver, useliveserver

    connections = []

    if usemockserver:
        connections.append(ConnectionContainer(MockedConnection, "mockserverlocal", Credentials("admin", "password", "mock"), True))

    if useliveserver:
        if useliveserver and live_server and socket.gethostbyname(live_server.hostname):
            logger.warning("Using live server {0}".format(live_server))
            connections.append(live_server)
        else:
            useliveserver = False

    credentialled_connections = {"good": [], "fake": [], "none": []}
    for c in connections:
        credentialled_connections['good'].append(c.clazz(c.hostname, auth=c.goodcredentials, verify=c.verify))
        credentialled_connections['none'].append(c.clazz(c.hostname, auth=None, verify=c.verify))
        credentialled_connections['fake'].append(c.clazz(c.hostname, auth=Credentials("fake", "fake", "fake"), verify=c.verify))

    if 'connection' in metafunc.fixturenames:
        metafunc.parametrize(
            "connection",
            credentialled_connections['good'],
            ids=identifiers_for_test_parameters)

    if 'blank_credential_connection' in metafunc.fixturenames:
        metafunc.parametrize(
            "blank_credential_connection",
            credentialled_connections['none'],
            ids=identifiers_for_test_parameters)

    if 'fake_credential_connection' in metafunc.fixturenames:
        """Credentials use provider=fake, which cannot ever succeed."""
        metafunc.parametrize(
            "fake_credential_connection",
            credentialled_connections['fake'],
            ids=identifiers_for_test_parameters)

    if 'wrong_credential_connection' in metafunc.fixturenames:
        metafunc.parametrize(
            "wrong_credential_connection",
            credentialled_connections['fake'] + credentialled_connections['none'],
            ids=identifiers_for_test_parameters)

    if 'all_credential_connection' in metafunc.fixturenames:
        metafunc.parametrize(
            "all_credential_connection",
            credentialled_connections['fake'] + credentialled_connections['none'] + credentialled_connections['good'],
            ids=identifiers_for_test_parameters)

    if 'server' in metafunc.fixturenames:
        metafunc.parametrize(
            "server",
            [c.server for c in credentialled_connections['good']],
            ids=identifiers_for_test_parameters
        )


def identifiers_for_test_parameters(val):
    return str(val).replace(".", "_")
    """
    if isinstance(val, (MockedConnection, )):
        return 'MockedConnection-{x._hostname}:{x._port}'.format(x=val).replace(".", "_")
    if isinstance(val, (Connection,)):
        print(val)
        return 'Connection-{x._hostname}:{x._port}'.format(x=val).replace(".", "_")
    if isinstance(val, (LogInsightMockAdapter,)):
        return 'LogInsightMockAdapter-{x._hostname}:{x._port}'.format(x=val).replace(".", "_")
    """
