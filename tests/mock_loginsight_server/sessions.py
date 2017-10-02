# -*- coding: utf-8 -*-
import json
import logging
import time

from .utils import RandomDict, requiresauthentication, User, Session, uuid_url_matcher, guid

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class MockedSessionsMixin(object):
    def __init__(self, **kwargs):
        super(MockedSessionsMixin, self).__init__(**kwargs)

        self.sessions_known = RandomDict()
        self.users_known = RandomDict()
        self.users_known["012345678-9ab-cdef-0123-456789abcdef"] = User('admin', 'VMware123!', 'Local', "admin@example.com")

        self.register_uri('POST', '/api/v1/sessions', text=self.session_new, status_code=200)
        self.register_uri('GET', '/api/v1/sessions/current', text=self.session_current, status_code=200)

        self.register_uri('GET', '/api/v1/users', text=self.callback_user_list, status_code=200)
        self.register_uri('POST', '/api/v1/users', text=self.callback_user_create, status_code=200)
        self.register_uri('GET', uuid_url_matcher('users'), text=self.callback_user_get, status_code=200)
        self.register_uri('DELETE', uuid_url_matcher('users'), text=self.callback_user_delete, status_code=200)
        self.register_uri('POST', uuid_url_matcher('users'), text=self.callback_user_update, status_code=200)

    @requiresauthentication
    def session_current(self, request, context, session_id, user_id):
        """Attempt to create a new session with provided credentials."""
        return json.dumps(self.sessions_known[session_id]._asdict())

    def session_new(self, request, context):
        """Attempt to create a new session with provided credentials."""
        self.session_timeout()
        attempted_credentials = request.json()
        for k, u in self.users_known.items():
            if u.username == attempted_credentials['username'] and u.type == attempted_credentials['provider']:
                if u.password == attempted_credentials['password']:
                    mockserverlogger.info("Successful authentication as {u.username} = {k}".format(k=k, u=u))
                    context.status_code = 200
                    sessionId = self.sessions_known.append(Session(k, 1800, time.time()))
                    return json.dumps({"userId": k, "sessionId": sessionId, "ttl": 1800})
                else:  # wrong password, bail out
                    mockserverlogger.warning("Correct username but invalid password (which is OK to say, because this is a mock)")
                    break
        context.status_code = 401
        return json.dumps({"errorMessage": "Invalid username or password.", "errorCode": "FIELD_ERROR"})

    def session_timeout(self):
        """Reap any expired (TTL) sessions"""
        for sessionId in self.sessions_known:
            if (time.time() - self.sessions_known[sessionId].created) > self.sessions_known[sessionId].ttl:
                mockserverlogger.warning("Session {0} expired".format(sessionId))
                del self.sessions_known[sessionId]

    def session_inspection_user_list(self):
        return set([usersession.userId for usersession in self.sessions_known.values()])

    @requiresauthentication
    def callback_user_list(self, request, context, session_id, user_id):
        r = json.dumps({'users': [dict_with_id(k, self.users_known[k]) for k in self.users_known]})
        return r

    @requiresauthentication
    def callback_user_create(self, request, context, session_id, user_id):
        body = request.json()
        assert 'username' in body
        assert 'password' in body
        if 'type' not in body:
            body['type'] = 'DEFAULT'
        guid = self.users_known.append(User(**body))

        r = json.dumps({'user': dict_with_id(guid, self.users_known[guid])})
        context.status_code = 201
        return r

    @guid
    @requiresauthentication
    def callback_user_get(self, request, context, session_id, user_id, guid):
        if guid in self.users_known:
            r = json.dumps({'user': dict_with_id(guid, self.users_known[guid])})
            return r
        context.status_code = 404
        return

    @guid
    @requiresauthentication
    def callback_user_delete(self, request, context, session_id, user_id, guid):
        try:
            del self.users_known[guid]
            mockserverlogger.info("Deleted user {0}".format(guid))
        except KeyError:
            mockserverlogger.info("Attempted to delete nonexistant user {0}".format(guid))
            context.status_code = 404
        return

    @guid
    @requiresauthentication
    def callback_user_update(self, request, context, session_id, user_id, guid):
        body = request.json()
        if 'type' not in body:
            body['type'] = 'DEFAULT'
        existing = self.users_known[guid]

        if 'id' in body:
            # Cannot re-id an object
            assert body['id'] == guid
            del body['id']

        for field in User._fields:
            if field not in body:
                body[field] = getattr(existing, field)

        self.users_known[guid] = User(**body)

        r = json.dumps({'user': dict_with_id(guid, self.users_known[guid])})
        context.status_code = 200
        return r


def dict_with_id(k, v):
    d = v._asdict()
    d['id'] = k
    return d
