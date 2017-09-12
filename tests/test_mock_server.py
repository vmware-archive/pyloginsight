# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest


@pytest.fixture(params=[1, 2])
def ExampleParam(request):
    """Placeholder to force multiple executions of the test"""
    return request.param

observed_connections = []


def test_each_connection_object_is_used_once(connection, ExampleParam):
    """
    Execute 2 tests for every `connection`.
    Verify that a single `connection` instance is never reused between tests.
    """
    identity = id(connection)
    assert identity not in observed_connections
    observed_connections.append(identity)
