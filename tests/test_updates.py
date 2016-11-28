# content of test_sample.py

import pytest
import requests_mock
from distutils.version import StrictVersion

from pyloginsight import updates


def test_upgrade_path():
    """Retrieve a mocked upgrade-path list consisting of 3.3.2 -> 3.6 -> 4.0. Verify available/highest"""
    with requests_mock.Mocker() as m:
        example_response = """
        {"metadata":{"count":2},"upgradePaths":[{"id":2072,"fromRelease":{"id":1049,"version":"3.6.0","major":3,"medium":6,"minor":0,"update":"","productId":88},"toRelease":{"id":2053,"version":"4.0.0","major":4,"medium":0,"minor":0,"update":"","productId":88},"footnotes":[],"compatible":"yes"},{"id":1903,"fromRelease":{"id":1064,"version":"3.3.2","major":3,"medium":3,"minor":2,"update":"","productId":88},"toRelease":{"id":1049,"version":"3.6.0","major":3,"medium":6,"minor":0,"update":"","productId":88},"footnotes":[],"compatible":"yes"}]}
        """
        m.get('https://simservice.vmware.com/api/v2/upgrade/product/88', text=example_response)

        assert updates.available("3.3.2") == StrictVersion("3.6")
        assert updates.highest() == StrictVersion("4.0")
        with pytest.raises(ValueError):
            updates.available("1.2")
        assert m.call_count == 3
