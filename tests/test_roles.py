#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function


import pytest
from pyloginsight.models import Role
import uuid


def test_setitem(connection):
    datasets = connection.server.datasets
    with pytest.raises(NotImplementedError):
        datasets['7c677664-e373-456d-ba85-6047dfc84452'] = 'raspberry'


def test_append_and_delete(connection):
    d = connection.server.roles

    name = "testdataset-" + str(uuid.uuid4())

    original_quantity = len(d)

    o = Role(name=name, description='mydescription')
    assert 'id' not in o

    new_object_guid = d.append(o)
    print("new_object_guid", new_object_guid)

    assert '-' in new_object_guid

    refetch_object = d[new_object_guid]
    print("refetch_object", refetch_object)

    assert len(d) == original_quantity + 1

    del d[new_object_guid]

    # Back to starting point
    assert len(d) == original_quantity
