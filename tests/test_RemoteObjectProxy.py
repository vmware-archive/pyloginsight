from __future__ import print_function
import logging
import pytest
import json
import attr

from pyloginsight.abstracts import RemoteObjectProxy, make_class


logger = logging.getLogger(__name__)


SCHEMA = '''{
                "$schema": "http://json-schema.org/draft-04/schema",
                "properties": {
                  "attribute": {
                      "type": "string"
                  },
                  "id": {
                      "type": "string"
                  }
                },
                "required": ["attribute"],
                "type": "object",
                "additionalProperties": true
              }'''


# Both of these objects have the same structure: A single string attribute named "attribute".

class ExampleObjectJson(make_class(SCHEMA, "Example"), RemoteObjectProxy):
    """An example object, defined by the jsonschema-objects"""

@attr.s
class ExampleObjectAttribs(RemoteObjectProxy):
    """An example object, defined by attr.ibs"""
    attribute = attr.ib(str)
    id = attr.ib(default=None)


@pytest.fixture(params=[ExampleObjectJson, ExampleObjectAttribs])
def ExampleObject(request):
    return request.param


def test_make_empty_object(ExampleObject):
    failed_object = ExampleObject()

    okobject = ExampleObject(attribute="foo")
    assert okobject.attribute == 'foo'


def test_get_attribute(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    x = original_object.attribute
    assert x == "value"


def test_object_serializes_to_json(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    dict_representation = json.loads(json.dumps(original_object._serialize()))
    assert dict_representation['attribute'] == 'value'


def test_set_attribute_and_write(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    original_object.attribute += "5"

    original_object.to_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    new_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert new_object.attribute == original_object.attribute


def test_set_attribute_under_context(connection, ExampleObject):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with original_object as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"

def test_set_attribute_under_context_with_exception_should_not_write(connection, ExampleObject):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with pytest.raises(RuntimeError):
        with original_object as w:
            w.attribute = "5"
            raise RuntimeError

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "value"


def test_two_instances_compare(connection, ExampleObject):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert original_object == second_object

    second_object.attribute = "changed"

    assert original_object != second_object


def test_instance_repr(connection, ExampleObject):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    x = repr(original_object)

    assert "ExampleObject" in x
    assert "url" not in x
    assert "12345678-90ab-cdef-1234-567890abcdef" not in x


def test_instance_dir(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    print(original_object)
    print(dir(original_object))

    assert 'attribute' in str(original_object)
    assert 'connection' not in str(original_object)
