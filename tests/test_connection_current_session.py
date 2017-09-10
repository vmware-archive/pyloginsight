import pytest
from pyloginsight.connection import Unauthorized

"""Attempt to interact with server while bearing blank or fake credentials. Server should respond consistently for each."""


def test_fails_without_credentials(wrong_credential_connection):
    with pytest.raises(Unauthorized) as excinfo:
        resp = wrong_credential_connection.get("/sessions/current")

    s = wrong_credential_connection.server
    with pytest.raises(Unauthorized) as excinfo:
        discard = s.current_session


def test_ok_with_credentials(connection):
    resp = connection.get("/sessions/current")
    assert 'ttl' in resp

    s = connection.server
    session = s.current_session
    assert 'ttl' in resp
