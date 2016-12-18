import pytest, requests_mock
from pyloginsight.models import Server, Credentials, Roles


# Example responses.
GET_GROUPS = '{"groups":[{"id":"00000000-0000-0000-0000-000000000001","name":"Super Admin","description":"Full Admin and User capabilities, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"INTERNAL"},{"id":"EDIT_SHARED"},{"id":"EDIT_ADMIN"},{"id":"STATISTICS"},{"id":"INVENTORY"},{"id":"DASHBOARD"}],"required":true,"editable":false},{"id":"df250358-ba62-4d0d-b11e-44d258d91540","name":"moo","description":"moo","capabilities":[{"id":"INVENTORY"}],"required":false,"editable":true},{"id":"dc48f0e1-7c3e-44d3-a480-c97dfa82b83a","name":"Dashboard User","description":"Can use only Dashboards","capabilities":[{"id":"DASHBOARD"}],"required":false,"editable":true},{"id":"583d447c-d960-4faf-8995-c0386f41d0d3","name":"test","description":"test","capabilities":[{"id":"INVENTORY"}],"required":false,"editable":true},{"id":"12b8d2eb-5245-416c-b744-cede668f05eb","name":"View Only Admin","description":"Can view Admin info and has full User access, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"EDIT_SHARED"},{"id":"DASHBOARD"}],"required":false,"editable":true},{"id":"00000000-0000-0000-0000-000000000002","name":"User","description":"Can use Interactive Analytics and Dashboards","capabilities":[{"id":"ANALYTICS"},{"id":"DASHBOARD"}],"required":true,"editable":true}]}'
POST_GROUPS = '{"group":{"id":"75915e20-99c1-46c1-aad7-748f5958f18d","name":"arf","description":"arf","capabilities":[{"id":"INTERNAL"}],"required":false,"editable":true}}'
GET_GROUPS_ID = '{"group":{"id":"00000000-0000-0000-0000-000000000001","name":"Super Admin","description":"Full Admin and User capabilities, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"INTERNAL"},{"id":"EDIT_SHARED"},{"id":"EDIT_ADMIN"},{"id":"STATISTICS"},{"id":"INVENTORY"},{"id":"DASHBOARD"}],"required":true,"editable":false}}'
GET_GROUPS_ID_400 = '{"errorMessage":"Bad request received (Cannot parse parameter groupId as UUID: Invalid UUID string: raspberry): GET /api/v1/groups/raspberry"}'
GET_GROUPS_ID_404 = '{"errorMessage":"Specified group does not exist.","errorCode":"RBAC_GROUPS_ERROR","errorDetails":{"errorCode":"com.vmware.loginsight.api.errors.rbac.group_does_not_exist"}}'
POST_GROUPS_ID = ''  # response is empty string
PATCH_GROUPS_ID = ''  # response is empty string
DELETE_GROUPS_ID = '' # response is empty string
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
    assert type([k for k in server.roles.keys()][0]) == str
    assert type([v for v in server.roles.values()][0]) == dict
    assert type([k for (k, v) in server.roles.items()][0]) == str


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
