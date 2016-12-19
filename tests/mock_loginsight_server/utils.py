from functools import wraps
import logging
import uuid
import re
from collections import namedtuple

mockserverlogger = logging.getLogger(__name__)


trailing_guid_pattern = re.compile('.*/([a-f0-9-]+)$')
license_url_matcher = re.compile('/api/v1/licenses/([a-f0-9-]+)$')


User = namedtuple("User", field_names=["username", "password", "provider", "userId"])
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
    def wrapper(self, request, context):
        session_id = request.headers.get('Authorization', "")[7:]
        if session_id in self.sessions_known:  # TODO: Don't ignore TTL
            mockserverlogger.info("Verified bearer has a valid sessionId")
            return fn(self, request, context, session_id, self.sessions_known[session_id].userId)
        context.status_code = 401
        return ""
    return wrapper
