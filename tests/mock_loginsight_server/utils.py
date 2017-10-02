# -*- coding: utf-8 -*-
from functools import wraps
import logging
import uuid
import re
from collections import namedtuple

mockserverlogger = logging.getLogger(__name__)


def uuid_url_matcher(base):
    return re.compile('/api/v1/' + base + '/([a-f0-9-]+)$')


User = namedtuple("User", field_names=["username", "password", "type", "email"])
Session = namedtuple("Session", field_names=["userId", "ttl", "created"])


class RandomDict(dict):
    """Subclass of `dict` that adds a list-like `append` method that generates a random UUID key"""
    def append(self, value):
        key = str(uuid.uuid4())
        while key in self:
            key = str(uuid.uuid4())
        self[key] = value
        return key


def requiresauthentication(fn):
    """Server mock; fail any request which does not contain the expected Authorization header with HTTP/401"""
    @wraps(fn)
    def wrapper(self, request, context, *args, **kwargs):
        session_id = request.headers.get('Authorization', "")[7:]
        if session_id in self.sessions_known:  # TODO: Don't ignore TTL
            mockserverlogger.info("Verified bearer has a valid sessionId")
            return fn(self, request=request, context=context, session_id=session_id, user_id=self.sessions_known[session_id].userId, *args, **kwargs)
        context.status_code = 401
        return ""
    return wrapper


def guid(fn):
    """Server mock; grab the object guid from the url"""
    @wraps(fn)
    def wrapper(self, request, context, *args, **kwargs):
        guid = uuid_url_matcher('[^/]+').match(request.path).group(1)
        return fn(self, request=request, context=context, guid=guid, *args, **kwargs)

    return wrapper
