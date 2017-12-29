# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest
from pyloginsight.models import Users, User
from pyloginsight.connection import Credentials
from pyloginsight.exceptions import Unauthorized
import uuid
import logging
from collections import namedtuple


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


@pytest.mark.sideeffects
def test_modify_an_existing_user_object(connection):
    d = Users(connection)
    previous_quantity = len(d)

    assert previous_quantity > 0  # The server should already have a user

    username = "testuser-" + str(uuid.uuid4())
    email = "testuser@local.localdom"
    new_user = User(username=username, email=email, password="abc!-DEF!-123!")
    print(new_user)

    new_user_id = d.append(new_user)
    print("Created new user id", new_user_id, ":", new_user)

    # Setup Completed

    # Get and mutate the object
    refetch_user = d[new_user_id]
    assert refetch_user.username == username

    with refetch_user as m:
        m.email = "testuser_changed_email@local.localdom"

    # Retrieve updated object from server
    verification = d[new_user_id]

    # Remove the key from the server before asserts
    del d[new_user_id]

    # Update happened
    assert verification.email == "testuser_changed_email@local.localdom"
    assert len(d) == previous_quantity


@pytest.fixture
def connection_with_temporary_testuser(connection):
    d = Users(connection)
    previous_quantity = len(d)
    assert previous_quantity > 0  # The server should already have a user
    username = "testuser-" + str(uuid.uuid4())
    email = "testuser@local.localdom"

    new_user = User(username=username, email=email, password="abc!-DEF!-123!")
    print(new_user)

    new_user_id = d.append(new_user)
    print("Created new user id", new_user_id, ":", new_user)

    # Let the test use the user
    ConnectionWithTemporaryTestUser = namedtuple("ConnectionWithTemporaryTestUser", "connection, users, user, user_id")
    yield ConnectionWithTemporaryTestUser(connection, d, d[new_user_id], new_user_id)

    # Cleanup
    del d[new_user_id]

    # Update happened
    assert len(d) == previous_quantity

    with pytest.raises(KeyError):
        _ = d[new_user_id]


@pytest.mark.sideeffects
def test_change_user_email(connection_with_temporary_testuser):

    connection, users, user, user_id = connection_with_temporary_testuser

    with user as m:
        m.email = "testuser_changed_email@local.localdom"

    # Retrieve updated object from server
    verification = users[user_id]

    # Update happened
    assert verification.email == "testuser_changed_email@local.localdom"


@pytest.mark.sideeffects
def test_change_user_password(connection_with_temporary_testuser):

    connection, users, user, user_id = connection_with_temporary_testuser

    with user as m:
        m.password = "abc!-DEF!-123!CHANGED"

    # Retrieve updated object from server
    verification = users[user_id]
    assert 'password' not in verification

    # Backup
    original_auth = connection._authprovider

    def type_to_provider(t):
        return {'DEFAULT': 'Local'}[t]

    logger.info("Try to login with the old password, should fail")
    with pytest.raises(Unauthorized):
        connection._authprovider = Credentials(username=user.username, password="abc!-DEF!-123!", provider=type_to_provider(user.type))
        current_session = connection.server.current_session

    logger.info("Try to login with new credentials")
    connection._authprovider = Credentials(username=user.username, password="abc!-DEF!-123!CHANGED", provider=type_to_provider(user.type))
    current_session = connection.server.current_session
    print("current_session", current_session)

    # Restore
    connection._authprovider = original_auth

    # Verify that we were logged in as the temporary user
    assert user_id == current_session['userId']


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
        print("Retrieved item", k, ",", v)
        assert k == v.id
        assert hasattr(v, "username")
        counter += 1
    assert counter > 0  # There should be at least one existing user (us)on the server
    assert counter == len(d) == len(d.keys())  # counting and length agree


@pytest.mark.sideeffects
def test_cleanup_test_users(connection):
    d = Users(connection)

    # retrieve every item
    for k, v in d.items():
        if 'email' in v and "testuser@local.localdom" == v.email:
            print("Should delete item", k, v)
            del d[k]


class MissingSentinal(object):
    pass


@pytest.mark.parametrize("email,valid", [
    ("testuser@local.localdom", True),
    ("", True),
    (None, True),
    (MissingSentinal, True),
    ("testuser_changed_email@local.localdom", True),
    ("a@example.com", True),
    # ("abcd", False),  # This is currently valid, because we're not subclassing fields.Email
])
def test_valid_email_addresses(email, valid):

    u = {'user': {'id': '1', 'username': 'a', 'email': email}}

    if email == MissingSentinal:
        del u['user']['email']
        email = None

    o = User.from_dict(None, None, u, many=False)

    print(o)
    assert valid == isinstance(o, User)

    back_to_json = o._serialize()
    print("back_to_json:", back_to_json)

    assert back_to_json['user']['email'] not in (None, MissingSentinal)

    if email == "":
        email = None

    if valid:
        assert isinstance(o, User)
        assert o.email == email
    else:
        assert isinstance(o, dict)
