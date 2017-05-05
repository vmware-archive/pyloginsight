import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock


class TestConnection():
    def test_bare_connection_makes_no_requests(self):

        adapter = requests_mock.Adapter()
        adapter_sessions = adapter.register_uri('ANY', 'ANY', status_code=400)

        connection = Connection("mockserverlocal")
        connection._requestsession.mount('https://', adapter)
        assert adapter_sessions.call_count == 0

    def test_authentication_required(self):
        """
        Mock /sessions and a fake /demand_auth resource.
        Force an HTTP 401 response on an non-credentialed request for the protected /demand_auth resource.
        The AuthorizationHeaderAuthentication should request /demand_auth, observe a HTTP 401, login, & retry the request.
        """
        credentials = Credentials(username="admin", password="pass", provider="mock")
        connection = Connection("mockserverlocal", auth=credentials)

        adapter = requests_mock.Adapter()

        successful_login = '{"userId":"027a19e4-f216-4f3e-a1f2-8f2b72c5b1b4","sessionId":"hNhXgA","ttl":1800}'
        adapter_sessions = adapter.register_uri('POST', '/api/v1/sessions', text=successful_login, status_code=200)

        adapter_failed = adapter.register_uri('POST', '/api/v1/demand_auth', text="denied protected resource", status_code=401)

        # Most specific matcher for the same URI has to be last
        adapter_success = adapter.register_uri('POST', '/api/v1/demand_auth',
                                               request_headers={'Authorization': 'Bearer hNhXgA'},
                                               text="protected resource", status_code=200)

        connection._requestsession.mount('https://', adapter)

        r = connection.post("/demand_auth", data="submitbody")

        assert adapter_sessions.call_count == 1
        assert adapter_success.call_count == 1
        assert adapter_failed.call_count == 1

        # Retrieved protected resource
        assert r == "protected resource"

        # No headers leaked
        assert "Authorization" not in connection._requestsession.headers

    def test_authentication_repeated(self):
        """
        Mock /sessions and a fake /demand_auth resource.
        Force an HTTP 401 response on EVERY request for the protected /demand_auth resource.
        The AuthorizationHeaderAuthentication should request /demand_auth, observe a HTTP 401, login, & retry the request,
        but then give up.
        """
        credentials = Credentials(username="admin", password="pass", provider="mock")
        connection = Connection("mockserverlocal", auth=credentials)

        adapter = requests_mock.Adapter()

        successful_login = '{"userId":"012345678-9ab-cdef-0123-456789abcdef","sessionId":"hNhXgA","ttl":1800}'
        adapter_sessions = adapter.register_uri('POST', '/api/v1/sessions', text=successful_login,
                                                status_code=200)

        adapter_failed = adapter.register_uri('POST', '/api/v1/demand_auth',
                                              text="denied protected resource", status_code=401)

        connection._requestsession.mount('https://', adapter)

        with pytest.raises(Unauthorized) as excinfo:
            connection.post("/demand_auth", data="submitbody")

        assert excinfo.value.args[0] == 'Authentication failed'
        assert excinfo.value.args[1].status_code == 401

        assert adapter_sessions.call_count == 1
        assert adapter_failed.call_count == 2

        # No headers leaked
        assert "Authorization" not in connection._requestsession.headers

    def test_failed_authentication(self):
        """
        Mock /sessions and a fake /demand_auth resource.
        Force an HTTP 401 response on EVERY request for the protected /demand_auth resource.
        Also fail /sessions requests
        The AuthorizationHeaderAuthentication should request /demand_auth, observe a HTTP 401, fail to login & raise exception
        """
        credentials = Credentials(username="admin", password="wrongpassword", provider="mock")
        connection = Connection("mockserverlocal", auth=credentials)

        adapter = requests_mock.Adapter()

        adapter_sessions = adapter.register_uri('POST', '/api/v1/sessions', text="",
                                                status_code=200)

        adapter_failed = adapter.register_uri('POST', '/api/v1/demand_auth',
                                              text="denied protected resource", status_code=401)

        connection._requestsession.mount('https://', adapter)

        with pytest.raises(Unauthorized) as excinfo:
            connection.post("/demand_auth", data="submitbody")

        assert excinfo.value.args[0] == 'Authentication failed'
        assert excinfo.value.args[1].status_code == 200

        assert adapter_sessions.call_count == 1
        assert adapter_failed.call_count == 1  # only one request was made to the protected resource /demand_auth

        # No authorization header leaked
        assert "Authorization" not in connection._requestsession.headers
