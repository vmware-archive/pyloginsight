import requests_mock
import logging
import pytest


from .sessions import MockedSessionsMixin
from .licenses import MockedLicensesMixin
from .version import MockedVersionMixin
from .exampleobject import MockedExampleObjectMixin
from .auth_providers import MockedAuthProvidersMixin
from .bootstrap import MockedBootstrapMixin
from .datasets_mock import MockedDatasetsMixin
from .groups_mock import MockedGroupsMixin
from .roles_mock import MockedRolesMixin

from pyloginsight.connection import Connection, Credentials

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


RAISE_ON_MISSING_MOCK_IMPLEMENTATION = False


class NotImplementedStubForMockAddress(requests_mock.exceptions.NoMockAddress):
    """register_uri() completed, but implementation is stubbed out."""


class LogInsightMockAdapter(MockedExampleObjectMixin, MockedRolesMixin, MockedGroupsMixin, MockedDatasetsMixin, MockedBootstrapMixin, MockedVersionMixin, MockedLicensesMixin, MockedSessionsMixin, MockedAuthProvidersMixin, requests_mock.Adapter):
    def Raise418(self, request, context):
        if RAISE_ON_MISSING_MOCK_IMPLEMENTATION:
            raise NotImplementedStubForMockAddress(request)
        context.status_code = 418  # Teapot, because a real server could return 501
        w = "{r.method} {r.url} not yet implemented in LoginsightMockAdapter".format(r=request)
        mockserverlogger.warning(w)
        pytest.xfail(w)
        return w


class MockedConnection(Connection):
    """A regular pyloginsight.connection.Connection that has a LogInsightMockAdapter pre-mounted"""
    def __init__(self, *args, **kwargs):
        # no outbound requests are made during init
        super(MockedConnection, self).__init__(*args, **kwargs)

        # Mount the requests-mock-adapter
        adapter = LogInsightMockAdapter()
        self._requestsession.mount('https://', adapter)


def mock_server_with_authenticated_connection():
    """Instantiate a LogInsightMockAdapter with a """
    raise DeprecationWarning()
    connection = Connection("mockserverlocal", auth=Credentials("admin", "password", "mock"))
    adapter = LogInsightMockAdapter()
    adapter.prep()
    connection._requestsession.mount('https://', adapter)
    return connection


def mock_server_with_authenticated_connection_and_bad_credentials():
    raise DeprecationWarning()
    connection = Connection("mockserverlocal", auth=Credentials("fakeuserthatdoesntexist", "", "mock"))
    adapter = LogInsightMockAdapter()
    adapter.prep()
    connection._requestsession.mount('https://', adapter)
    return connection


def mock_server_with_connection_and_no_credentials():
    raise DeprecationWarning()
    connection = Connection("mockserverlocal", auth=None)
    adapter = LogInsightMockAdapter()
    adapter.prep()
    connection._requestsession.mount('https://', adapter)
    return connection
