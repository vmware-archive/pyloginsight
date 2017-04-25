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
    """Base class for a remote object. Such an object has a URL, but the object gets to declare its own expected properties."""
    #_url = None  # TODO: Causes test_set_attribute_under_context_with_exception to fail

    _connection = None

    #__masked_properties = ["_connection", "_url"]


    @classmethod
    def from_server(cls, connection, url):
        body = connection.get(url)
        self = cls(**body)
        self._extended_properties['_connection'] = connection
        self._extended_properties['_url'] = url
        return self

    def to_server(self, connection, url=None):
        if url is None:
            url = str(self._url)
            if not url:
                raise AttributeError("Cannot submit object to server without a url")

        self.validate()
        logger.debug("About to PUT {}: {}".format(url, self.for_json()))
        response = connection.put(url, json=self.for_json())

    def __enter__(self):
        if self._extended_properties['_connection'] is None:
            raise RuntimeError("Cannot use {0} as a content manager without a connection object.".format(self.__class__))
        url = str(self._url)
        if not url:
            raise AttributeError("Cannot submit object to server without a url")
        print("Entering __enter__")
        #self._context = self.__class__(url=self._url, **self.for_json())
        #self._context._connection = self._connection
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            if exc_type == Cancel:
                return True
            logger.warning("Dropping changes to {b} due to exception {e}".format(b=self, e=exc_value))

        else:
            self.to_server(self._extended_properties['_connection'], self._url)


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

    with connection.write(original_object, url="/example/12345678-90ab-cdef-1234-567890abcdef") as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"


def test_set_attribute_under_context_with_automatic_url(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with connection.write(original_object) as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"


def test_set_attribute_under_context_provided_by_object(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with original_object as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"

def test_set_attribute_under_context_with_exception_should_not_write(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with pytest.raises(RuntimeError):
        with connection.write(original_object) as w:
            original_object.attribute = "5"
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
    assert "url" in x
    assert "12345678" in x
