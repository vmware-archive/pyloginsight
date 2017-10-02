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
from .abstracts import ServerAddressableObject, AppendableServerDictMixin, ServerDictMixin, DirectlyAddressableContainerMapping
from .abstracts import ServerProperty, RemoteObjectProxy, ObjectSchema, EnvelopeObjectSchema, bind_to_model
import attrdict
from marshmallow import fields
from .exceptions import TransportError
from datetime import datetime
import collections


logger = logging.getLogger(__name__)


class LicenseKey(RemoteObjectProxy, attrdict.AttrDict):
    """A single license key for Log Insight."""


@bind_to_model
class LicenseKeySchema(EnvelopeObjectSchema):
    __envelope__ = {
        'single': 'licenseKey',
        'many': 'licenses',
        'append': lambda x: {'key': x['licenseKey']}  # When creating a new instance, the server expects an hashmap with the name "key" instead of "licenseKey"
    }
    __model__ = LicenseKey
    id = fields.Str()
    error = fields.Str(load_only=True)
    status = fields.Str(load_only=True)
    configuration = fields.Str(load_only=True)
    expiration = fields.Raw(load_only=True)
    licenseKey = fields.Str()
    infinite = fields.Raw(load_only=True)
    count = fields.Integer(load_only=True)
    typeEnum = fields.Str(load_only=True)


