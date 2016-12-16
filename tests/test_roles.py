import pytest, requests_mock
from pyloginsight.models import Server, Credentials, Roles


# Example responses.
GET_GROUPS='{"groups":[{"id":"00000000-0000-0000-0000-000000000001","name":"Super Admin","description":"Full Admin and User capabilities, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"INTERNAL"},{"id":"EDIT_SHARED"},{"id":"EDIT_ADMIN"},{"id":"STATISTICS"},{"id":"INVENTORY"},{"id":"DASHBOARD"}],"required":true,"editable":false},{"id":"df250358-ba62-4d0d-b11e-44d258d91540","name":"moo","description":"moo","capabilities":[{"id":"INVENTORY"}],"required":false,"editable":true},{"id":"dc48f0e1-7c3e-44d3-a480-c97dfa82b83a","name":"Dashboard User","description":"Can use only Dashboards","capabilities":[{"id":"DASHBOARD"}],"required":false,"editable":true},{"id":"583d447c-d960-4faf-8995-c0386f41d0d3","name":"test","description":"test","capabilities":[{"id":"INVENTORY"}],"required":false,"editable":true},{"id":"12b8d2eb-5245-416c-b744-cede668f05eb","name":"View Only Admin","description":"Can view Admin info and has full User access, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"EDIT_SHARED"},{"id":"DASHBOARD"}],"required":false,"editable":true},{"id":"00000000-0000-0000-0000-000000000002","name":"User","description":"Can use Interactive Analytics and Dashboards","capabilities":[{"id":"ANALYTICS"},{"id":"DASHBOARD"}],"required":true,"editable":true}]}'
POST_GROUPS = '{"group":{"id":"75915e20-99c1-46c1-aad7-748f5958f18d","name":"arf","description":"arf","capabilities":[{"id":"INTERNAL"}],"required":false,"editable":true}}'
GET_GROUPS_ID = '{"group":{"id":"00000000-0000-0000-0000-000000000001","name":"Super Admin","description":"Full Admin and User capabilities, including editing Shared content","capabilities":[{"id":"ANALYTICS"},{"id":"VIEW_ADMIN"},{"id":"INTERNAL"},{"id":"EDIT_SHARED"},{"id":"EDIT_ADMIN"},{"id":"STATISTICS"},{"id":"INVENTORY"},{"id":"DASHBOARD"}],"required":true,"editable":false}}'
POST_GROUPS_ID = ''  # response is empty string
PATCH_GROUPS_ID = ''  # response is empty string
DELETE_GROUPS_ID='' # response is empty string


# Added responses to mock server.
adapter = requests_mock.Adapter()
adapter.register_uri(method='GET', url='https://mockserver:9543/api/v1/groups/', text=GET_GROUPS_ID, status_code=200)
adapter.register_uri(method='POST', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=POST_GROUPS_ID,
                     status_code=200)
adapter.register_uri(method='PATCH', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=GET_GROUPS_ID,
                     status_code=200)
adapter.register_uri(method='DELETE', url='https://mockserver:9543/api/v1/groups/00000000-0000-0000-0000-000000000001',
                     text=DELETE_GROUPS_ID,
                     status_code=200)


credentials = Credentials(username='admin', password='secret', provider='Local')
server = Server(hostname='mockserver', auth=credentials)
server._requestsession.mount('https://', adapter)


def test_property():
    assert server.roles is not None
    assert type(server.roles) is Roles


def test_getitem():
    with pytest.raises(NotImplementedError):
        assert server.roles['00000000-0000-0000-0000-000000000001'] is not None


def test_setitem():
    with pytest.raises(NotImplementedError):
        server.roles['00000000-0000-0000-0000-000000000001'] = 'moo'


def test_delitem():
    with pytest.raises(NotImplementedError):
        server.roles.pop('00000000-0000-0000-0000-000000000001', None)


def test_iter():
    with pytest.raises(NotImplementedError):
        test_var = [x for x in server.roles]


def test_len():
    with pytest.raises(NotImplementedError):
        test_var = len(server.roles)

