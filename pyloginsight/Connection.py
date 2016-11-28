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


logger = logging.getLogger(__name__)


def default_user_agent():
    return "pyloginsight 0.1"


class ServerError(RuntimeError):
    pass


class Unauthorized(ServerError):
    pass


class Server(object):
    """Low-level HTTP transport connecting to a remote Log Insight server's API."""

    def __init__(self, hostname, port=9543, ssl=True, verify=True):
        self._requestsession = requests.Session()
        self._hostname = hostname
        self._port = port
        self._ssl = ssl
        self._verify = verify

        self._apiroot = '{method}://{hostname}:{port}/api/v1'.format(method='https' if ssl else 'http',
                                                                     hostname=hostname, port=port)
        self.useragent = default_user_agent()
        self.headers = requests.structures.CaseInsensitiveDict({
            'User-Agent': self.useragent,
            'Content-Type': 'application/json'
        })
        logging.debug("Connected to {0}".format(self))

    def __repr__(self):
        return "Server({0})".format(repr(self._apiroot))

    @property
    def version(self):
        """Retrieve version number of remote server"""
        from distutils.version import StrictVersion
        # distutils isn't lightweight; don't import it unless needed

        resp = self.get("/version").json()

        # The "version number" contains build-flags (e.g., build number, "TP") after the dash; ignore them
        # 1.2.3-build.flag.names
        parts = resp.get("version").split("-", 1)
        return StrictVersion(parts[0])

    def post(self, url, obj=None, auth=True, params=None):
        if obj:
            obj = obj.serialize()
        r = self._requestsession.post(self._apiroot + url, data=obj, verify=self._verify, params=params)

        if r.status_code != 200:
            raise NotImplementedError("Implement marshaling of result datatypes")
            """
            o = self.trymarshaltype(["Serveralreadybootstrapped"], r.text)
            if o:
                raise ServerError(o)
            try:
                # attempt to marshal the result to a known exception
                print(r.text)
                o = model.create("Servererror", r.text)
                raise ServerError(str(o.as_dict()))
            except:
                raise
            """
        return r

    def get(self, url, params=None):
        return self._requestsession.get(self._apiroot + url, verify=self._verify, params=params)

    def login(self, username, password, provider):
        return AuthenticatedServer.from_server(server=self,
                                               auth=AuthorizationHeaderAuthentication(username=username, password=password, provider=provider))

    def is_bootstrapped(self):
        """Convenience function for interogating a server to determine whether it's been bootstrapped already."""
        raise NotImplementedError("TODO: Determine whether the server is already bootstrapped")
        try:
            self.post("/deployment/new")
            return False
        except:
            return True


class AuthorizationHeaderAuthentication(requests.auth.AuthBase):
    """An authorization header, with bearer token, is included in each HTTP request.
    Based on http://docs.python-requests.org/en/master/_modules/requests/auth/"""
    server = None

    def __init__(self, server, username, password, provider, sessionId=None, reuse_session=None):
        """If passed an existing sessionId, try to use it."""
        self.server = server  # Server object, from which we consume apiroot, session, _verify
        self.username = username
        self.password = password
        self.provider = provider
        self.sessionId = sessionId  # hNhXgAM1xrl...
        self.requests_session = reuse_session or requests.Session()

    def get_session(self):
        """Perform a session login and return a live session ID."""
        if self.username is None or self.password is None:
            raise RuntimeError("Cannot authenticate without username/password")
        logging.info("Attempting to authenticate as {0}".format(self.username))
        # This inner request does not pass auth=self, and it does not recurse.
        authdict = {"username": self.username, "password": self.password, "provider": self.provider}

        # TODO: This is probably a bad pattern. Reconsider the way it reaches into the Server object.
        authresponse = self.server._requestsession.post(self.server._apiroot + "/sessions", json=authdict, verify=self.server._verify)

        try:
            return authresponse.json()['sessionId']
        except:
            raise Unauthorized("Authentication failed", authresponse)

    def handle_401(self, r, **kwargs):
        # method signature matches requests.Request.register_hook

        # Is it possible for a non-401 to end up here?
        assert r.status_code == 401

        self.sessionId = self.get_session()

        # Now that we have a good session, copy and retry the original request. If it fails again, raise Unauthorized.
        r.content
        r.close()
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

        # Attempt the request. If it fails with a 401, generate a new sessionId
        r.register_hook('response', self.handle_401)
        # r.register_hook('response', self.handle_redirect)
        return r


class AuthenticatedServer(Server):
    """Attempts requests to the server which require authentication. If requests fail with HTTP 401 Unauthorized,
    obtains a session bearer token and retries the request."""
    _auth = None
    _server = None
    bearertoken = None

    def __init__(self, hostname, port=9543, ssl=True, verify=True, auth=None):
        Server.__init__(self, hostname, port, ssl, verify)

        if auth:
            auth.server = self
        self._authprovider = auth

    @classmethod
    def from_server(cls, server, auth=None):
        return cls(server._hostname, server._port, server._ssl, server._verify, auth)

    def post(self, url, data=None, params=None):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        r = self._requestsession.post(self._apiroot + url,
                                      data=data,
                                      verify=self._verify,
                                      auth=self._authprovider,
                                      params=params)
        return r

    def get(self, url, params=None):
        return self._requestsession.get(self._apiroot + url,
                                        verify=self._verify,
                                        auth=self._authprovider,
                                        params=params)


class AuthenticatedRequest(object):
    pass
