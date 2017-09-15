# -*- coding: utf-8 -*-

"""
Verify consistent behavior of all server collection classes
"""

import pytest
import inspect
import collections
import json

from pyloginsight import models
from pyloginsight import abstracts

print(dir(models))


collection_classes = [cls for cls in
                      [object.__getattribute__(models, classname) for classname in dir(models) if classname[-1] == 's']
                      if inspect.isclass(cls)]


@pytest.fixture(params=collection_classes)
def collection_class(request):
    """A Collection class from pyloginsight.models, like Roles, Datasets, Users, etc"""
    return request.param


def test_collections_have_length(connection, collection_class):
    """Can invoke len(collection) and produce a number."""
    collection = collection_class(connection)

    assert isinstance(collection, collections.Sized)
    assert len(collection) >= 0


def test_iterate_by_key(connection, collection_class):
    """Can iterate over a collection using `for key in collection`."""
    collection = collection_class(connection)

    count = 0
    for key in collection:
        count += 1
        assert isinstance(key, str) or isinstance(key, int)
        assert key in collection

    assert count == len(collection)


def test_iterate_by_items(connection, collection_class):
    """When enumerating over an instance of a collection class, we get back objects that are a instance of collection_class._single"""
    Single = collection_class._single
    collection = collection_class(connection)

    count = 0
    for key, value in collection.items():
        count += 1
        assert isinstance(key, str) or isinstance(key, int)
        assert isinstance(value, Single)
        assert key in collection

    assert count == len(collection)


def test_callable(connection, collection_class):
    """A collection is callable, and produces a collections.Mapping produced from JSON without marshalling to higher-order objects."""
    collection = collection_class(connection)

    assert isinstance(collection, abstracts.ServerAddressableObject)

    result = collection()

    assert isinstance(collection, collections.Iterable)
    assert isinstance(result, collections.Mapping)

    # The mapping is composed entirely of primative datatypes, which means
    # the value can always be round-tripped to/from JSON again directly.
    assert result == json.loads(json.dumps(result))


def test_get_nonexistant(connection, collection_class):
    """Trying to retrieve a non-existent item from a collection produces a KeyError."""
    collection = collection_class(connection)

    # Be certain that the fake key we're trying to fetch really doesn't exist.
    for key, value in collection.items():
        assert key != "000000000-000-0000-0000-000000000000"

    with pytest.raises(KeyError):
        _ = collection["000000000-000-0000-0000-000000000000"]


def test_nonexistant_is_not_in_collection(connection, collection_class):
    """Can use `item in collection` to determine collection membership."""
    collection = collection_class(connection)

    # Be certain that the fake key we're trying to fetch really doesn't exist.
    for key, value in collection.items():
        assert key != "000000000-000-0000-0000-000000000000"

    assert "000000000-000-0000-0000-000000000000" not in collection