class LicenseKeys(AppendableServerDictMixin, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/licenses"
    _single = LicenseKey
    _schema = LicenseKeySchema
    _basekey = "licenses"


class Host(RemoteObjectProxy, attrdict.AttrDict):
    """ A single host returned by Log Insight. """


@bind_to_model
class HostSchema(ObjectSchema):
    __model__ = Host
    hostname = fields.Str(missing=None)
    lastReceived = fields.DateTime(attribute='last_received')
    sourcePath = fields.Str(attribute='source', missing=None)


class Hosts(collections.Sequence, ServerAddressableObject):
    """ A Sequence of Host objects returned from Log Insight sorted by their lastReceived property. """
    _baseurl = '/hosts'
    _single = Host
    _basekey = 'hosts'

    def __iter__(self, sort_order='desc'):
        assert sort_order in ['desc', 'asc']
        hosts = []

        for mode in [True, False]:
            maximum = 100000
            hosts_from = 1
            hosts_to = 200
            while hosts_from < maximum:
                response = self._connection.post(self._baseurl, json={'loadMissingHosts': mode,
                                                                      'from': hosts_from, 'to': hosts_to,
                                                                      'sortOrder': sort_order})
                hosts += response['hosts']
                hosts_from += 200
                hosts_to += 200
                maximum = response['count']

        for host in sorted(hosts, key=lambda k: k['lastReceived'], reverse=True if sort_order == 'desc' else False):
            last_received_in_seconds = int(host['lastReceived'] / 1000)
            date_format = '%Y-%m-%dT%H:%M:%SZ'
            host['lastReceived'] = datetime.utcfromtimestamp(last_received_in_seconds).strftime(date_format)
            yield Host.from_dict(connection=self._connection, url=None, data=host)

    def __len__(self):
        total = 0
        for mode in [True, False]:
            total += int(self._connection.post(self._baseurl, json={'loadMissingHosts': mode})['count'])
        return total

    def __getitem__(self, item):
        # Interleaving the results in the __iter__ may allow us to perform getitem with fewer requests.
        return [host for host in self][item]

    def __reversed__(self):
        return self.__iter__(sort_order='asc')

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


@bind_to_model
class VersionSchema(ObjectSchema):
    __model__ = Version
    version = fields.Str()
    releaseName = fields.Str(attribute="release_name")


class Dataset(RemoteObjectProxy, attrdict.AttrDict):
    """
    An object, canonically at /datasets/UUID, which defines a set of rules constraining queries.

    Can sent itself back to the server, if it has a connection and existing UUID.
    Can be appended to a Datasets collection.
    Can be retrieved from a Datasets collection.

    class Constraints(ServerListMixin):
        pass

        class Constraint(ServerAddressableObject):

            name = None
            operator = None
            value = None
            fieldType = "STRING"
            hidden = False
    """


@bind_to_model
class DatasetSchema(EnvelopeObjectSchema):
    __envelope__ = {
        'single': 'dataSet',
        'many': 'dataSets',
    }
    __model__ = Dataset
    id = fields.Str()
    name = fields.Str()
    description = fields.Str()
    type = fields.Str()
    constraints = fields.List(fields.Dict())


class Datasets(AppendableServerDictMixin, DirectlyAddressableContainerMapping, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/datasets"
    _single = Dataset
    _schema = DatasetSchema
    _basekey = "dataSets"

    _fetchone = True


class Group(RemoteObjectProxy, attrdict.AttrDict):
    """
    An object, canonically at /groups/UUID, which defines a set of users granted Capabilities or view to Datasets.
    Compatible with Log Insight 4.5 and earlier. Deprecated - use `Roles` instead.
    """

# 2017-07-25 c06fa5f3be67e7981ebdcc7cc094c1c5ace14f00
# Updated the existing /groups API to /roles API


@bind_to_model
class GroupSchema(EnvelopeObjectSchema):
    __envelope__ = {
        'single': 'dataSet',
        'many': 'dataSets',
    }
    __model__ = Dataset
    id = fields.Str()
    name = fields.Str()
    description = fields.Str()
    type = fields.Str()
    capabilities = fields.List(fields.Dict())
    # users?


class Groups(AppendableServerDictMixin, DirectlyAddressableContainerMapping, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/groups"
    _single = Group
    _schema = GroupSchema


class Role(RemoteObjectProxy, attrdict.AttrDict):
    pass


@bind_to_model
class RoleSchema(EnvelopeObjectSchema):
    __envelope__ = {
        'single': 'user',
        'many': 'users',
        'append': lambda x: x['user']
    }
    __model__ = Role
    id = fields.Str()
    username = fields.Str()
    password = fields.Str(dump_only=True)
    email = fields.Email(missing=None, required=False)
    type = fields.Str()
    apiId = fields.Str()
    groupIds = fields.List(fields.String())
    capabilities = fields.List(fields.String())
    userCapabilities = fields.List(fields.String())
    userDataSets = fields.List(fields.String())
    typeEnum = fields.Str()


class Roles(AppendableServerDictMixin, DirectlyAddressableContainerMapping, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/roles"
    _single = Role
    _schema = RoleSchema


class User(RemoteObjectProxy, attrdict.AttrDict):
    def to_server(self, connection, url=None):
        """
        The instance validates & serializes itself, then writes back to the server at an existing URL with POST.
        Alternatively, replace the existing instance in the collection with this instance, `d[k]=instance`.
        To create a new server-side entity, add this instance to a collection, `d.append(instance)`.
        """
        if url is None:
            url = str(object.__getattribute__(self, "__url"))
            if url is None:
                raise AttributeError("Cannot submit object to server without a url")

        return connection.post(url, json=self._serialize()['user'])


class NullableStringField(fields.Str):
    def _serialize(self, value, attr, obj):
        if value is None:
            return ''
        return value

    def _deserialize(self, value, attr, data):
        if value == '':
            return None
        return value


@bind_to_model
class UserSchema(EnvelopeObjectSchema):

    __envelope__ = {
        'single': 'user',
        'many': 'users',
        'append': lambda x: x['user'],
    }
    __model__ = User
    id = fields.Str()
    username = fields.Str()
    password = fields.Str(dump_only=True)
    email = NullableStringField(missing=None, required=False, allow_none=True)  # Can we use fields.Email, but allow zero-length strings (or treat them as None)?
    type = fields.Str(missing="DEFAULT")
    apiId = fields.Str()
    groupIds = fields.List(fields.String())
    capabilities = fields.List(fields.String())
    userCapabilities = fields.List(fields.String())
    userDataSets = fields.List(fields.String())
    typeEnum = fields.Str()


class Users(AppendableServerDictMixin, DirectlyAddressableContainerMapping, ServerDictMixin, ServerAddressableObject):
    _baseurl = "/users"
    _single = User
    _schema = UserSchema


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
    def groups(self):
        return Groups(self._connection)

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
