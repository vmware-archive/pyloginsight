from __future__ import print_function
import python_jsonschema_objects
import sys
import logging
import json


import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock
from pyloginsight.atomic import *
import requests
import json
import six



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



class RemoteObjectProxy(object):
    """Base class for a remote object. Such an object has a URL, but the object gets to declare its own expected properties."""

    def __init__(self, url=None, **kwargs):
        self._url = url
        super(RemoteObjectProxy, self).__init__(self, **kwargs)

    @classmethod
    def from_server(cls, connection, url):
        instance = cls(**connection.get(url))
        instance._url = url
        return instance

    def to_server(self, connection, url=None):
        if url is None:
            url = str(self._url)
            if url == "":
                raise AttributeError("Cannot submit object to server without a url")

        self.validate()
        response = connection.put(url, json=self.for_json())

    def __setattr__(self, name, value):
        print("SetAttr", name, value)
        raise RuntimeError("Got a set attr")
        super(RemoteObjectProxy, self).__setattr__(name, value)


class ExampleObject(ExampleSchema, RemoteObjectProxy):
    """An example object that knows how to save itself to the server, but doesn't know who the server is"""


import wrapt

class CustomProxy(wrapt.ObjectProxy):
    def __setattr__(self, key, value):
        raise RuntimeError("OK!")
        print("Write!", key, value)
        return self.__wrapped__.__setattr__(key, value)


ExampleObject = CustomProxy(ExampleObject)


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

    with connection.atomic(original_object, url="/example/12345678-90ab-cdef-1234-567890abcdef") as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"


def test_set_attribute_under_context_with_automatic_url(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with connection.write(original_object) as w:
        original_object.attribute = "5"

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
