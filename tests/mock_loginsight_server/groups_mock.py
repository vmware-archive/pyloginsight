# -*- coding: utf-8 -*-
from __future__ import print_function

import requests_mock
import logging
from .utils import RandomDict, uuid_url_matcher

logger = logging.getLogger("LogInsightMockAdapter").getChild(__name__)


class MockedGroupsMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedGroupsMixin, self).__init__(**kwargs)

        self.__known = RandomDict()

        # Plural
        self.register_uri('GET', '/api/v1/groups', status_code=200, text=self.Raise418)
        self.register_uri('POST', '/api/v1/groups', status_code=201, text=self.Raise418)

        # Singular
        self.register_uri('DELETE', uuid_url_matcher('groups'), status_code=200, text=self.Raise418)
        self.register_uri('GET', uuid_url_matcher('groups'), status_code=200, text=self.Raise418)
        self.register_uri('POST', uuid_url_matcher('groups'), status_code=201, text=self.Raise418)
        self.register_uri('PATCH', uuid_url_matcher('groups'), status_code=201, text=self.Raise418)

    def prep(self):
        pass
