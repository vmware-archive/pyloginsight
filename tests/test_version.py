import pytest
from pyloginsight.models import Version, Server
from distutils.version import StrictVersion


def test_version_attributes(connection):
    remoteversionobject = Version.from_server(connection)
    assert remoteversionobject.release_name

def test_version_dict(connection):
    remoteversionobject = Version.from_server(connection)
    for expecteddictentry in ["releaseName"]:
        assert expecteddictentry in remoteversionobject._raw



def test_version_not_slicable(connection):
    remoteversionobject = Version.from_server(connection)
    with pytest.raises(TypeError):  # dynamic properties are not slice-accessible; that's reserved for the collections mixins
        discard = remoteversionobject["releaseName"]


def test_version_not_iterable(connection):
    remoteversionobject = Version.from_server(connection)
    with pytest.raises(TypeError):
        for _ in remoteversionobject:
            discard = _


def test_server_dot_version_directly_produces_populated_StrictVersion(connection):
    """Verify that a version number is accessible without correct/any authentication"""
    s = connection.server
    version = s.version
    assert isinstance(version, Version)
    assert isinstance(version, StrictVersion)
    assert version > StrictVersion("0.0")
    print(version)
    assert hasattr(version, 'version')


def test_server_dot_version2_directly_produces_populated_StrictVersion(connection):
    """Verify that a version number is accessible without correct/any authentication"""
    s = connection.server
    version = s.version2
    assert isinstance(version, Version)
    assert isinstance(version, StrictVersion)
    assert version > StrictVersion("0.0")
    assert hasattr(version, 'version')
