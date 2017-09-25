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

from requests.compat import urlunparse, urlparse
from . import __version__ as version

import requests
import logging
import warnings
from .exceptions import ResourceNotFound, TransportError, Unauthorized, ServerWarning, NotBootstrapped, AlreadyBootstrapped

from .models import Server

logger = logging.getLogger(__name__)
APIV1 = '/api/v1'


def default_user_agent():
    return "pyloginsight/{0}".format(version)


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
            raise Unauthorized("Cannot authenticate without username/password")
        logger.info("Attempting to authenticate as {0}".format(self.username))
        authdict = {"username": self.username, "password": self.password, "provider": self.provider}

        prep = previousresponse.request.copy()
        try:
            del prep.headers['Authorization']
        except KeyError:
            pass  # Better to ask for forgiveness than to look before you leap
        if 'Authorization' in prep.headers:
            del prep.headers['Authorization']

        prep.prepare_method("post")
        p = urlparse(previousresponse.request.url)
        prep.prepare_url(urlunparse([p.scheme,
                                     p.netloc,
                                     APIV1 + "/sessions",
                                     None,
                                     None,
                                     None]), params=None)

        logger.debug("Authenticating via url: {0}".format(prep.url))
        prep.prepare_body(data=None, files=None, json=authdict)
        authresponse = previousresponse.connection.send(prep, **kwargs)  # kwargs contains ssl _verify
        try:
            return authresponse.json()['sessionId']
        except:
            if authresponse.status_code == 503 and 'should be bootstrapped' in authresponse.json().get('errorMessage', ''):
                raise NotBootstrapped(authresponse.json().get('errorMessage'), authresponse)
            raise Unauthorized("Authentication failed", authresponse)

    def handle_401(self, r, **kwargs):
        # method signature matches requests.Request.register_hook

        if r.status_code not in [401, 440]:
            return r

        logger.debug("Not authenticated (got status {r.status_code} @ {r.request.url})".format(r=r))
        r.content  # Drain previous response body, if any
        r.close()

        self.sessionId = self.get_session(r, **kwargs)

        # Now that we have a good session, copy and retry the original request. If it fails again, raise Unauthorized.
        prep = r.request.copy()
        prep.headers.update({"Authorization": "Bearer %s" % self.sessionId})
        _r = r.connection.send(prep, **kwargs)
        _r.history.append(r)
        _r.request = prep

        if _r.status_code in [401, 440]:
            raise Unauthorized("Authentication failed", _r)
        logger.debug("Authenticated successfully.")
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
        logger.debug("Connected to {0}".format(self))

    @classmethod
    def copy_connection(cls, connection):
        warnings.warn("copy_connection is deprecated.")
        return cls(hostname=connection._hostname,
                   port=connection._port,
                   ssl=connection._ssl,
                   verify=connection._verify,
                   auth=connection._authprovider,
                   existing_session=connection._requestsession)

    def _call(self, method, url, data=None, json=None, params=None, sendauthorization=True):
        logger.debug("{} {} data={} json={} params={}".format(method, url, data, json, params))

        r = self._requestsession.request(method=method,
                                         url="%s%s" % (self._apiroot, url),
                                         data=data,
                                         json=json,
                                         verify=self._verify,
                                         auth=self._authprovider if sendauthorization else None,
                                         params=params)

        if 'Warning' in r.headers:
            if 'VMware-LI-API-Status' in r.headers:
                warnings.warn("Log Insight API resource {} {} is {}".format(method, url, r.headers['VMware-LI-API-Status']),
                              ServerWarning,
                              stacklevel=5)
            else:
                warnings.warn(r.headers.get('Warning'))

        try:
            payload = r.json()
        except:
            payload = r.text

        if r.status_code in [401, 440]:
            raise Unauthorized(r.status_code, payload)
        if r.status_code in [404]:
            raise ResourceNotFound(r.status_code, payload)

        """
        if r.status_code in [200, 201]:
            try:
                if payload.keys() == ['id']:  # if there is only one key in the response, and it's "id", return it
                    return payload['id']
            except (KeyError, AttributeError):
                return True
        """

        logger.debug("{} {}: status_code[{}]: {}".format(method, url, r.status_code, payload))

        # Success
        if 200 <= r.status_code < 300:
            return payload

        # Failure. We're going to throw an exception. Try to harvest an errorMessage from the response.

        try:
            error_message = payload['errorMessage']
        except (TypeError, KeyError):
            error_message = None
        try:
            error_message = payload['errorDetails']
        except (TypeError, KeyError):
            error_message = None

        if r.status_code == 418:
            raise NotImplementedError("{} {}: {}".format(method, url, payload))

        if error_message:
            raise ValueError(r.status_code, error_message)
        else:
            raise TransportError(r.status_code, payload)

    def post(self, url, data=None, json=None, params=None, sendauthorization=True):
        """
        Attempt to post to server with current authorization credentials.
        If post fails with HTTP 401 Unauthorized, authenticate and retry.
        """
        return self._call(method="POST",
                          url=url,
                          data=data,
                          json=json,
                          sendauthorization=sendauthorization,
                          params=params)

    def get(self, url, params=None, sendauthorization=True):
        return self._call(method="GET",
                          url=url,
                          sendauthorization=sendauthorization,
                          params=params)

    def delete(self, url, params=None, sendauthorization=True):
        return self._call(method="DELETE",
                          url=url,
                          sendauthorization=sendauthorization,
                          params=params)

    def put(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        return self._call(method="PUT",
                          url=url,
                          data=data,
                          json=json,
                          sendauthorization=sendauthorization,
                          params=params)

    def patch(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        return self._call(method="PATCH",
                          url=url,
                          data=data,
                          json=json,
                          sendauthorization=sendauthorization,
                          params=params)

    def __repr__(self):
        """Human-readable and machine-executable description of the current connection."""
        return '{cls}(hostname={x._hostname!r}, port={x._port!r}, ssl={x._ssl!r}, verify={x._verify!r}, auth={x._authprovider!r})'.format(cls=self.__class__.__name__, x=self)

    @property
    def server(self):
        return Server(self)

    def bootstrap(self, email=''):
        """
        :param email: optional email for the administrator's account
        :return:
        """

        if self._authprovider.password is None:
            import uuid
            self._authprovider.password = str(uuid.uuid4())

        deployment_payload = {
            'user': {
                'userName': self._authprovider.username,
                'password': self._authprovider.password,
                'email': email
            }
        }

        # Directly call without sending an authorization header
        try:
            self._call(
                method="POST",
                url="/deployment/new",
                json=deployment_payload,
                sendauthorization=False)
        except TransportError as e:
            if e.args[0] == 403:
                raise AlreadyBootstrapped(e)

        logging.info("Bootstrap has started, but it might take a while for server to start.")
        self.wait_until_started()

    def wait_until_started(self):
        self._call(
            method="POST",
            url="/deployment/waitUntilStarted"
        )
        logging.info("Server is started.")
