import pytest
from pyloginsight.models import Version
from distutils.version import StrictVersion


def test_version_attributes(connection):
    remoteversionobject = Version.from_server(connection, "/version")
    assert remoteversionobject.release_name


def test_version_not_slicable(connection):
    remoteversionobject = Version.from_server(connection, "/version")
    with pytest.raises(TypeError):  # dynamic properties are not slice-accessible; that's reserved for the collections mixins
        discard = remoteversionobject["releaseName"]


def test_version_not_iterable(connection):
    remoteversionobject = Version.from_server(connection, "/version")
    with pytest.raises(TypeError):
        for _ in remoteversionobject:
            discard = _


def test_server_dot_version_is_a_StrictVersion(connection):
    """Verify that a version number is a normal StrictVersion object"""
    s = connection.server
    version = s.version
    assert isinstance(version, Version)
    assert isinstance(version, StrictVersion)
    assert version > StrictVersion("0.0")
    assert hasattr(version, 'version')
