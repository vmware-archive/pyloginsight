import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock
from pyloginsight.atomic import *
import requests
import attr

@attr.s
class ExampleObject(object):
    """
    An object contains full content as attributes, and its identity (url).
    """

    attribute = attr.ib()
    id = attr.ib(default=None)
    _url = attr.ib(default=None)


    @classmethod
    def from_server(cls, connection, url):
        body = connection.get(url)
        print("Got a body", body)
        return cls(url=url, **body)

    def to_server(self, connection, url=None):
        if url is None:
            url = self._url

        body = attr.asdict(self)
        del body['_url']
        print("Writing body {body} to url {url}".format(body=body, url=url))
        response = connection.put(url, json=body)
        return response




def test_make_empty_object():
    with pytest.raises(TypeError):
        failed_object = ExampleObject()

    okobject = ExampleObject(attribute="foo")
    assert okobject.attribute == 'foo'

def test_get_attribute(connection):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    print("original_object", original_object)

    assert original_object is not None

    x = original_object.attribute
    assert x == 'value'


def test_set_attribute(connection):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    print(original_object)

    x = original_object.attribute
    original_object.attribute = 5
    assert x is not original_object.attribute  # The attribute value has been replaced

    original_object.to_server(connection)  # Write

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == 5


def test_set_attribute_under_context(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with connection.write(original_object) as w:
        w.attribute = 5

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == 5

def test_set_attribute_under_context_raw(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with connection.write(original_object) as w:
        original_object.attribute = 5

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == 5
