import pytest
import requests_mock
from pyloginsight.models import Server, Credentials, Roles


# Example responses.
GET_GROUPS = '{"groups":[{"id":"00000000-0000-0000-0000-000000000001","name":"Super Admin","description":"Full Admin and User capabilities, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"INTERNAL"},{"id":"EDIT_SHARED"},{"id":"EDIT_ADMIN"},{"id":"STATISTICS"},{"id":"INVENTORY"},{"id":"DASHBOARD"}],"required":true,"editable":false},{"id":"df250358-ba62-4d0d-b11e-44d258d91540","name":"moo","description":"moo","capabilities":[{"id":"INVENTORY"}],"required":false,"editable":true},{"id":"dc48f0e1-7c3e-44d3-a480-c97dfa82b83a","name":"Dashboard User","description":"Can use only Dashboards","capabilities":[{"id":"DASHBOARD"}],"required":false,"editable":true},{"id":"583d447c-d960-4faf-8995-c0386f41d0d3","name":"test","description":"test","capabilities":[{"id":"INVENTORY"}],"required":false,"editable":true},{"id":"12b8d2eb-5245-416c-b744-cede668f05eb","name":"View Only Admin","description":"Can view Admin info and has full User access, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"EDIT_SHARED"},{"id":"DASHBOARD"}],"required":false,"editable":true},{"id":"00000000-0000-0000-0000-000000000002","name":"User","description":"Can use Interactive Analytics and Dashboards","capabilities":[{"id":"ANALYTICS"},{"id":"DASHBOARD"}],"required":true,"editable":true}]}'
POST_GROUPS = '{"group":{"id":"75915e20-99c1-46c1-aad7-748f5958f18d","name":"arf","description":"arf","capabilities":[{"id":"INTERNAL"}],"required":false,"editable":true}}'
GET_GROUPS_ID = '{"group":{"id":"00000000-0000-0000-0000-000000000001","name":"Super Admin","description":"Full Admin and User capabilities, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"INTERNAL"},{"id":"EDIT_SHARED"},{"id":"EDIT_ADMIN"},{"id":"STATISTICS"},{"id":"INVENTORY"},{"id":"DASHBOARD"}],"required":true,"editable":false}}'
GET_GROUPS_ID_400 = '{"errorMessage":"Bad request received (Cannot parse parameter groupId as UUID: Invalid UUID string: raspberry): GET /api/v1/groups/raspberry"}'
GET_GROUPS_ID_404 = '{"errorMessage":"Specified group does not exist.","errorCode":"RBAC_GROUPS_ERROR","errorDetails":{"errorCode":"com.vmware.loginsight.api.errors.rbac.group_does_not_exist"}}'
POST_GROUPS_ID = ''  # response is empty string
PATCH_GROUPS_ID = ''  # response is empty string
DELETE_GROUPS_ID = ''  # response is empty string
DELETE_GROUPS_ID_409 = '{"errorMessage":"Specified group is required.","errorCode":"RBAC_GROUPS_ERROR","errorDetails":{"errorCode":"com.vmware.loginsight.api.errors.rbac.group_is_required"}}'
DELETE_GROUPS_ID_404 = '{"errorMessage":"Specified group does not exist.","errorCode":"RBAC_GROUPS_ERROR","errorDetails":{"errorCode":"com.vmware.loginsight.api.errors.rbac.group_does_not_exist"}}'


# Added responses to mock server.
adapter = requests_mock.Adapter()
adapter.register_uri(method='GET', url='https://mockserver:9543/api/v1/groups', text=GET_GROUPS, status_code=200)
adapter.register_uri(method='POST', url='https://mockserver:9543/api/v1/groups', text=POST_GROUPS, status_code=200)
adapter.register_uri(method='GET', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=GET_GROUPS_ID, status_code=200)
adapter.register_uri(method='GET', url='https://mockserver:9543/api/v1/groups/raspberry',
                     text=GET_GROUPS_ID_400, status_code=400)
adapter.register_uri(method='GET', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000025',
                     text=GET_GROUPS_ID_404, status_code=404)
adapter.register_uri(method='POST', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=POST_GROUPS_ID, status_code=200)
adapter.register_uri(method='PATCH', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=GET_GROUPS_ID, status_code=200)
adapter.register_uri(method='DELETE', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=DELETE_GROUPS_ID_409, status_code=409)
adapter.register_uri(method='DELETE', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000025',
                     text=DELETE_GROUPS_ID_404, status_code=404)
adapter.register_uri(method='DELETE', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000004',
                     text=DELETE_GROUPS_ID, status_code=200)


credentials = Credentials(username='admin', password='secret', provider='Local')
server = Server(hostname='mockserver', auth=credentials)
server._requestsession.mount('https://', adapter)


def test_property():
    assert server.roles is not None
    assert type(server.roles) is Roles


def test_getitem():
    assert type(server.roles['00000000-0000-0000-0000-000000000001']) == dict
    assert server.roles['00000000-0000-0000-0000-000000000001']['name'] == 'Super Admin'
    assert type(server.roles['00000000-0000-0000-0000-000000000001']['capabilities']) == list
    assert server.roles['00000000-0000-0000-0000-000000000001']['capabilities'][0]['id'] in (
        'ANALYTICS', 'DASHBOARDS', 'EDIT_ADMIN', 'EDIT_SHARED', 'INTERNAL', 'INVENTORY', 'STATISTICS', 'VIEW_ADMIN')

    with pytest.raises(KeyError):
        print(server.roles[5])

    with pytest.raises(KeyError):
        print(server.roles['raspberry'])

    with pytest.raises(KeyError):
        print(server.roles['00000000-0000-0000-0000-000000000025'])


