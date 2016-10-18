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

import .model
import requests
import logging

logger = logging.getLogger(__name__)

def default_user_agent():
    return "pyloginsight 0.1"

class ServerError(RuntimeError):
    pass
class Connection(object):
    """Low-level HTTP transport connecting to a remote Log Insight server's API."""
    def __init__(self, server, port=9543, ssl=True, verify=True):
        self._requestsession = requests.Session()
        self._verify = verify
        self._apiroot = '{method}://{server}:{port}/api/v1'.format(method='https' if ssl else 'http', server=server, port=port)
        self.useragent = default_user_agent()
        self.session = None
        self.headers = requests.structures.CaseInsensitiveDict({
            'User-Agent':self.useragent,
            'Content-Type':'application/json'
        })



    def __repr__(self):
        return "Connection({0})".format(self._apiroot)

    def get_session(self):
        return 3

    def connect(self):
        pass

    def version_object(self):
        a = self.get("/version", auth=False)
        o = model.create("Serverversion", a.text)
        return o

    def version(self):
        o = self.version_object()
        parts = getattr(o, "version").split("-",1)
        
        flags = parts[1].split(".")
        build = flags.pop(0)
        
        return "%s %s (build %s)" % (parts[0], o.releaseName, build)

    def trymarshaltype(self, clazzlist, o):
        for t in clazzlist:
            try:
                return model.create(t, o)
            except:
                pass
        return None

    def post(self, url, obj=None, auth=True, params=None):
        if obj:
            obj=obj.serialize()
        authenticationprovider=None
        if auth:
            authenticationprovider=AuthorizationHeaderAuthentication(self.session)
        r = self._requestsession.post(self._apiroot + url, data=obj, verify=self._verify, auth=authenticationprovider, params=params)
        
        if r.status_code != 200:
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
        return r

    def get(self, url, auth=True, params=None):
        authenticationprovider=None
        if auth:
            authenticationprovider=AuthorizationHeaderAuthentication(self.session)
        return self._requestsession.get(self._apiroot + url, verify=self._verify, auth=authenticationprovider, params=params)

    def login(self, **kwargs):
        o = model.get("Createsession")(**kwargs)

        #o.serialize()
        a = self.post("/sessions", obj=o, auth=False)
        
        ro = self.trymarshaltype(["Activesession"], a.text)
        self.session = ro
        return ro

    def is_unbootstrapped(self):
        return not self.is_bootstrapped()
    def is_bootstrapped(self):
        """Convenience function for interogating a server to determine whether it's been bootstrapped already."""
        try:
            a = self.post("/deployment/new")
        except:
            raise

class AuthorizationHeaderAuthentication(requests.auth.AuthBase):
    def __init__(self, session):
        self.session=session
    def __call__(self, r):
        # Implement my authentication
        r.headers.update({"Authorization": "Bearer %s" % self.session.sessionId})
        return r