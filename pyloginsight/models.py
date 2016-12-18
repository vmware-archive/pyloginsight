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

import requests
import logging
from requests.compat import urlunparse, urlparse
import collections
from distutils.version import StrictVersion
from .connection import Connection, Unauthorized, ServerError, Credentials
import warnings
import json

logger = logging.getLogger(__name__)


class Server(Connection):
    """High-level object representing the capabilities of a remote Log Insight server"""

    @property
    def version(self):
        """Version number of remote server as a :py:class:: distutils.version.StrictVersion"""
        resp = self._get("/version").json()

        # The "version number" contains build-flags (e.g., build number, "TP") after the dash; ignore them
        # 1.2.3-build.flag.names
        parts = resp.get("version").split("-", 1)
        return StrictVersion(parts[0])

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

    # TODO: Model the server features as properties


class ServerList(collections.Sequence):
    """A server-backed list of items. Can be appended to, sliced, etc.
    Updating an item in the list usually means POST/PUTing a full new list."""
    pass


class ServerDict(collections.MutableMapping):
    """A server-backed dictionary (hashmap) or items, usually keyed by a UUID.
    Adding, deleting or updating an item usually means POST/PUTing a single item's resource."""
    pass


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


class Roles(collections.MutableMapping):

    def __init__(self, connection):
        self._connection = connection

    @property
    def _rootobject(self):
        return {group['id']:group for group in self._connection._get('/groups').json()['groups']}

    def __delitem__(self, group_id):
        """ Deletes a role. """

        if type(group_id) is not str:
            raise TypeError('The group_id value must be a string.')

        try:
            response = self._connection._delete('/groups/{i}'.format(i=group_id))

            if not response.ok:
                if response.status_code == 404:
                    raise KeyError('The specified role does not exist.')
                elif response.status_code == 409:
                    raise KeyError('The specified role is required and cannot be deleted.')
                else:
                    raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))
            else:
                return None

        except Exception as e:
            import sys
            print(sys.exc_info()[1])
            raise e

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

        try:
            data = json.dumps({'name': name, 'description': description, 'capabilities': valid_capabilities})
            response = self._connection._post('/groups', data=data)

            if not response.ok:
                if response.status_code == 409:
                    raise ValueError('A role with the same name value already exists.')
                else:
                    raise SystemError('Operation failed.  Status: {r.status_code!r}, Error: {r.text!r}'.format(r=response))
            else:
                return None

        except Exception as e:
            import sys
            print(sys.exc_info()[1])
