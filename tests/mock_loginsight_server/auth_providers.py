# -*- coding: utf-8 -*-

import requests_mock
import json
import logging

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class MockedAuthProvidersMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedAuthProvidersMixin, self).__init__(**kwargs)

        self.auth_providers = {"providers": ["Local", "ActiveDirectory"]}
        self.register_uri(
            method='GET',
            url='/api/v1/auth-providers',
            status_code=200,
            text=self.callback_get_auth_providers
        )

    def callback_get_auth_providers(self, request, context):
        return json.dumps(self.auth_providers)

    def prep(self):
        pass
