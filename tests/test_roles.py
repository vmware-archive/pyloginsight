#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function


import pytest
from pyloginsight.models import Role, Roles
import uuid


def test_setitem(connection):
    datasets = connection.server.datasets
    with pytest.raises(NotImplementedError):
        datasets['7c677664-e373-456d-ba85-6047dfc84452'] = 'raspberry'


def test_append_and_delete(connection):
    d = connection.server.roles

    name = "testrole-" + str(uuid.uuid4())

    original_quantity = len(d)

    o = Role(name=name, description='mydescription', capabilities=["ANALYTICS"])
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


def test_parse_roles():
    roles_dict = {'roles': [{'capabilities': [{'id': 'DASHBOARD'}], 'editable': True, 'dataSets': [], 'id': 'b7b56e53-55ea-41c5-af0c-4da7c3787789', 'name': 'Dashboard User', 'description': 'Can use only Dashboards', 'required': False}, {'capabilities': [{'id': 'ANALYTICS'}, {'id': 'VIEW_ADMIN'}, {'id': 'INTERNAL'}, {'id': 'EDIT_SHARED'}, {'id': 'EDIT_ADMIN'}, {'id': 'STATISTICS'}, {'id': 'INVENTORY'}, {'id': 'DASHBOARD'}], 'editable': False, 'dataSets': [], 'id': '00000000-0000-0000-0000-000000000001', 'name': 'Super Admin', 'description': 'Full Admin and User capabilities, including editing Shared content', 'required': True}, {'capabilities': [{'id': 'ANALYTICS'}, {'id': 'DASHBOARD'}], 'editable': True, 'dataSets': [], 'id': '00000000-0000-0000-0000-000000000002', 'name': 'User', 'description': 'Can use Interactive Analytics and Dashboards', 'required': True}, {'capabilities': [{'id': 'ANALYTICS'}, {'id': 'VIEW_ADMIN'}, {'id': 'EDIT_SHARED'}, {'id': 'DASHBOARD'}], 'editable': True, 'dataSets': [], 'id': '3f31d0ab-c648-4251-a012-b1b5897bf850', 'name': 'View Only Admin', 'description': 'Can view Admin info and has full User access, including editing Shared content', 'required': False}]}

    collection_class = Roles

    Single = collection_class._single
    collection = collection_class(None)

    collection.asdict = lambda: roles_dict

    count = 0
    for key, value in collection.items():
        count += 1
        assert isinstance(key, (u"".__class__, "".__class__, int))
        assert isinstance(value, Single)

    assert count == len(collection)
