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

# from . import model
import requests
import logging
from requests.compat import urlunparse, urlparse
import collections
from distutils.version import StrictVersion
from . import __version__ as version


logger = logging.getLogger(__name__)
APIV1 = '/api/v1'


def default_user_agent():
    return "pyloginsight/{0}".format(version)


class ServerError(RuntimeError):
    pass


class Unauthorized(ServerError):
    pass


class Credentials(requests.auth.AuthBase):
    """An authorization header, with bearer token, is included in each HTTP request.
    Based on http://docs.python-requests.org/en/master/_modules/requests/auth/"""

    def __init__(self, username, password, provider, sessionId=None, reuse_session=None):
        """If passed an existing sessionId, try to use it."""
        self.username = username
        self.password = password
        self.provider = provider
        self.sessionId = sessionId  # An existing session id, like "hNhXgAM1xrl..."
        self.requests_session = reuse_session or requests.Session()

    def get_session(self, previousresponse, **kwargs):
        """Perform a session login and return a new session ID."""
        if self.username is None or self.password is None:
            raise RuntimeError("Cannot authenticate without username/password")
        logging.info("Attempting to authenticate as {0}".format(self.username))
        authdict = {"username": self.username, "password": self.password, "provider": self.provider}

        prep = previousresponse.request.copy()
        try:
            del prep.headers['Authorization']
        except KeyError:
            pass  # Better to ask for forgiveness than to look before you leap
        if 'Authorization' in prep.headers:
            del prep.headers['Authorization']

        prep.prepare_method("post")
        print(previousresponse)
        print(previousresponse.request)
        print(dir(previousresponse.request))

        p = urlparse(previousresponse.request.url)
        prep.prepare_url(urlunparse([p.scheme,
                                     p.netloc,
                                     APIV1 + "/sessions",
                                     None,
                                     None,
                                     None]), params=None)

        prep.prepare_body(data=None, files=None, json=authdict)
        authresponse = previousresponse.connection.send(prep, **kwargs)  # kwargs contains ssl _verify
        try:
            return authresponse.json()['sessionId']
        except:
            raise Unauthorized("Authentication failed", authresponse)

    def handle_401(self, r, **kwargs):
        # method signature matches requests.Request.register_hook

        # Is it possible for a non-401 to end up here?
        if r.status_code != 401:
            logging.warning("Got a non-400 status %d in handle_401" % r.status_code)
            return r

        assert r.status_code == 401

        r.content  # Drain previous response body, if any
        r.close()

        self.sessionId = self.get_session(r, **kwargs)

        # Now that we have a good session, copy and retry the original request. If it fails again, raise Unauthorized.
        prep = r.request.copy()
        prep.headers.update({"Authorization": "Bearer %s" % self.sessionId})
        _r = r.connection.send(prep, **kwargs)
        _r.history.append(r)
        _r.request = prep

        if _r.status_code == 401:
            raise Unauthorized("Authentication failed", _r)
        logging.debug("Authenticated successfully.")
        return _r

    def __call__(self, r):
        if self.sessionId:
            # If we already have a Session ID Bearer Token, try to use it.
            r.headers.update({"Authorization": "Bearer %s" % self.sessionId})

        # TODO: If the TTL has expired, or we have no Bearer token at all, we can reasonably expect this
        # TODO.cont: request to fail with 401. In both cases, we could avoid a round-trip to the server.
        # TODO.cont: This is an optimization and does not materially affect success.

        # Attempt the request. If it fails with a 401, generate a new sessionId
        r.register_hook('response', self.handle_401)
        return r

    def __repr__(self):
        return '{cls}(username={x.username!r}, password=..., provider={x.provider!r})'.format(cls=self.__class__.__name__, x=self)


class Connection(object):
    """Low-level HTTP transport connecting to a remote Log Insight server's API.
    Attempts requests to the server which require authentication. If requests fail with HTTP 401 Unauthorized,
    obtains a session bearer token and retries the request.
    You should probably use the :py:class:: Server class instead"""

    def __init__(self, hostname, port=9543, ssl=True, verify=True, auth=None, existing_session=None):
        self._requestsession = existing_session or requests.Session()
        self._hostname = hostname
        self._port = port
        self._ssl = ssl
        self._verify = verify
        self._authprovider = auth

        self._apiroot = '{method}://{hostname}:{port}{apiv1}'.format(method='https' if ssl else 'http',
                                                                     hostname=hostname, port=port, apiv1=APIV1)

        self._requestsession.headers.update({'User-Agent': default_user_agent()})
        logging.debug("Connected to {0}".format(self))

    def _post(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        r = self._requestsession.post(self._apiroot + url,
                                      data=data,
                                      json=json,
                                      verify=self._verify,
                                      auth=self._authprovider if sendauthorization else None,
                                      params=params)
        return r

    def _get(self, url, params=None, sendauthorization=True):
        return self._requestsession.get(self._apiroot + url,
                                        verify=self._verify,
                                        auth=self._authprovider if sendauthorization else None,
                                        params=params)

    def _delete(self, url, params=None, sendauthorization=True):
        return self._requestsession.delete(self._apiroot + url,
                                           verify=self._verify,
                                           auth=self._authprovider if sendauthorization else None,
                                           params=params)

    def _put(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        r = self._requestsession.put(self._apiroot + url,
                                     data=data,
                                     json=json,
                                     verify=self._verify,
                                     auth=self._authprovider if sendauthorization else None,
                                     params=params)
        return r

    def _patch(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        r = self._requestsession.patch(self._apiroot + url,
                                       data=data,
                                       json=json,
                                       verify=self._verify,
                                       auth=self._authprovider if sendauthorization else None,
                                       params=params)
        return r

    def __repr__(self):
        """Human-readable and machine-executable description of the current connection."""
        return '{cls}(hostname={x._hostname!r}, port={x._port!r}, ssl={x._ssl!r}, verify={x._verify!r}, auth={x._authprovider!r})'.format(cls=self.__class__.__name__, x=self)

    @property
    def server(self):
        return Server.copy_connection(self)

    @classmethod
    def copy_connection(cls, connection):
        return cls(hostname=connection._hostname,
                   port=connection._port,
                   ssl=connection._ssl,
                   verify=connection._verify,
                   auth=connection._authprovider,
                   existing_session=connection._requestsession)


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

    # TODO: Model the server features as properties


class ServerList(collections.Sequence):
    """A server-backed list of items. Can be appended to, sliced, etc.
    Updating an item in the list usually means POST/PUTing a full new list."""
    pass


class ServerDict(collections.MutableMapping):
    """A server-backed dictionary (hashmap) or items, usually keyed by a UUID.
    Adding, deleting or updating an item usually means POST/PUTing a single item's resource."""
    pass
