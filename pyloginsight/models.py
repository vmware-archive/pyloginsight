#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import logging
import collections
from .abstracts import ServerAddressableObject, AppendableServerDictMixin, ServerDictMixin, ServerListMixin
from .abstracts import ServerProperty, RemoteObjectProxy, BaseSchema
import json
import attrdict
from marshmallow import Schema, fields
from .exceptions import TransportError
from datetime import datetime

logger = logging.getLogger(__name__)


class LicenseKey(RemoteObjectProxy, attrdict.AttrDict):
    """A single license key for Log Insight."""
    class MarshmallowSchema(Schema):
        id = fields.Str()
        error = fields.Str(load_only=True)
        status = fields.Str(load_only=True)
        configuration = fields.Str(load_only=True)
        expiration = fields.Str(load_only=True)
        licenseKey = fields.Str()
        infinite = fields.Str(load_only=True)
        count = fields.Integer(load_only=True)
        typeEnum = fields.Str(load_only=True)


class LicenseKeys(AppendableServerDictMixin, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/licenses"
    _single = LicenseKey
    _basekey = "licenses"

    def _createspec(self, value):
        # When creating a new instance, the server expects an hashmap with the name "key" instead of "licenseKey"
        if isinstance(value, LicenseKey):
            value = value['licenseKey']
        return {'key': value}


class Host(RemoteObjectProxy, attrdict.AttrDict):
    """ A single host returned by Log Insight. """
    class MarshmallowSchema(Schema):
        hostname = fields.Str(missing=None)
        lastReceived = fields.DateTime(attribute='last_received')
        sourcePath = fields.Str(attribute='source', missing=None)


class Hosts(collections.Sequence, ServerAddressableObject):
    """ A Sequence of Host objects returned from Log Insight sorted by their lastReceived property. """
    _baseurl = '/hosts'
    _single = Host
    _basekey = 'hosts'

    def __iter__(self, reverse=False):
        hosts_max = 100000
        sources_max = 100000
        hosts_from = 1
        hosts_to = 200
        sort_order = 'asc' if reverse else 'desc'

        # Iterate over "hosts" and "sources" with upwards of 200 hosts per response.
        # Exit when we've reached both the "hosts" and the "sources" maximums.
        while hosts_from < hosts_max and hosts_from < sources_max:

            # If our "hosts" counters exceeds the "hosts", return an empty list to avoid an unnecessary requests.
            if hosts_from < hosts_max:
                hosts_response = self._connection.post(self._baseurl, json={'loadMissingHosts': False,
                                                                            'from': hosts_from, 'to': hosts_to,
                                                                            'sortOrder': sort_order})
            else:
                hosts_response = {'hosts': []}

            # The same for "sources".
            if hosts_from < sources_max:
                sources_response = self._connection.post(self._baseurl, json={'loadMissingHosts': True,
                                                                              'from': hosts_from, 'to': hosts_to,
                                                                              'sortOrder': sort_order})
            else:
                sources_response = {'hosts': []}

            # Add "hosts" and "sources" lists and sort the results by the "lastReceived" value.
            sorted_objects = sorted(hosts_response['hosts']+sources_response['hosts'],
                                    key=lambda k: k['lastReceived'], reverse=reverse)

            # Yield host objects in the sorted order.
            for host in sorted_objects:
                last_received_in_seconds = int(host['lastReceived']/1000)
                date_format = '%Y-%m-%dT%H:%M:%SZ'
                host['lastReceived'] = datetime.utcfromtimestamp(last_received_in_seconds).strftime(date_format)
                yield Host().from_dict(connection=self._connection, url=self._baseurl, data=host)

            # Increment to the next pages if necessary.
            hosts_from += 200
            hosts_to += 200
            hosts_max = hosts_response['count']
            sources_max = sources_response['count']

    def __len__(self):
        total = 0
        for mode in [True, False]:
            total += int(self._connection.post(self._baseurl, json={'loadMissingHosts': mode})['count'])
        return total

    def __getitem__(self, item):
        # Interleaving the results in the __iter__ may allow us to perform getitem with fewer requests.
        return [host for host in self][item]

    def __reversed__(self):
        return self.__iter__(reverse=True)

    # The __contains__ method was not implemented because host objects on Log Insight do not have an ID. Although the
        # API does accept a searchTerm parameter that could be used to identify hosts by their FQDN or IP, the API will
        # return partial matches. It may be possible for the library to use the hostname or sourcePath properties
        # as identifiers, but then the Hosts and Host class would need to be re-implemented as RemoteObjectProxy type
        # sub-class.
        #
        # Tests using __contains__ will still work. See
        # https://docs.python.org/3.6/reference/datamodel.html#object.__contains__


class Version(StrictVersion, RemoteObjectProxy):
    """
    Server's self-reported current version number.

    Extract a Major.Minor.Patch version number from the server's response,
    and update internal state.

    """
    release_name = None
    prerelease = None
    _url = "/version"

    def __init__(self, version, release_name, **kwargs):
        self.release_name = release_name
        self.vstring, self.build_string = version.split("-", 1)
        super(Version, self).__init__(self.vstring, **kwargs)

    @property
    def build(self):
        """
        Extract build number from version string returned by server.
        Every official build has a distinct, non-repeating build number.
        Higher build numbers do not necessarily indicate a superset of functionality.
        :return: int
        """
        return int(self.build_string)

    class MarshmallowSchema(Schema):
        version = fields.Str()
        releaseName = fields.Str(attribute="release_name")

    __schema__ = MarshmallowSchema


class Dataset(ServerAddressableObject):
    """
    An object, canonically at /datasets/UUID, which defines a set of rules constraining queries.

    Can self-update on property change, if it has a connection and existing UUID.
    Can be appended to a Datasets collection.
    Can be retrieved from a Datasets collection.
    """

    id = None
    name = ""
    description = ""
    type = None
    constraints = None

    def __init__(self, name, description="", id=None, type="OR", constraints=None):
        self.id = id
        self.name = name
        self.description = description
        self.type = type
        self.constraints = Dataset.Constraints(constraints) if constraints else Dataset.Constraints()

    class Constraints(ServerListMixin):
        pass

        class Constraint(ServerAddressableObject):
            name = None
            operator = None
            value = None
            fieldType = "STRING"
            hidden = False


class Datasets(collections.MutableMapping):

    def __init__(self, connection):
        self._connection = connection

    @property
    def _rootobject(self):
        return {dataset['id']: dataset for dataset in self._connection.get('/datasets')['dataSets']}

    def __delitem__(self, key):
        response = self._connection.delete('/datasets/{i}'.format(i=key))
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
        response = self._connection.post('/datasets', data=data)

        if response.ok:
            return None

        else:
            if response.status_code == 400:
                raise TypeError(response.text)
            else:
                raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))


