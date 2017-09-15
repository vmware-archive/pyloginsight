# -*- coding: utf-8 -*-
from __future__ import print_function

import requests_mock
import json
import logging
from .utils import RandomDict, requiresauthentication, trailing_guid_pattern, uuid_url_matcher, guid

logger = logging.getLogger("LogInsightMockAdapter").getChild(__name__)


class MockedDatasetsMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedDatasetsMixin, self).__init__(**kwargs)

        # Two datasets
        self.__known = RandomDict(
            {
                '12345678-90ab-cdef-1234-567890abcdef': {
                    'id': '12345678-90ab-cdef-1234-567890abcdef',
                    'constraints': [
                      {'value': 'vobd', 'hidden': False, 'name': 'appname', 'fieldType': 'STRING', 'operator': 'CONTAINS'}
                    ],
                    'type': 'OR',
                    'name': 'permissive dataset',
                    'description': 'Dataset which adds to other datasets using type=OR'
                },
                '12345678-aaaa-cdef-1234-567890abcdef': {
                    'id': '12345678-aaaa-cdef-1234-567890abcdef',
                    'name': 'restrictive dataset',
                    'type': 'AND',
                    'constraints': [
                      {'name': 'hostname', 'operator': 'CONTAINS', 'fieldType': 'STRING', 'hidden': False, 'value': 'test-hostname'},
                      {'name': 'lineno', 'operator': 'EQUAL', 'fieldType': 'NUMBER', 'hidden': False, 'value': '4'},
                      {'name': 'hostname', 'operator': 'MATCH', 'fieldType': 'STRING', 'hidden': False, 'value': 'regexpattern'}
                    ],
                    'description': 'Dataset which restricts other datasets using type=AND'
                }
            }
        )

        # Plural
        self.register_uri('GET', '/api/v1/datasets', status_code=200, text=self.__list)
        self.register_uri('POST', '/api/v1/datasets', status_code=201, text=self.__add)

        # Singular
        self.register_uri('DELETE', uuid_url_matcher('datasets'), status_code=200, text=self.__remove)
        self.register_uri('GET', uuid_url_matcher('datasets'), status_code=200, text=self.Raise418)
        self.register_uri('POST', uuid_url_matcher('datasets'), status_code=201, text=self.Raise418)
        self.register_uri('PATCH', uuid_url_matcher('datasets'), status_code=201, text=self.Raise418)

    @requiresauthentication
    def __list(self, request, context, session_id, user_id):
        return json.dumps({'dataSets': list(self.__known.values())})

    @requiresauthentication
    def __add(self, request, context, session_id, user_id):
        body = request.json()
        print("Got blob from client", body)
        assert 'dataSet' in body
        newitem = body['dataSet']
        assert 'name' in newitem
        assert 'id' not in newitem

        newitem['id'] = self.__known.append(newitem)

        context.status_code = 201

        return json.dumps(newitem)

    @guid
    @requiresauthentication
    def __remove(self, request, context, session_id, user_id, guid):
        try:
            del self.__known[guid]
            logger.info("Deleted {0}".format(guid))
        except KeyError:
            logger.info("Attempted to delete nonexistant {0}".format(guid))
            context.status_code = 404
        return

    def prep(self):
        pass
