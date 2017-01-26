#!/usr/bin/env python

# VMware vRealize Log Insight SDK
# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from distutils.version import StrictVersion
from .connection import Connection, Credentials
import logging
import collections
from .abstracts import ServerAddressableObject, AppendableServerDictMixin, ServerDictMixin
import json


logger = logging.getLogger(__name__)


def named_tuple_with_defaults(name, fields, values=()):
    new_class = collections.namedtuple(name, fields)
    new_class.__new__.__defaults__ = (None,) * len(new_class._fields)

    if isinstance(values, collections.Mapping):
        prototype = new_class(**values)
    else:
        prototype = new_class(*values)

    new_class.__new__.__defaults__ = tuple(prototype)
    return new_class


class LicenseKeys(collections.MutableMapping):
    """A server-backed dictionary (hashmap) of items embedded in the
    Adding, deleting or updating an item usually means POST/PUTing a single item's resource."""

    def __init__(self, connection, baseurl):
        self._connection = connection
        self._baseurl = baseurl

    def __delitem__(self, item):
        resp = self._connection._delete("{0}/{1}".format(self._baseurl, item))
        if resp.status_code == 200:
            return True
        elif resp.status_code == 404:
            raise KeyError("Unknown license key uuid {0}".format(item))
        else:
            raise ValueError(resp.json()['errorMessage'])
        # TODO: Should raise KeyError on unknown license key.

    def append(self, licensekey):
        """A list-like interface for addding a new licence.
        The server will assign a new UUID when inserting into the mapping.
        A subsequent request to keys/iter will contain the new license in the value."""
        resp = self._connection._post(self._baseurl, json={"key": licensekey})
        if resp.status_code in [400, 409, 500]:
            raise ValueError(resp.json()['errorMessage'])
        elif resp.status_code == 201:
            return True
        raise NotImplementedError("Unhandled status")

    def __getitem__(self, item):
        """Retrieve details for a license key. Could raise KeyError."""
        return self._rootobject['licenses'][item]

    def keys(self):
        return self._rootobject['licenses'].keys()

    def __iter__(self):
        for key in self.keys():
            yield key

    def __len__(self):
        return len(self._rootobject["licenses"])

    def __setitem__(self, key, value):
        raise NotImplementedError

    @property
    def _rootobject(self):
        return self._connection._get(self._baseurl).json()

    @property
    def summary(self):
        """Dictionary summarizing installed licenses and active features"""
        return self._rootobject


class AlternateLicenseKeys(AppendableServerDictMixin, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/licenses"
    _fromserver = collections.namedtuple("License", ("id", "error", "status", "configuration", "expiration", "licenseKey", "infinite", "count", "typeEnum"))

    class _createspec(object):
        def __init__(self, key):
            self.key = key

        def _asdict(self):
            return {"key": self.key}

    @property
    def _iterable(self):
        return self.asdict().get("licenses")


class Version(ServerAddressableObject, StrictVersion):
    """Server's self-reported current version number."""
    _baseurl = "/version"

    def __call__(self):
        """
        Extract a Major.Minor.Patch version number from the server's response,
        and update internal state.
        :return: self, which acts like a distutils.StrictVersion
        """
        self.parse(self.asdict().get("version").split("-", 1)[0])
        return self

    @property
    def build(self):
        """
        Extract build number from version string returned by server.
        Every official build has a distinct, non-repeating build number.
        Higher build numbers do not necessarily indicate builds.
        :return: int
        """
        return int(self.asdict().get("version").split("-", 1)[1])

    @property
    def raw(self):
        """
        Raw version string returned by server. Has the format `Major.Minor.Patch-build.flag.names`,
        where flag names are strings like "TP" or "BETA".
        :return: str
        """
        return self.asdict().get("version")


class Datasets(collections.MutableMapping):

    def __init__(self, connection):
        self._connection = connection

    @property
    def _rootobject(self):
        return {dataset['id']: dataset for dataset in self._connection._get('/datasets').json()['dataSets']}

    def __delitem__(self, key):
        response = self._connection._delete('/datasets/{i}'.format(i=key))
        if response.ok:
            pass
        else:
            if response.status_code == 400:
                raise KeyError('The specified data set does not exist.')
            else:
                raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))

    def __getitem__(self, key):
        return self._rootobject[key]

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __len__(self):
        return len(self._rootobject)

    def __iter__(self):
        return iter(self._rootobject)

    def append(self, name, description, field, value):

        if type(name) == str and type(description) == str and type(field) == str and type(value) == str:
            pass
        else:
            raise TypeError('The name, description, field, and value should be string types.')

        constraints = [{'name': field, 'operator': 'CONTAINS', 'value': value, 'fieldType': 'STRING'}]
        data = json.dumps({'name': name, 'description': description, 'constraints': constraints})
        response = self._connection._post('/datasets', data=data)

        if response.ok:
            return None

        else:
            if response.status_code == 400:
                raise TypeError(response.text)
            else:
                raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))


