


"""
There are two styles of server-side collections:

# A top-level key, containing a List of Dicts. This is very rare.

    {"many": [ {"id":123, "name":"Foo"} ]

# A top-level key, containing a Dict of Dicts. This is very common.

    {"many": {123: {"name":"Foo"} } }

And a predominant style of direct resource access

# A top-level key, containing a Dict

    {"single": {"id":123, "name":"Foo"} }

http://marshmallow.readthedocs.io/en/latest/extending.html#example-enveloping-revisited

"""

from marshmallow import Schema, fields, pre_load, post_dump, post_load

import pytest
import attrdict
import warnings
from collections import Mapping


@pytest.fixture
def list_from_server():
    return {'users': [{'id': "1234", 'name': 'Keith'}, {'id': "5678", 'name': 'Mick'}]}


@pytest.fixture
def dict_from_server():
    return {'users': {"1234": {'name': 'Keith'}, "5678": {'name': 'Mick'}}}


@pytest.fixture
def instance_from_server():
    return {'user': {
        'name': 'Keith',
        'email': 'keith@stones.com'
    }}

@pytest.fixture
def just_an_instance():
    return {
        'name': 'Keith',
        'email': 'keith@stones.com'
    }


class BaseSchema(Schema):
    # Custom options
    __envelope__ = {
        'single': None,
        'many': None
    }
    __model__ = None

    def get_envelope_key(self, many):
        """Helper to get the envelope key."""
        key = self.__envelope__['many'] if many else self.__envelope__['single']
        assert key is not None, "Envelope key undefined"
        return key


    @pre_load(pass_many=True)
    def unwrap_envelope(self, data, many):
        print("unwrap_envelope called with many=", many, "and data=", data)
        key = self.get_envelope_key(many)
        if many and key and isinstance(data[key], Mapping):
            # List-ify the collection, moving the key into the 'id' field
            def _f(x):
                if 'id' in x[1] and x[1]['id'] != x[0]:
                    warnings.warn("Object already had an 'id' property that differs from the key: {}".format(x))
                x[1]['id'] = x[0]
                return x[1]
            print("unwrap_envelope return style, new")
            return list(map(_f, data[key].items()))
            #r = data[key]
        else:
            print("unwrap_envelope return style, classic")
            r = data[key]
        print("unwrap_envelope returning", type(r), ":", r)
        return r

    @post_dump(pass_many=True)
    def wrap_with_envelope(self, data, many):
        key = self.get_envelope_key(many)
        return {key: data}

    @post_load
    def make_object(self, data):
        print("make_object called with", data)
        return self.__model__(**data)


class User(attrdict.AttrDict):
    pass

class UserSchema(BaseSchema):
    __envelope__ = {
        'single': 'user',
        'many': 'users',
    }
    __model__ = User
    id = fields.Str()
    name = fields.Str()
    email = fields.Email()


def test_example_enveloping_revisited_get_single_instance(instance_from_server):

    ser = UserSchema()
    user_dict = ser.load(instance_from_server).data

    assert 'email' in user_dict
    print(user_dict)


def test_example_enveloping_revisited_get_list_of_instances(list_from_server):

    ser = UserSchema()
    parse = ser.load(list_from_server, many=True)
    print(parse)
    user_objs = parse.data

    for user_dict in user_objs:
        assert 'name' in user_dict
        assert 'id' in user_dict
        print(user_dict)


def test_example_enveloping_revisited_get_dict_of_instances(dict_from_server):

    ser = UserSchema()
    parse = ser.load(dict_from_server, many=True)
    print(parse)
    user_objs = parse.data

    for user_dict in user_objs:
        assert 'name' in user_dict
        assert 'id' in user_dict
        print(user_dict)