# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest
from pyloginsight.models import Users, User
import uuid
import logging


logger = logging.getLogger(__name__)


@pytest.mark.sideeffects
def test_add_user_and_remove_it_again(connection):
    d = Users(connection)
    previous_quantity = len(d)

    assert previous_quantity > 0  # The server should already have a user

    username = "testuser-" + str(uuid.uuid4())
    email = "testuser@local.localdom"
    new_user = User(username=username, email=email, password="abc!-DEF!-123!")
    print(new_user)

    new_user_id = d.append(new_user)
    print("Created new user id", new_user_id, ":", new_user)

    refetch_user = d[new_user_id]
    assert refetch_user.username == username

    # Remove the key from the server; server may become unlicensed at this point
    del d[new_user_id]

    # Same quantity now as before
    assert len(d) == previous_quantity


def test_remove_nonexistent(connection):
    d = Users(connection)
    previous_quantity = len(d)

    # the fake key we're trying to delete really doesn't exist
    for guid in d.keys():
        assert guid != "000000000-000-0000-0000-000000000000"

    with pytest.raises(KeyError):
        del d["000000000-000-0000-0000-000000000000"]
    assert len(d) == previous_quantity


def test_iterate_over(connection):
    d = Users(connection)

    counter = 0
    # retrieve every item
    for k, v in d.items():
        assert k == v.id
        assert hasattr(v, "username")
        counter += 1
    assert counter > 0  # There should be at least one existing user (us)on the server
    assert counter == len(d)  # counting and length agree


@pytest.mark.sideeffects
def test_cleanup_test_users(connection):
    d = Users(connection)

    # retrieve every item
    for k, v in d.items():
        if 'email' in v and "testuser@local.localdom" == v.email:
            print("Should delete item", k, v)
            del d[k]
