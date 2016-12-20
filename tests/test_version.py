import pytest
from pyloginsight.models import Version, Server
from distutils.version import StrictVersion


def test_version_attributes(connection):
    remoteversionobject = Version(connection)
    for expectedproperty in ["releaseName", "raw", "asdict"]:
        assert hasattr(remoteversionobject, expectedproperty)


def test_version_dict(connection):
    remoteversionobject = Version(connection)
    for expecteddictentry in ["releaseName"]:
        assert expecteddictentry in remoteversionobject.asdict()

    # dynamic properties provided by __dir__ and __getattr__, so dict() and hasattr() agree
    for key in remoteversionobject.asdict().keys():
        assert hasattr(remoteversionobject, key)


def test_version_callable(connection):
    # Calling the Version object populates it with server content
    remoteversionobject = Version(connection)
    assert callable(remoteversionobject)
    assert not isinstance(remoteversionobject.version, tuple)
    remoteversionobject()
    assert isinstance(remoteversionobject.version, tuple)
    assert remoteversionobject > StrictVersion("0.0")


def test_version_not_slicable(connection):
    remoteversionobject = Version(connection)
    with pytest.raises(TypeError):  # dynamic properties are not slice-accessible; that's reserved for the collections mixins
        discard = remoteversionobject["releaseName"]


def test_version_not_iterable(connection):
    remoteversionobject = Version(connection)
    with pytest.raises(TypeError):
        for _ in remoteversionobject:
            discard = _


def test_server_dot_version_directly_produces_populated_StrictVersion(all_credential_connection):
    """Verify that a version number is accessible without correct/any authentication"""
    s = Server.copy_connection(all_credential_connection)
    version = s.version
    assert isinstance(version, Version)
    assert isinstance(version, StrictVersion)
    assert version > StrictVersion("0.0")
    assert hasattr(version, 'version')
