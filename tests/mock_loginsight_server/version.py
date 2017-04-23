import requests_mock
from collections import Counter
import json
import logging
from .utils import RandomDict, requiresauthentication, trailing_guid_pattern, license_url_matcher

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class MockedVersionMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedVersionMixin, self).__init__(**kwargs)

        self.version = {"releaseName": "GA","version": "1.2.3-4567890"}
        self.register_uri('GET', '/api/v1/version', text=self.callback_get_version, status_code=200)

    @requiresauthentication
    def callback_get_version(self, request, context, session_id, user_id):
        return json.dumps(self.version)

    def prep(self):
        pass
