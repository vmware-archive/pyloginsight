#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function


import pytest
from pyloginsight.models import Dataset, Datasets
import uuid


def test_get_nonexistant(connection):

    # the fake key we're trying to fetch really doesn't exist
    for guid, license in connection.server.datasets.items():
        assert guid != "000000000-000-0000-0000-000000000000"

    with pytest.raises(KeyError):
        _ = connection.server.datasets["000000000-000-0000-0000-000000000000"]


def test_setitem(connection):
    datasets = connection.server.datasets
    with pytest.raises(NotImplementedError):
        datasets['7c677664-e373-456d-ba85-6047dfc84452'] = 'raspberry'


def test_remove_nonexistant(connection):

    previous_quantity = len(connection.server.datasets)

    # the fake key we're trying to delete really doesn't exist
    for guid, item in connection.server.datasets.items():
        assert isinstance(guid, (u"".__class__, "".__class__))
        assert isinstance(item, Dataset)
        assert guid != "000000000-000-0000-0000-000000000000"

    with pytest.raises(KeyError):
        del connection.server.datasets["000000000-000-0000-0000-000000000000"]
    assert len(connection.server.datasets) == previous_quantity  # no change to number of license keys on server


def test_iterate_all_datasets_by_key(connection):
    count = 0
    for dataset_key in connection.server.datasets:
        count += 1
        print(dataset_key)

    assert count == len(connection.server.datasets)


def test_collection_callable(connection):
    d = Datasets(connection)

    called = d()

    print("type(d)", type(d), d)
    print("type(called)", type(called), called)


def test_iterate_all_datasets_on_server(connection):
    count = 0
    for dataset_key, dataset in connection.server.datasets.items():
        count += 1
        print(dataset_key)
        assert isinstance(dataset, Dataset)
        print(dataset)

    assert count == len(connection.server.datasets)


def test_append_and_delete(connection):
    name = "testdataset-" + str(uuid.uuid4())

    original_quantity = len(connection.server.datasets)

    dataset = Dataset(name=name, description='mydescription', field='hostname', value='esx*', constraints=[{'value': 'vobd', 'hidden': False, 'name': '__li_source_path', 'fieldType': 'STRING', 'operator': 'CONTAINS'}])
    assert 'id' not in dataset

    new_object_guid = connection.server.datasets.append(dataset)
    print("new_object_guid", new_object_guid)

    assert '-' in new_object_guid

    refetch_object = connection.server.datasets[new_object_guid]
    print("refetch_object", refetch_object)

    assert len(connection.server.datasets) == original_quantity + 1

    del connection.server.datasets[new_object_guid]

    # Back to starting point
    assert len(connection.server.datasets) == original_quantity
