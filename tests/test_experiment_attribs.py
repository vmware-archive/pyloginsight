import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock
import requests
import attr
import logging


logger = logging.getLogger(__name__)


class Cancel(RuntimeError):
    """Update to server cancelled"""


class RemoteObjectProxy(object):
    __connection = None

    @classmethod
    def from_server(cls, connection, url):
        body = connection.get(url)
        obj = cls(**body)
        obj.__connection = connection
        obj.__url = url
        return obj

    def to_server(self, connection, url=None):
        """
        Default implementation writing to server with HTTP PUT at origin URL.
        For alternate implementations, subclass and override.
        """
        if url is None:
            url = self.__url

        return connection.put(url, json=attr.asdict(self))


    def __enter__(self):
        if self.__connection is None:
            raise RuntimeError("Cannot use {0} as a content manager without a connection object.".format(self.__class__))
        url = str(self.__url)
        if not url:
            raise AttributeError("Cannot submit object to server without a url")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            if exc_type == Cancel:
                return True
            logger.warning("Dropping changes to {b} due to exception {e}".format(b=self, e=exc_value))
        else:
            self.to_server(self.__connection, self.__url)


@attr.s
class ExampleObject(RemoteObjectProxy):
    """
    An object contains full content as attributes, and its identity (url).
    """
    attribute = attr.ib()
    id = attr.ib(default=None)


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


@pytest.mark.xfail(reason="Implementation doesn't copy yet.", run=True)
def test_set_attribute_on_copy(connection):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert original_object.attribute != 5

    with connection.write(original_object) as w:
        original_object.attribute = 5

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute != 5


def test_set_attribute_under_context_provided_by_object(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with original_object as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"


def test_set_attribute_under_context_with_exception_should_not_write(connection):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with pytest.raises(RuntimeError):
        with original_object as w:
            w.attribute = 5
            raise RuntimeError

    with original_object as w:
        w.attribute = 5
        raise Cancel

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "value"


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
