#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function


import pytest
import requests_mock
from pyloginsight.models import Dataset, Datasets
import uuid


GET_DATASETS_200 = '{"dataSets":[{"id":"7c677664-e373-456d-ba85-6047dfc84452","name":"vobd","description":"Events from the vobd daemon on ESXi","type":"OR","constraints":[{"name":"appname","operator":"CONTAINS","value":"vobd","fieldType":"STRING","hidden":false}]}]}'
POST_DATASETS_400 = '{"errorMessage":"Some fields have incorrect values","errorCode":"FIELD_ERROR","errorDetails":{"name":[{"errorCode":"com.vmware.loginsight.api.errors.field_value_should_be_one_of","errorMessage":"Value should be one of (appname,hostname,procid,__li_source_path,vc_details,vc_event_type,vc_username,vc_vm_name)","errorParams":["appname","hostname","procid","__li_source_path","vc_details","vc_event_type","vc_username","vc_vm_name"]}]}}'
POST_DATASETS_201 = '{"dataSet":{"id":"084ba074-53e7-434f-b6bb-253d1695c084","name":"test2","description":"test2","type":"OR","constraints":[{"name":"hostname","operator":"CONTAINS","value":"esx*","fieldType":"STRING","hidden":false}]}}'
DELETE_DATASETS_200 = ''
DELETE_DATASETS_400 = '{"errorMessage":"Specified data set does not exist.","errorCode":"RBAC_DATASETS_ERROR","errorDetails":{"errorCode":"com.vmware.loginsight.api.errors.rbac.dataset_does_not_exist"}}'
DELETE_DATASETS_400_2 = '{"errorMessage":"Bad request received (Cannot parse parameter dataSetId as UUID: Invalid UUID string: raspberry): DELETE /api/v1/datasets/raspberry"}'


adapter = requests_mock.Adapter()
adapter.register_uri('GET', 'https://mockserver:9543/api/v1/datasets', text=GET_DATASETS_200, status_code=200)
adapter.register_uri('POST', 'https://mockserver:9543/api/v1/datasets', text=POST_DATASETS_400, status_code=400)
adapter.register_uri('POST', 'https://mockserver:9543/api/v1/datasets', text=POST_DATASETS_201, status_code=201)
adapter.register_uri('DELETE', 'https://mockserver:9543/api/v1/datasets/7c677664-e373-456d-ba85-6047dfc84452', text=DELETE_DATASETS_200, status_code=200)
adapter.register_uri('DELETE', 'https://mockserver:9543/api/v1/datasets/00000000-0000-0000-0000-000000000050', text=DELETE_DATASETS_400, status_code=400)
adapter.register_uri('DELETE', 'https://mockserver:9543/api/v1/datasets/raspberry', text=DELETE_DATASETS_400_2, status_code=400)


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
        assert isinstance(guid, str)
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
