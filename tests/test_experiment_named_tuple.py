import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock
from pyloginsight.atomic import *
import requests
import json
from collections import namedtuple
import logging


logger = logging.getLogger(__name__)

RawObject = namedtuple("RawObject", ["attribute"])

class ExampleObject(object):
    """
    An object's only state is its identity. Aka the URL.
    All its attributes are really behaviors (e.g., get name, set name)
    fronting HTTP requests.
    """

    _obj = None
    _connection = None
    _url = None

    @classmethod
    def from_server(cls, connection, url):
        """Shim for compatibility with sibling experiments"""
        return cls(connection=connection, url=url)

    def to_server(self, connection, url=None):
        if url is None:
            url = str(self._url)
            if url == "":
                raise AttributeError("Cannot submit object to server without a url")

        response = connection.put(url, json=self._asdict())

    def __init__(self, connection=None, url=None, default=None):
        object.__setattr__(self, "_connection", connection)
        object.__setattr__(self, "_url", url)

        object.__setattr__(self, "_obj", RawObject(default))  # passing a dictionary to the namedtuple constructor
        if url and connection and not default:
            body = connection.get(url)
            print("body", body, RawObject)
            for k in [k for k in body.items() if k not in self._obj._fields]:
                logger.debug("Ignoring unknown field {k}".format(k=k))
            only_known_fields = {k:v for k, v in body.items() if k in self._obj._fields}

            object.__setattr__(self, "_obj", RawObject(**only_known_fields))  # passing a dictionary to the namedtuple constructor

    # Delegates
    def __getattr__(self, item):
        return getattr(self._obj, item)

    def __setattr__(self, item, value):
        return setattr(self._obj, item, value)

    def _replace(self, **kwargs):
        newrawobj = self._obj._replace(**kwargs)
        print("Making a copy of {self} with kwargs {kwargs}: {newrawobj}".format(self=self, kwargs=kwargs, newrawobj=newrawobj))
        return self.__class__(self._connection, self._url, newrawobj)

    def _asdict(self):
        return self._obj._asdict()
    def _raw(self):
        return self._obj

    def __repr__(self):
        return repr(self._obj)


def test_get_attribute(connection):
    original_object = ExampleObject(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    print("original_object", original_object)

    assert original_object is not None

    x = original_object.attribute
    assert x == 'value'


def test_set_attribute_local(connection):
    original_object = ExampleObject(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    print(original_object)

    x = original_object.attribute

    with pytest.raises(AttributeError):
        original_object.attribute = 5

    newobject = original_object._replace(attribute=4)

    assert newobject.attribute != original_object.attribute
    r = RawObject


def test_set_attribute_under_context(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert original_object is not None

    with connection.write(original_object) as w:
        w.attribute = 5

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == 5


def test_set_attribute_under_context_raw(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert original_object is not None

    with connection.write(original_object) as w:
        w._replace(attribute=5)

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == 5
