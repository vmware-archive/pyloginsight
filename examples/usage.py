#!/usr/bin/env python

"""
Example usage of the pyloginsight library
"""

class User(object):
    def save(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

class User(object):
    def save(self):
        pass
    def __enter__(self):
        self._context = copy_of(self)  # User(**self._asdict())
        return self._context
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context.save()
        del self._context



class generalized_save(object):
    def __init__(self, original):
        self.data = copy_of(original)
    def __enter__(self):
        return self.data
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.data.save()


class Users(object):
    def __getitem__(self, item):
        return User(item)

def change_every_bob_email_address():
    from pyloginsight import LogInsight, Credentials


    with LogInsight("192.168.50.149", Credentials(username="foo", password="bar", provider="Local")) as connection:

        for user in connection.admin.users:
            if user.name == "Bob":
                with user as changes:
                    changes.email = "bob@example.com"


def change_every_bob_email_address_alternate():
    from pyloginsight import LogInsight, Credentials

    with LogInsight("192.168.50.149", Credentials(username="foo", password="bar", provider="Local")) as connection:

        with connection.admin.users["123456789"] as changes:
            changes.email = "bob@example.com"

        with Changes(connection.admin.users["123456789"]) as changes:
            changes.email = "bob@example.com"


        myuser = connection.admin.users["123456789"]
        myuser.email = "bob@example.com"
        myuser.save()

        myuser = connection.admin.users["123456789"]
        bar = myuser.email
        assert bar == "bar@foo.com"

        with myuser as u:
            assert myuser is not u
            u.email = "foo@bar.com"

        assert myuser.email != bar

def make_a_dataset():
    from pyloginsight import LogInsight, Credentials, Save, Dataset

    with LogInsight("192.168.50.149", Credentials(username="foo", password="bar", provider="Local")) as connection:

        new_dataset = Dataset("datasetname")

        connection.admin.dataset.append(new_dataset)


def run_a_query():
    from pyloginsight import LogInsight, Credentials, Save, Constraint

    with LogInsight("192.168.50.149", Credentials(username="foo", password="bar", provider="Local")) as connection:

        conditions = [Constraint("fieldname", Constraint.EQUALS, "value")]
        for result in connection.query.events(conditions):
            print(result)