def test_setitem():
    with pytest.raises(NotImplementedError):
        server.roles['00000000-0000-0000-0000-000000000001'] = 'moo'


def test_delitem():
    assert server.roles.pop('00000000-0000-0000-0000-000000000004', None) is None

    with pytest.raises(KeyError):
        server.roles.pop('00000000-0000-0000-0000-000000000025')

    with pytest.raises(KeyError):
        server.roles.pop('00000000-0000-0000-0000-000000000001', None)


def test_iter():
    # assert type([k for k in server.roles.keys()][0]) == str
    # assert type([k for (k, v) in server.roles.items()][0]) == str
    # Above tests fails because on Python 2.7 gets unicode instead of string.
    assert type([v for v in server.roles.values()][0]) == dict


def test_len():
    assert len(server.roles) == 6


def test_append():
    server.roles.append(
        name='myrole',
        description='mydescription',
        capabilities=['INTERNAL']
    ) is None

    with pytest.raises(TypeError):
        server.roles.append(
            name=5,
            description='mydescription',
            capabilities=[]
        )

    with pytest.raises(TypeError):
        server.roles.append(
            name='myrole',
            description=5,
            capabilities=[]
        )

    with pytest.raises(TypeError):
        server.roles.append(
            name='myrole',
            description='mydescription',
            capabilities=5
        )

    with pytest.raises(TypeError):
        server.roles.append(
            name='myrole',
            description='mydescription',
            capabilities=[]
        )

    with pytest.raises(TypeError):
        server.roles.append(fruit='Raspberry')

    with pytest.raises(TypeError):
        server.roles.append()


@pytest.mark.xfail
def test_role_get():
    assert server.roles['00000000-0000-0000-0000-000000000001'] is not None


@pytest.mark.xfail
def test_role_set():
    r = server.roles['00000000-0000-0000-0000-000000000001']
    server.roles['00000000-0000-0000-0000-000000000001'] = r


@pytest.mark.xfail
def test_role_del():
    del server.roles['00000000-0000-0000-0000-000000000001']

    with pytest.raises(KeyError):
        del server.roles['00000000-0000-0000-0000-000000000001']


@pytest.mark.xfail
def test_role_get_name():
    assert server.roles['00000000-0000-0000-0000-000000000001'].name is not None


@pytest.mark.xfail
def test_role_set_name():
    server.roles['00000000-0000-0000-0000-000000000001'].name = 'moo'


@pytest.mark.xfail
def test_role_set_multiple():
    with server.roles['00000000-0000-0000-0000-000000000001'] as role:
        role.name = 'moo'
        role.description = 'desc'


# Datasets
@pytest.mark.xfail
def test_role_get_datasets():
    for d in server.roles['00000000-0000-0000-0000-000000000001'].datasets:
        assert type(d) == Dataset


@pytest.mark.xfail
def test_role_set_dataset():
    d = server.roles['00000000-0000-0000-0000-000000000001'].datasets
    server.roles['00000000-0000-0000-0000-000000000001'].datasets = d


# Users
@pytest.mark.xfail
def test_role_get_users():
    for u in server.roles['00000000-0000-0000-0000-000000000001'].users:
        assert type(u) == User


@pytest.mark.xfail
def test_role_set_users():
    u = server.roles['00000000-0000-0000-0000-000000000001'].users
    server.roles['00000000-0000-0000-0000-000000000001'].users = u


# ADGroups
@pytest.mark.xfail
def test_role_get_adgroups():
    for u in server.roles['00000000-0000-0000-0000-000000000001'].users:
        assert type(u) == User


@pytest.mark.xfail
def test_role_set_adgroups():
    g = server.roles['00000000-0000-0000-0000-000000000001'].adgroups
    server.roles['00000000-0000-0000-0000-000000000001'].adgroups = g


# Capabilities
@pytest.mark.xfail
def test_role_get_capabilities():
    for c in server.roles['00000000-0000-0000-0000-000000000001'].capabilities:
        assert type(c) == Capability


@pytest.mark.xfail
def test_role_set_capabilities():
    c = server.roles['00000000-0000-0000-0000-000000000001'].capabilities
    with pytest.raises(NotImplementedError):
        server.roles['00000000-0000-0000-0000-000000000001'].capabilities[0] = c[0]


@pytest.mark.xfail
def test_theory():
    class ZDataset(object):
        def __init__(self, dataset_id):
            self.dataset_id = dataset_id


    class XRole(object):

        def __init__(self, roleid):
            self._roleid = roleid

        class YDatasets(object):
            def __init__(self, roleid):
                self._roleid = roleid

            def __getitem__(self, dataset_id):
                return ZDataset(dataset_id)

        @property
        def datasets(self):
            return self.YDatasets(self._roleid)

        pass

    r = XRole(1)

    d = r.datasets

    ds = d[4]

    assert ds.dataset_id == 4

