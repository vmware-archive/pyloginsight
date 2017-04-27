import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock
import requests
import attr
import logging
from test_experiment_option1_jsonschema import RemoteObjectProxy, Cancel


logger = logging.getLogger(__name__)


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
