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
import sys
import logging
import json

try:
    from . import __version__
except:
    __version__="0"

def Connect(server, username, password, port=None, ssl=True):
    if not port:
        port = 443 if ssl else 9000

    connection = Connection()


def default_user_agent(name="pyLogInsight"):
    return '%s/%s' % (name, __version__)

class AuthenticatedSession(object):
    sessionId = ""
    expiry = 0



def marshalerror(struct):
    pass

class ApiError(RuntimeError):
    pass
class BootstrapCompleted(RuntimeError):
    pass
class BootstrapNeeded(RuntimeError):
    pass
class ValidationError(RuntimeError):
    """
    The client submitted a request body which the server claims is incorrectly formatted.

    {
        "errorMessage":"Some fields have incorrect values",
        "errorCode":"FIELD_ERROR",
        "errorDetails":{
            "user":[
                    {
                        "errorCode":"com.vmware.loginsight.api.errors.field_required",
                        "errorMessage":"Required value is null"
                    }
                ]
        }
    }
    """
    def __init__(self, payload):
        self.payload = payload
    def __str__(self):
        return str(self.payload)

class Resource(object):
    """All resource fields are optional. If the client or serverdoesn't understand a field,
    it can be safely ignored. If the server requires a field, raise ValidationError."""
    _resource = None
    _changedattributes = {}

    def __init__(self, connection, resource=None):
        self._connection = connection
        self._changedattributes = {}
        if resource:
            self._resource = resource
    def __repr__(self):
        return "{0}: {1}".format(self._resource, str(self._serialize()))
    def _serialize(self):
        return {k:v for k,v in vars(self).items()+vars(self.__class__).items() if not k.startswith("_")}

    def blank(self):
        self._changedattributes = {}
        for k in vars(self):
            if not k.startswith("_"):
                logging.debug("Blanking key " + k)
                delattr(self, k)

    def __setattr__(self, name, value):
        if not name.startswith("_") and hasattr(self,name) and getattr(self, name):
            self._changedattributes[name]=True
            logging.debug("{0} property {1} changed from {2} to {3}".format(self._resource, name, getattr(self, name), value))
        return object.__setattr__(self, name, value)

    def _put(self):
        headers = self._connection.headers
        if hasattr(self,'_getheaders') and callable(self._getheaders):
            headers = dict(headers, **self._getheaders())
        logging.debug("_post to {0}: {1} with headers {2}".format(self._resource, self._serialize(), headers))
        r = self._connection._requestsession.post(
                self._connection._apiroot+self._resource,
                headers=headers,
                verify=self._connection._verify,
                json=self._serialize())
        if r.status_code == 400:
            raise ValidationError(r.json())
        return r.json()

    def _get(self, connection, resource):
        self._requestsession.get(
            self._apiroot+self._resource,
            verify=self.verify)
        #TODO: clear self._changedattributes

    def save(self):
        #TODO: support patch
        self._put()

class UnauthenticatedResource(Resource):
    pass

class AuthenticatedResource(Resource):
    def _getheaders(self):
        return {'X-LI-Session-Id':self._connection.get_session()}

class EmptyRequest(UnauthenticatedResource):
    foo = str()
    def __init__(self, connection, resource=None):
        super(EmptyRequest, self).__init__(connection=connection, resource=resource)


class NewDeployment(UnauthenticatedResource):
    _resource = '/deployment/new'

    user = {"a":str()}
    userName = str()
    email = str()
    password = str()


class Deployment(object):
    """
    Bootstraps a new Log Insight server node.

    Prior to bootstrap, a server node does not store data, perform authentication or participate in a cluster. Bootstrap creates local databases and configuration. A server node takes some amount of time to perform a bootstrap operation. A second bootstrap request during this window will fail.
    """
    def __init__(connection):
        self.connection = connection
    def is_unbootstrapped(self):
        pass
    def is_bootstrapped(self):
        """Convenience function for interogating a server to determine whether it's been bootstrapped already."""

        pass
    def new(self, username, password, email=""):
        pass
    def join_cluster(self, master, port=16520):
        """Join this node to another, forming a cluster."""
    def approve(self):
        pass
    def wait_for_bootstrap(self):
        pass


from collections import MutableMapping

class ServerSingleton(object):
    pass # TODO

class ServerCollection(MutableMapping):
    def __init__(self, connection, baseurl, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        print "__getitem__(",key,")"
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        print "__setitem__(",key,")"
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        print "__delitem__(",key,")"
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key

    def invalidatecache(self):
        return True

def main(q):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    #c = Connection('8.43.192.236', verify=False)
    #c = Connection('localhost', verify=False)
    #print c

    #a = NewDeployment(c)
    #a.blank()
    #a._post()

    c = ServerCollection(None, None)
    d = {"e":True}
    c['d'] = d

    print "c", c
    for _ in c:
        print "_", _, c[_]

    del d
    #del c['d']
    c = None
if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    main(query)
