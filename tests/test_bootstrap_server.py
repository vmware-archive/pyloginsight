# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest
from pyloginsight.exceptions import AlreadyBootstrapped


@pytest.mark.sideeffects
@pytest.mark.tryfirst
def test_bootstrap_and_license_server(connection, licensekey):

    try:
        connection.bootstrap(email="testbootstrapped@localhost")
    except AlreadyBootstrapped:
        print("Already Bootstrapped")

    connection.wait_until_started()

    if 'ACTIVE' != connection.server.license.licenseState:
        connection.server.license.append(str(licensekey))
    else:
        print("Already Licensed")
