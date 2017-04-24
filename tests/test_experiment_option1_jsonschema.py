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



class RemoteObjectProxy(object):
    """Base class for a remote object. Such an object has a URL, but the object gets to declare its own expected properties."""
    #_url = None  # TODO: Causes test_set_attribute_under_context_with_exception to fail
    #_connection = None

    _baseobject = None
    _connection = None

    __masked_properties = ["_connection", "_url", "_baseobject"]

    def __init__(self, **kwargs):

        self._extended_properties['_connection'] = "a"
        self._extended_properties.extend('_url')

        print("aaaa", self.__object_attr_list__)
        self._url = url

        raise RuntimeError("Not Possible.")
        self._connection = connection

        super(RemoteObjectProxy, self).__init__(self, **kwargs)

    @classmethod
    def from_server(cls, connection, url):


        if not url:
            raise AttributeError("Cannot retrieve object from server without a url")
        if not connection:
            raise AttributeError("Cannot retrieve object from server without a Connection object")
        print("Attempt to make a cls", cls, "with url",url,", connection",connection, "data")
        data = connection.get(url)
        print("data", data)
        instance = cls(**data)
        print("got instance", instance)
        instance._url = url
        print("improved instance with url", instance)
        print("bbbb", instance.__object_attr_list__)
        instance._extended_properties['_connection'] = connection
        #instance._connection = connection
        return instance

    def to_server(self, connection, url=None):
        if url is None:
            url = str(self._url)
            if not url:
                raise AttributeError("Cannot submit object to server without a url")

        self.validate()
        logger.debug("About to PUT {}: {}".format(url, self.for_json()))
        response = connection.put(url, json=self.for_json())

    #def __setattr__(self, name, value):
    #    print("SetAttr", name, value)
    #    raise RuntimeError("Got a set attr")
    #    super(RemoteObjectProxy, self).__setattr__(name, value)

    def __enter__(self):
        if self._connection is None and self._extended_properties['_connection'] is None:
            print(self._extended_properties['_connection'])
            raise RuntimeError("Cannot use {0} as a content manager without a connection object.".format(self.__class__))
        url = str(self._url)
        if not url:
            raise AttributeError("Cannot submit object to server without a url")
        print("Entering __enter__")
        #self._context = self.__class__(url=self._url, **self.for_json())
        #self._context._connection = self._connection
        self._extended_properties['_cancelled'] = False
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        print("Entering __exit__")
        print("0. What is cancelled", self._extended_properties['_cancelled'], type(self._extended_properties['_cancelled']))
        if self._extended_properties['_cancelled']:
            print("1 Cannelled is true-ish!", self._extended_properties['_cancelled'])
        if self._extended_properties['_cancelled'] is False:
            print("2 Cannelled is false!", self._extended_properties['_cancelled'])

        if exc_type is not None:
            print("Exception")
            logger.warning("Dropping changes to {b} due to exception {e}".format(b=self._baseobject, e=exc_value))
        elif self._extended_properties['_cancelled']:
            print("3 Cancelled", self._extended_properties['_cancelled'])
            print("4 Cancelled is false?", self._extended_properties['_cancelled'] is False)
            logger.warning("Dropping changes to {b} due to cancellation".format(b=self._baseobject))
        else:
            print("to_server")
            self.to_server(self._connection or self._extended_properties['_connection'], self._url)


class ExampleObject(ExampleSchema, RemoteObjectProxy):
    """An example object that knows how to save itself to the server, but doesn't know who the server is"""


import wrapt


#class CustomProxy(wrapt.ObjectProxy):
#    def __setattr__(self, key, value):
#        raise RuntimeError("OK!")
#        print("Write!", key, value)
#        return self.__wrapped__.__setattr__(key, value)


#ExampleObject = CustomProxy(ExampleObject)


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
