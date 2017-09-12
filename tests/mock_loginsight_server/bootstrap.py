# -*- coding: utf-8 -*-
import logging

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class MockedBootstrapMixin(object):
    def __init__(self, **kwargs):
        super(MockedBootstrapMixin, self).__init__(**kwargs)

        self.register_uri('POST', '/api/v1/deployment/new', text=self.deployment_new, status_code=200)
        self.register_uri('POST', '/api/v1/deployment/waitUntilStarted', text="{}", status_code=200)

    def deployment_new(self, request, context):
        body = request.json()

        assert 'user' in body
        assert 'userName' in body['user']
        return "{}"
