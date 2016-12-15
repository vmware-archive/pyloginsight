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

