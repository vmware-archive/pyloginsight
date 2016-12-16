import pytest
from functools import wraps
from pyloginsight.connection import Connection, Credentials, Unauthorized
from pyloginsight.models import Server, LicenseKeys
import requests_mock
from collections import namedtuple, Counter
import uuid
import json
from datetime import datetime
import logging
import time
import re

mockserverlogger = logging.getLogger("ServerMock")

class RandomDict(dict):
    """Subclass of `dict` that adds a list-like `append` method that generates a random UUID key"""
    def append(self, value):
        key = str(uuid.uuid4())
        while key in self:
            key = str(uuid.uuid4())
        self[key] = value
        return key


def requiresauthentication(fn):
    """Server mock; fail any request which does not contain the expected Authorization header with HTTP/401"""
    @wraps(fn)
    def wrapper(self, request, context):
        session_id = request.headers.get('Authorization', "")[7:]
        if session_id in self.sessions_known:  # TODO: Don't ignore TTL
            mockserverlogger.info("Verified bearer has a valid sessionId")
            return fn(self, request, context, session_id, self.sessions_known[session_id].userId)
        context.status_code = 401
        return ""
    return wrapper


trailing_guid_pattern = re.compile('.*/([a-f0-9-]+)$')

license_url_matcher = re.compile('/api/v1/licenses/([a-f0-9-]+)$')

User = namedtuple("User", field_names=["username", "password", "provider", "userId"])
Session = namedtuple("Session", field_names=["userId", "ttl", "created"])


def idfn(val):
    if isinstance(val, (Connection,)):
        return '{x._hostname}:{x._port}'.format(x=val).replace(".","_")
    if isinstance(val, (ServerMock,)):
        return '{x._hostname}:{x._port}'.format(x=val).replace(".","_")


class ServerMock(requests_mock.Adapter):
    SUCCESSFUL_LOGIN_JSON = '{"userId":"012345678-9ab-cdef-0123-456789abcdef","sessionId":"hNhXgA","ttl":1800}'
    LICENSE_LIST_JSON = '{"hasOsi": true, "limitedLicenseCapabilities": ["QUERY", "RBAC", "UPGRADE", "ACTIVE_DIRECTORY", "CONTENT_PACK"], "standardLicenseCapabilities": ["FORWARDING", "RBAC", "UPGRADE", "CUSTOM_SSL", "ACTIVE_DIRECTORY", "CONTENT_PACK", "VSPHERE_FULL_SUPPORT", "CLUSTER", "IMPORT_CONTENT_PACKS", "QUERY", "ARCHIVE", "THIRD_PARTY_CONTENT_PACKS"], "maxCpus": 0, "uninitializedLicenseCapabilities": ["RBAC", "ACTIVE_DIRECTORY", "CONTENT_PACK"], "hasCpu": false, "maxOsis": 0, "licenseState": "ACTIVE", "licenses": {"95bfa29a-e60d-49e7-b00e-8c40d83f2036": {"infinite": true, "configuration": "1 Operating System Instance (OSI)", "status": "Active", "expiration": 0, "licenseKey": "4J2TK-XXXXX-XXXXX-XXXXX-XXXXX", "count": 0, "error": "", "typeEnum": "OSI", "id": "95bfa29a-e60d-49e7-b00e-8c40d83f2036"}}, "hasTap": false}'
    NEW_LICENSE_KEY = 'M502V-XXXXX-XXXXX-XXXXX-XXXXX'
    EXISTING_LICENSE_UUID = "95bfa29a-e60d-49e7-b00e-8c40d83f2036"

    def prep(self):
        self.users_known = [User('admin', 'password', 'mock', "012345678-9ab-cdef-0123-456789abcdef")]
        self.licenses_known = RandomDict({'12345678-90ab-cdef-1234-567890abcdef': {'typeEnum': 'OSI', 'id': '12345678-90ab-cdef-1234-567890abcdef', 'error': '', 'status': 'Active', 'configuration': '1 Operating System Instance (OSI)', 'licenseKey': '4J2TK-XXXXX-XXXXX-XXXXX-XXXXX', 'infinite': True, 'count': 0, 'expiration': 0}})
        self.sessions_known = RandomDict()

        self.sessions_adapter = self.register_uri('POST',
                                                  'https://mockserver:9543/api/v1/sessions',
                                                  text=self.session_new,
                                                  status_code=200)

        self.sessions_adapter = self.register_uri('GET',
                                                  'https://mockserver:9543/api/v1/sessions/current',
                                                  text=self.session_current,
                                                  status_code=200)

        self.failure_adapter = self.register_uri('POST', 'https://mockserver:9543/api/v1/demand_auth',
                                           text="denied protected resource", status_code=401)

        # License Keys
        self.register_uri('GET', 'https://mockserver:9543/api/v1/licenses', status_code=200, text=self.callback_list_license)
        self.register_uri('POST', 'https://mockserver:9543/api/v1/licenses', status_code=201, text=self.callback_add_license)
        self.register_uri('DELETE', license_url_matcher, status_code=200, text=self.callback_remove_license)

    @requiresauthentication
    def callback_list_license(self, request, context, session_id, user_id):
        return json.dumps(self.get_license_summary_object())

    @requiresauthentication
    def callback_add_license(self, request, context, session_id, user_id):
        body = request.json()
        newitem = {'typeEnum': 'OSI', 'id': 'TBD', 'error': '', 'status': 'Active',
                   'configuration': '1 Operating System Instance (OSI)',
                   'licenseKey': body['key'], 'infinite': True, 'count': 0, 'expiration': 0}
        newitem['id'] = self.licenses_known.append(newitem)
        return json.dumps(newitem)

    @requiresauthentication
    def callback_remove_license(self, request, context, session_id, user_id):
        delete_guid = trailing_guid_pattern.match(request._url_parts.path).group(1)
        try:
            del self.licenses_known[delete_guid]
            mockserverlogger.info("Deleted license {0}".format(delete_guid))
        except KeyError:
            mockserverlogger.info("Attempted to delete nonexistant license {0}".format(delete_guid))
            context.status_code = 404
        return

    def get_license_summary_object(self):
        counts = Counter(OSI=0, CPU=0)
        for key, license in self.licenses_known.items():
            if not license['error']:
                counts[license['typeEnum']] += license["count"]

        return {"hasOsi": counts['OSI']>0,
                "hasCpu": counts['CPU']>0,
                "maxOsis": counts['OSI'],
                "maxCpus": counts['CPU'],
                "limitedLicenseCapabilities": ["QUERY", "RBAC", "UPGRADE", "ACTIVE_DIRECTORY", "CONTENT_PACK"],
                "standardLicenseCapabilities": ["FORWARDING", "RBAC", "UPGRADE", "CUSTOM_SSL", "ACTIVE_DIRECTORY", "CONTENT_PACK", "VSPHERE_FULL_SUPPORT", "CLUSTER", "IMPORT_CONTENT_PACKS", "QUERY", "ARCHIVE", "THIRD_PARTY_CONTENT_PACKS"],
                "uninitializedLicenseCapabilities": ["RBAC", "ACTIVE_DIRECTORY", "CONTENT_PACK"],
                "licenseState": "ACTIVE" if (counts['OSI']+counts['CPU']>0) else "INACTIVE",
                "licenses": self.licenses_known,
                "hasTap": False}

    @requiresauthentication
    def session_current(self, request, context, session_id, user_id):
        """Attempt to create a new session with provided credentials."""
        return json.dumps(self.sessions_known[session_id]._asdict())

    def session_new(self, request, context):
        """Attempt to create a new session with provided credentials."""
        self.session_timeout()
        attempted_credentials = request.json()
        for u in self.users_known:
            if u.username == attempted_credentials['username'] and u.provider == attempted_credentials['provider']:
                if u.password == attempted_credentials['password']:
                    mockserverlogger.info("Successful authentication as {u.username} = {u.userId}".format(u=u))
                    context.status_code = 200
                    sessionId = self.sessions_known.append(Session(u.userId, 1800, time.time()))
                    return json.dumps({"userId": u.userId, "sessionId": sessionId, "ttl": 1800})
                else:  # wrong password, bail out
                    mockserverlogger.warning("Correct username but invalid password (which is OK to say, because this is a mock)")
                    break
        context.status_code = 401
        return json.dumps({"errorMessage": "Invalid username or password.","errorCode": "FIELD_ERROR"})

    def session_timeout(self):
        """Reap any expired (TTL) sessions"""
        for sessionId in self.sessions_known:
            if (time.time() - self.sessions_known[sessionId].created) > self.sessions_known[sessionId].ttl:
                logging.warning("Session {0} expired".format(sessionId))
                del self.sessions_known[sessionId]

    def session_inspection_user_list(self):
        return set([usersession.userId for usersession in self.sessions_known.values()])

