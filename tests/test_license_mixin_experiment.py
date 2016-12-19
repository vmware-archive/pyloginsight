import pytest
from pyloginsight.models import Server, AlternateLicenseKeys
import logging


logger = logging.getLogger(__name__)


def test_retrieve_license_list_demands_authentication(connection):
    MY_USER_ID = "012345678-9ab-cdef-0123-456789abcdef"

    # Invasive verification of mock-server state.
    # This test must be altered if it is to be used against a live server.
    mockserver = connection._requestsession.adapters['https://']

    previous_quantity = len(mockserver.sessions_known)

    assert mockserver.call_count == 0
    licenseobject = AlternateLicenseKeys(connection)
    assert len(licenseobject) == 1  # force a login

    assert mockserver.call_count == 3  # Three requests: /licenses=401, /sessions=200, /licenses=200

    assert len(mockserver.sessions_known) == previous_quantity + 1  # 1 logged in user, me
    assert MY_USER_ID in mockserver.session_inspection_user_list()
    assert MY_USER_ID == Server.copy_connection(connection).current_session['userId']


def test_append_license(connection):
    NEW_LICENSE_KEY = '12345-XXXXX-XXXXX-XXXXX-XXXXX'
    licenseobject = AlternateLicenseKeys(connection)
    previous_quantity = len(licenseobject)
    licenseobject.append(NEW_LICENSE_KEY)
    assert len(licenseobject) == previous_quantity + 1


def test_remove_first_license(connection):
    licenseobject = AlternateLicenseKeys(connection)
    previous_quantity = len(licenseobject)
    index = list(licenseobject.keys())[0]
    del licenseobject[index]
    assert len(licenseobject) == previous_quantity - 1


def test_remove_nonexistent_license(connection):
    licenseobject = AlternateLicenseKeys(connection)
    previous_quantity = len(licenseobject)
    with pytest.raises(KeyError):
        del licenseobject["0000"]
    assert len(licenseobject) == previous_quantity  # no change to number of license keys on server


def test_iterate_over_licenses(connection):
    licenseobject = AlternateLicenseKeys(connection)
    counter = 0
    for k, v in licenseobject.items():
        assert k == v.id
        assert hasattr(v, "licenseKey")
        counter += 1
    assert counter > 0
    assert counter == len(licenseobject)  # counting and length agree


def test_get_license_summary(connection):
    """Retrive license summary, verify it contains a `hasOsi` boolean"""
    licenseobject = AlternateLicenseKeys(connection)
    assert isinstance(licenseobject.asdict().get('hasOsi'), bool)
    assert isinstance(licenseobject()['hasOsi'], bool)
    assert isinstance(licenseobject.hasCpu, bool)
    assert isinstance(licenseobject.hasOsi, bool)


def test_ServerDictMixin_incompatible_with_ServerListMixin(connection):
    """Try (and fail) to use the ServerDictMixin and ServerListMixin together."""
    from pyloginsight.abstracts import ServerAddressableObject, ServerDictMixin, ServerListMixin

    class ImpossibleObject(ServerAddressableObject, ServerDictMixin, ServerListMixin):
        _baseurl = None
        pass

    with pytest.raises(TypeError):
        ImpossibleObject(None)
