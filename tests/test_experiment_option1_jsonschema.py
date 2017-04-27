from __future__ import print_function
import python_jsonschema_objects
import sys
import logging
import json


import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock
import requests
import json
import six
import attr



logger = logging.getLogger(__name__)


def make_class(schema, title):
    s4 = json.loads(schema)
    s4["title"] = title
    builder = python_jsonschema_objects.ObjectBuilder(s4)
    ns = builder.build_classes()
    return getattr(ns, title)


SCHEMA = '''{
                "$schema": "http://json-schema.org/draft-04/schema",
                "properties": {
                  "attribute": {
                      "type": "string"
                  }
                },
                "required": ["attribute"],
                "type": "object",
                "additionalProperties": true
              }'''

ExampleSchema = make_class(SCHEMA, "Example")


class Cancel(RuntimeError):
    """Update to server cancelled"""


class RemoteObjectProxy(object):
    """
    Base class for a remote object. Such an object has a URL, but the object gets to declare its own expected properties.

    Compatible with objects based on both Attribs and Python-JsonSchema-Objects
    """

    __connection = None
    __url = None

    @classmethod
    def from_server(cls, connection, url):
        body = connection.get(url)
        self = cls(**body)

        # Can't access directly, as validator borrows the setattr/getattribute interface.
        object.__setattr__(self, "__connection", connection)
        object.__setattr__(self, "__url", url)
        return self

    def __serialize(self):
        if hasattr(self, "validate"):
            self.validate()
        if hasattr(self, "for_json"):
            return self.for_json()
        return attr.asdict(self)

    def to_server(self, connection, url=None):

        if url is None:
            url = str(object.__getattribute__(self, "__url"))
            if url is None:
                raise AttributeError("Cannot submit object to server without a url")

        return connection.put(url, json=self.__serialize())

    def __enter__(self):
        connection = object.__getattribute__(self, "__connection")
        if connection is None:
            raise RuntimeError("Cannot use {0} as a content manager without a connection object.".format(self.__class__))
        url = str(self.__url)
        if not url:
            raise AttributeError("Cannot submit object to server without a url")
        # Consider returning a deep copy.
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            if exc_type == Cancel:
                return True
            logger.warning("Dropping changes to {b} due to exception {e}".format(b=self, e=exc_value))

        else:
            connection = object.__getattribute__(self, "__connection")
            self.to_server(connection, self.__url)


class ExampleObject(ExampleSchema, RemoteObjectProxy):
    """An example object that knows how to save itself to the server, but doesn't know who the server is"""


def test_make_empty_object():
    #    with pytest.raises(TypeError):
    failed_object = ExampleObject()

    okobject = ExampleObject(attribute="foo")
    assert okobject.attribute == 'foo'


def test_get_attribute(connection):

    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    x = original_object.attribute

    assert x == "value"



def test_set_attribute_and_write(connection):
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert original_object.attribute != "newname"
    original_object.attribute = "newname"

    original_object.to_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    new_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert new_object.attribute == "newname"


def test_set_attribute_under_context(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with original_object as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"

def test_set_attribute_under_context_with_exception_should_not_write(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with pytest.raises(RuntimeError):
        with original_object as w:
            w.attribute = "5"
            raise RuntimeError

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "value"


def test_two_instances_compare(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert original_object == second_object

    second_object.attribute = "changed"

    assert original_object != second_object


def test_instance_repr(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    x = repr(original_object)

    assert "ExampleObject" in x
    assert "url" not in x
    assert "12345678-90ab-cdef-1234-567890abcdef" not in x


def test_instance_dir(connection):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    print(original_object)
    print(dir(original_object))

    assert 'attribute' in str(original_object)
    assert 'connection' not in str(original_object)
