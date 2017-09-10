from __future__ import print_function
import pytest

@pytest.fixture(params=[1, 2])
def ExampleParam(request):
    return request.param

observed_connections = []


def test_each_connection_object_is_used_once(connection, ExampleParam):
    print("Running against connection", id(connection))
    identity = id(connection)

    assert identity not in observed_connections
    observed_connections.append(identity)
