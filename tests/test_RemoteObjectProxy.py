from __future__ import print_function
import logging
import pytest
import json
import attr
import datetime

from mock_loginsight_server import MockedConnection
from pyloginsight.abstracts import RemoteObjectProxy, make_class

import attrdict

from marshmallow import Schema, fields


pytestmark = pytest.mark.exampleapi  # Cannot succeed against a real server

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



class ExampleObjectMarshmallow(RemoteObjectProxy, attrdict.AttrDict):
    class MarshmallowSchema(Schema):
        attribute = fields.Str()
        id = fields.Str()
        datetime = fields.DateTime()
        timedelta = fields.TimeDelta(precision='microseconds')
        defaultseven = fields.Integer(missing=7)


# Can add ExampleObjectJson, ExampleObjectAttribs to the params list to exercise more tests.
@pytest.fixture(params=[ExampleObjectMarshmallow])
def ExampleObject(request):
    """A DAO class under scrutiny."""
    return request.param


def test_make_empty_object(ExampleObject):
    failed_object = ExampleObject()

    okobject = ExampleObject(attribute="foo")
    assert okobject.attribute == 'foo'


def mockonly(f):
    def wraps(connection, ExampleObject):
        if not isinstance(connection, MockedConnection):
            pytest.skip("Test only applies to a MockedConnection")
        return f(connection, ExampleObject)
    return wraps

@mockonly
def test_get_attribute(connection, ExampleObject):
    print("Running against connection", id(connection))
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    x = original_object.attribute
    assert x == "value"


@mockonly
def test_object_serializes_to_json(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    print(original_object)
    print(original_object._serialize())
    dict_representation = json.loads(json.dumps(original_object._serialize()))
    assert dict_representation['attribute'] == 'value'


@mockonly
def test_set_attribute_and_write(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    original_object.attribute += "5"

    original_object.to_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    new_object = ExampleObject.from_server(connection=connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert new_object.attribute == original_object.attribute


@mockonly
def test_set_attribute_under_context(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with original_object as w:
        w.attribute = "5"

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "5"


@mockonly
def test_set_attribute_under_context_with_exception_should_not_write(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    with pytest.raises(RuntimeError):
        with original_object as w:
            w.attribute = "5"
            raise RuntimeError

    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert second_object.attribute == "value"


@mockonly
def test_two_instances_compare(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    assert original_object == second_object

    second_object.attribute = "changed"

    assert original_object != second_object


@mockonly
def test_instance_repr(connection, ExampleObject):

    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    x = repr(original_object)

    assert "ExampleObject" in x
    assert "url" not in x
    assert "12345678-90ab-cdef-1234-567890abcdef" not in x


@mockonly
def test_instance_dir(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")

    print(original_object)
    print(dir(original_object))

    assert 'attribute' in str(original_object)
    assert 'connection' not in str(original_object)


@mockonly
def test_instances_ignore_extra_attributes_from_server(connection, ExampleObject):
    o = ExampleObject.from_server(connection, url="/example/uuid-of-object-with-extra-attribute")
    assert 'extraattribute' not in repr(o)


@mockonly
def test_instances_dont_send_extra_attributes_to_server(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    print(original_object)
    assert 'bogusattribute' not in repr(original_object)

    with original_object as w:
        w.bogusattribute = "5"

    print(original_object)
    second_object = ExampleObject.from_server(connection, url="/example/12345678-90ab-cdef-1234-567890abcdef")
    assert 'bogusattribute' not in repr(second_object)


@mockonly
def test_instances_from_server_deserialize_datetime(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/object-with-a-datetime")
    print(original_object)

    assert isinstance(original_object.datetime, datetime.datetime)
    assert original_object.timedelta == datetime.timedelta(minutes=6)


@mockonly
def test_instances_from_server_have_defaults(connection, ExampleObject):
    original_object = ExampleObject.from_server(connection, url="/example/object-with-a-datetime")
    print(original_object)

    assert isinstance(original_object.defaultseven, int)
    assert original_object.defaultseven == 7