_Role = collections.namedtuple('Role', 'name, description, datasets, capabilities, users')


class Role(_Role):
    def __new__(cls, name, description="", datasets=[], capabilities=[], users=[]):
        if not isinstance(datasets, ServerListMixin):
            datasets = ServerListMixin(datasets)
        if not isinstance(capabilities, ServerListMixin):
            capabilities = ServerListMixin(capabilities)
        if not isinstance(users, ServerListMixin):
            users = ServerListMixin(users)

        self = super(Role, cls).__new__(cls, name, description, datasets, capabilities, users)
        return self


class Roles(collections.MutableMapping):
    def __init__(self, connection):
        self._connection = connection

    @property
    def _rootobject(self):
        return {group['id']: group for group in self._connection.get('/groups')['groups']}

    def __delitem__(self, group_id):
        """ Deletes a role. """

        response = self._connection.delete('/groups/{i}'.format(i=group_id))

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
        response = self._connection.post('/groups', data=data)

        if response.ok:
            pass

        else:
            if response.status_code == 409:
                raise ValueError('A role with the same name value already exists.')
            else:
                raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))


class User(RemoteObjectProxy, attrdict.AttrDict):
    class MarshmallowSchema(BaseSchema):
        __envelope__ = {
            'single': 'user',
            'many': 'users',
        }

        id = fields.Str()
        username = fields.Str()
        password = fields.Str(dump_only=True)
        email = fields.Email(missing="", required=True)
        type = fields.Str()
        apiId = fields.Str()
        groupIds = fields.List(fields.String())
        capabilities = fields.List(fields.String())
        userCapabilities = fields.List(fields.String())
        userDataSets = fields.List(fields.String())
        typeEnum = fields.Str()
    __schema__ = MarshmallowSchema


class Users(AppendableServerDictMixin, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/users"
    _basekey = "users"
    _single = User
    _fetchone = True

    def keys(self):
        return [x['id'] for x in self._iterable]

    def _createspec(self, instance):
        # When creating a new instance, the server expects an hashmap with the name "key" instead of "licenseKey"
        return instance


class Server(object):
    """High-level object representing the capabilities of a remote Log Insight server"""
    _connection = None

    def __init__(self, connection):
        self._connection = connection

    version = ServerProperty(Version, "/version")

    @property
    def is_bootstrapped(self):
        """Convenience function for interogating a server to determine whether it's been bootstrapped already."""

        # Attempt to bootstrap without providing any of the required fields, and inspect the exception
        try:
            response = self._connection.post("/deployment/new", json={})
            raise TransportError("POST {} to /deployment/new should have raised an exception, but didn't", response)
        except ValueError as e:
            if e.args[0] == 400:
                # The server is willing to accept correct field values to bootstrap with, so isn't bootstrapped yet.
                return False
            if e.args[0] == 403:
                # The server is no longer willing to accept POSTs to /deployment/new, because it's already bootstrapped.
                return True
            raise
        raise TransportError(response)

    @property
    def current_session(self):
        resp = self._connection.get("/sessions/current")
        return resp

    @property
    def license(self):
        return LicenseKeys(self._connection)

    @property
    def roles(self):
        return Roles(self._connection)

    @property
    def datasets(self):
        return Datasets(self._connection)

    @property
    def hosts(self):
        return Hosts(self._connection)

    # TODO: Model the server features as properties
