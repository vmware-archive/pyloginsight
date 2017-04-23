import pytest
from pyloginsight.connection import Connection, Credentials, Unauthorized
import requests_mock

adapter = requests_mock.Adapter()

adapter.register_uri(
    method='GET',
    url='/api/v1/auth-providers',
    status_code=200,
    text='{"providers": ["Local","ActiveDirectory"]}'
)

adapter.register_uri(
    method='GET',
    url='/api/v1/auth-providers',
    status_code=503,
    text='{"errorMessage": "LI server should be bootstrapped to process this API call"}'
)

server = Connection(
    hostname='mockserverlocal',
    port=9543,
    auth=Credentials(
        username='admin',
        password='admin',
        provider='local'
    )
)
server._requestsession.mount('https://', adapter=adapter)

def test_providers(server):
    assert 0 == 0
