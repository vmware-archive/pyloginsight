from mock_loginsight_server import MockedConnection
from pyloginsight.connection import Connection, Credentials
from pyloginsight.exceptions import ServerWarning

import socket
from collections import namedtuple
import logging
import pytest

logger = logging.getLogger(__name__)

import sys
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logging.captureWarnings(True)

import urllib3
urllib3.disable_warnings()

import warnings
warnings.simplefilter("ignore", ServerWarning)

socket.setdefaulttimeout(1)
ConnectionContainer = namedtuple("Connections", ["clazz", "hostname", "auth", "verify"])

usemockserver = True
useliveserver = True
useinternet = False


server_instance_metadata = []
if usemockserver:
    server_instance_metadata.append(ConnectionContainer(MockedConnection, "mockserverlocal", Credentials("admin", "password", "mock"), True))
if useliveserver:
    #server_instance_metadata.append(ConnectionContainer(Connection, "real.server.example.com", Credentials("admin", "secret", "Local"), False))
    server_instance_metadata.append(ConnectionContainer(Connection, "192.168.50.149", Credentials("admin", "VMware123!", "Local"), False))


def identifiers_for_test_parameters(val):
    print("Compute identifier for", val)
    return str(val).replace(".", "_")


# Fixtures using above servers and working credentials
@pytest.fixture(
    params=server_instance_metadata,
    ids=identifiers_for_test_parameters
)
def connection(request):
    c = request.param
    connection_instance = c.clazz(c.hostname, auth=c.auth, verify=c.verify)
    return connection_instance


@pytest.fixture(
    #params=recredentialed_server_instance_metadata,
    params=[sim._replace(auth=None) for sim in server_instance_metadata] + [sim._replace(auth=Credentials("fake", "fake", "fake")) for sim in server_instance_metadata],
    ids=identifiers_for_test_parameters
)
def wrong_credential_connection(request):
    c = request.param
    connection_instance = c.clazz(c.hostname, auth=c.auth, verify=c.verify)
    return connection_instance

