import pytest

from pyloginsight.connection import Unauthorized
from pyloginsight.models import Server

"""Attempt to interact with server while bearing blank or fake credentials. Server should respond consistently for each."""


def test_retrieve_current_session_unauthorized(wrong_credential_connection):
    with pytest.raises(Unauthorized) as excinfo:
        resp = wrong_credential_connection._get("/sessions/current")
        assert resp.status_code == 401

    s = Server.copy_connection(wrong_credential_connection)
    with pytest.raises(Unauthorized) as excinfo:
        discard = s.current_session
