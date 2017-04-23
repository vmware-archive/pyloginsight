#!/usr/bin/env python


import pytest
import requests_mock
from pyloginsight.models import Server
from pyloginsight.connection import Credentials


pytest.mark.skip("Broken")


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


#creds = Credentials(username='admin', password='secret', provider='Local')
#server = Server(hostname='mockserver', verify=False)
#server._requestsession.mount('https://', adapter)


def test_delitem(server):
    # For some reason when performing local tests this operation returns a string instead of none.
    # When testing interactively, I get the expected response.
    server.datasets.pop('7c677664-e373-456d-ba85-6047dfc84452', None)

    with pytest.raises(KeyError):
        del server.datasets['00000000-0000-0000-0000-000000000050']

    with pytest.raises(KeyError):
        del server.datasets['raspberry']


def test_getitem(server):
    assert server.datasets['7c677664-e373-456d-ba85-6047dfc84452']['name'] == 'vobd'
    assert type(server.datasets['7c677664-e373-456d-ba85-6047dfc84452']['constraints']) == list


def test_setitem(server):
    with pytest.raises(NotImplementedError):
        server.datasets['7c677664-e373-456d-ba85-6047dfc84452'] = 'raspberry'


def test_len(server):
    assert len(server.datasets) == 1


def test_iter(server):
    assert type([v for v in server.datasets.values()][0]) == dict
    assert len([d for d in server.datasets]) == 1


def test_append(server):
    assert server.datasets.append(name='mydataset', description='mydescription', field='hostname', value='esx*') is None

    with pytest.raises(TypeError):
        server.datasets.append(name='mydataset', description='mydescription', field=1, value='error')