class Roles(collections.MutableMapping):

    def __init__(self, connection):
        self._connection = connection

    @property
    def _rootobject(self):
        return {group['id']: group for group in self._connection._get('/groups').json()['groups']}

    def __delitem__(self, group_id):
        """ Deletes a role. """

        response = self._connection._delete('/groups/{i}'.format(i=group_id))

        if response.ok:
            pass

        else:
            if response.status_code == 404:
                raise KeyError('The specified role does not exist.')
            elif response.status_code == 409:
                raise KeyError('The specified role is required and cannot be deleted.')
            else:
                raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))

    def __getitem__(self, group_id):
        """ Gets a role. """
        return self._rootobject[group_id]

    def __setitem__(self, group_id, value):
        raise NotImplementedError

    def __iter__(self):
        return iter(self._rootobject)

    def __len__(self):
        return len(self._rootobject)

    def append(self, name, description, capabilities):
        """ Creates a role. """

        # Ensure we are not getting invalid data types.
        if not type(name) is str:
            raise TypeError('The name value must be a string.')

        if not type(description) is str:
            raise TypeError('The description value must be a string.')

        if not type(capabilities) is list:
            raise TypeError('The capabilities value must be a list.')

        # Ensure we only use valid capabilities.
        good_capabilities = ('ANALYTICS', 'DASHBOARDS', 'EDIT_ADMIN', 'EDIT_SHARED', 'INTERNAL', 'INVENTORY',
                             'STATISTICS', 'VIEW_ADMIN')
        valid_capabilities = [capability for capability in capabilities if capability in good_capabilities]
        if not valid_capabilities:
            raise TypeError('Capabilities must contain at least one valid capability.  Capabilities include: {m}.'.format(m=', '.join(good_capabilities)))

        data = json.dumps({'name': name, 'description': description, 'capabilities': valid_capabilities})
        response = self._connection._post('/groups', data=data)

        if response.ok:
            pass

        else:
            if response.status_code == 409:
                raise ValueError('A role with the same name value already exists.')
            else:
                raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))


class Server(Connection):
    """High-level object representing the capabilities of a remote Log Insight server"""

    _connection = None

    version = Version(_connection)

    def login(self, username, password, provider):
        # TODO: Should this attempt to use the credentials?
        self._authprovider = Credentials(username=username, password=password, provider=provider)

    @property
    def is_bootstrapped(self):
        """Convenience function for interogating a server to determine whether it's been bootstrapped already."""
        raise NotImplementedError("TODO: Determine whether the server is already bootstrapped")
        try:
            self.post("/deployment/new")
            return False
        except:
            return True

    @property
    def current_session(self):
        resp = self._get("/sessions/current").json()
        return resp

    @property
    def license(self):
        return LicenseKeys(self, "/licenses")

    @property
    def roles(self):
        return Roles(self)

    @property
    def datasets(self):
        return Datasets(self)

    # TODO: Model the server features as properties
