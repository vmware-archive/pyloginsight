# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest
from pyloginsight.models import LicenseKeys
import logging


logger = logging.getLogger(__name__)


def first_active_license_key(licenses):
    for guid, license in licenses.items():
        print("Considering license guid", guid, "with payload", license)
        if license.status == 'Active':
            return (guid, license.licenseKey)
        print("Skipping non-active license", license)
    return None


@pytest.mark.sideeffects
def test_remove_first_license_and_re_add_it_again(connection):
    licenseobject = LicenseKeys(connection)
    previous_quantity = len(licenseobject)

    assert previous_quantity > 0  # The server should already have a license key - we're going to try removing it

    (guid, key) = first_active_license_key(licenseobject)
    print("Retrieved license key", guid, key)

    # Remove the key from the server; server may become unlicensed at this point
    del licenseobject[guid]

    # Which reduced the quantity by 1
    assert len(licenseobject) == previous_quantity - 1

    # Re-add key, will get a new url-fragment guid assigned
    r = licenseobject.append(key)
    assert isinstance(r, str)
    assert r != guid

    # Same quantity now as before
    assert len(licenseobject) == previous_quantity


def test_remove_nonexistent_license(connection):
    licenseobject = LicenseKeys(connection)
    previous_quantity = len(licenseobject)

    # the fake key we're trying to delete really doesn't exist
    for guid, license in licenseobject.items():
        assert license != "000000000-000-0000-0000-000000000000"

    with pytest.raises(KeyError):
        del licenseobject["000000000-000-0000-0000-000000000000"]
    assert len(licenseobject) == previous_quantity  # no change to number of license keys on server


def test_iterate_over_licenses(connection):
    licenseobject = LicenseKeys(connection)

    counter = 0
    for k, v in licenseobject.items():
        assert k == v.id
        assert hasattr(v, "licenseKey")
        print(v)
        counter += 1
    assert counter > 0  # There should be at least one existing license key on the server
    assert counter == len(licenseobject)  # counting and length agree


def test_get_license_summary(connection):
    """Retrive license summary, verify it contains a `hasOsi` boolean"""
    licenseobject = LicenseKeys(connection)
    assert isinstance(licenseobject.asdict().get('hasOsi'), bool)
    assert isinstance(licenseobject()['hasOsi'], bool)
    assert isinstance(licenseobject.hasCpu, bool)
    assert isinstance(licenseobject.hasOsi, bool)
