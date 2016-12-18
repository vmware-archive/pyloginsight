import pytest
from functools import wraps
from pyloginsight.connection import Credentials
from pyloginsight.models import Server, LicenseKeys
import requests_mock


SUCCESSFUL_LOGIN_JSON = '{"userId":"012345678-9ab-cdef-0123-456789abcdef","sessionId":"hNhXgA","ttl":1800}'
LICENSE_LIST_JSON = '{"hasOsi": true, "limitedLicenseCapabilities": ["QUERY", "RBAC", "UPGRADE", "ACTIVE_DIRECTORY", "CONTENT_PACK"], "standardLicenseCapabilities": ["FORWARDING", "RBAC", "UPGRADE", "CUSTOM_SSL", "ACTIVE_DIRECTORY", "CONTENT_PACK", "VSPHERE_FULL_SUPPORT", "CLUSTER", "IMPORT_CONTENT_PACKS", "QUERY", "ARCHIVE", "THIRD_PARTY_CONTENT_PACKS"], "maxCpus": 0, "uninitializedLicenseCapabilities": ["RBAC", "ACTIVE_DIRECTORY", "CONTENT_PACK"], "hasCpu": false, "maxOsis": 0, "licenseState": "ACTIVE", "licenses": {"12345678-90ab-cdef-1234-567890abcdef": {"infinite": true, "configuration": "1 Operating System Instance (OSI)", "status": "Active", "expiration": 0, "licenseKey": "4J2TK-XXXXX-XXXXX-XXXXX-XXXXX", "count": 0, "error": "", "typeEnum": "OSI", "id": "12345678-90ab-cdef-1234-567890abcdef"}}, "hasTap": false}'
NEW_LICENSE_KEY = 'M502V-XXXXX-XXXXX-XXXXX-XXXXX'
EXISTING_LICENSE_UUID = "12345678-90ab-cdef-1234-567890abcdef"


@pytest.fixture
def adapter():
    mockadapter = requests_mock.Adapter()
    return mockadapter


@pytest.fixture
def connection():
    credentials = Credentials(username="admin", password="pass", provider="mock")
    connection = Server("mockserverlocal", auth=credentials)
    return connection


@pytest.fixture
def authenticatedconnection():
    credentials = Credentials(username="admin", password="pass", provider="mock")
    connection = Server("mockserverlocal", auth=credentials)
    connection._requestsession.mount('https://', adapter)
    connection._get("/sessions/current")
    return connection


def requiresauthentication(fn):
    """Server mock; fail any request which does not contain the expected Authorization header with HTTP/401.
    Designed to be used as a `@requiresauthentication` decorator"""
    @wraps(fn)
    def wrapper(request, context):
        if request.headers.get('Authorization') != 'Bearer hNhXgA':
            context.status_code = 401
            return ""
        return fn(request, context)
    return wrapper


def test_retrieve_license_list_requires_authentication(adapter, connection):
    adapter_sessions = adapter.register_uri('POST',
                                            '/api/v1/sessions',
                                            text=SUCCESSFUL_LOGIN_JSON,
                                            status_code=200)

    @requiresauthentication
    def callback_list_license(request, context):
        return LICENSE_LIST_JSON

    license_list = adapter.register_uri('GET',
                                        '/api/v1/licenses',
                                        status_code=200,
                                        text=callback_list_license)

    connection._requestsession.mount('https://', adapter)

    licenseobject = LicenseKeys(connection, "/licenses")
    assert license_list.call_count == 0  # merely taking the reference doesn't require a server connection
    assert len(licenseobject) == 1  # server/fixture knows about one existing license key
    assert license_list.call_count == 2  # one request received a HTTP/401, second HTTP/200 and a payload
    assert adapter_sessions.call_count == 1  # we had to login