adapter = ServerMock()
adapter.prep()

def mock_server_with_authenticated_connection():
    connection = Connection("mockserver", auth=Credentials("admin", "password", "mock"))
    adapter = ServerMock()
    adapter.prep()
    connection._requestsession.mount('https://', adapter)
    return connection

def mock_server_with_authenticated_connection_and_bad_credentials():
    connection = Connection("mockserver", auth=Credentials("fakeuserthatdoesntexist", "", "mock"))
    adapter = ServerMock()
    adapter.prep()
    connection._requestsession.mount('https://', adapter)
    return connection


@pytest.mark.parametrize("connection,adapter", [
    (Connection("mockserver", auth=Credentials("fakeuserthatdoesntexist", "", "mock")), adapter),
    (Connection("li-latest.eng.vmware.com", auth=Credentials("fakeuserthatdoesntexist", "", "Local"), verify=False), None)
], ids=idfn)
class TestUnauthenticatedConnection():
    def test_authentication_param(self, connection, adapter):
        if adapter:
            connection._requestsession.mount('https://', adapter)

        with pytest.raises(Unauthorized) as excinfo:
            print(connection._get("/sessions/current"))

import pytest
@pytest.mark.parametrize("connection,adapter", [
    (Connection("mockserver", auth=Credentials("admin", "password", "mock")), adapter),
    (Connection("li-latest.eng.vmware.com", auth=Credentials("admin", "VMware123!", "Local"), verify=False), None)
])
class TestAuthenticatedConnection():
    def test_authentication_repeated(self, connection, adapter):
        """
        Mock /sessions and a fake /demand_auth resource.
        Force an HTTP 401 response on EVERY request for the protected /demand_auth resource.
        The AuthorizationHeaderAuthentication should request /demand_auth, observe a HTTP 401, login, & retry the request,
        but then give up.
        """
        if adapter:
            connection._requestsession.mount('https://', adapter)


        licenseobject = LicenseKeys(connection, "/licenses")

        assert len(licenseobject) == 1  # server/fixture knows about one existing (fake) license key
        k = list(licenseobject.keys())
