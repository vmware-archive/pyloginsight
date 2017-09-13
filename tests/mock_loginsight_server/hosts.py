# -*- coding: utf-8 -*-
import requests_mock
import json
import logging

from .utils import requiresauthentication

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class MockedHoststMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedHoststMixin, self).__init__(**kwargs)

        self.known_sources = [
            {'lastReceived': 1505247698798, 'sourcePath': '192.168.0.66', 'sortOrder': '0'},
        ]

        self.known_hosts = [
            {'hostname': 'host_b', 'lastReceived': 1505248138884, 'sortOrder': '0'},
            {'hostname': 'host_a', 'lastReceived': 1505248128457, 'sortOrder': '1'}
        ]

        # Collection
        self.register_uri('POST', '/api/v1/hosts', status_code=200, text=self.callback_hosts)

    @requiresauthentication
    def callback_hosts(self, request, context, **kwargs):
        body = request.json()
        assert 'loadMissingHosts' in body

        load_missing_hosts = body.get('loadMissingHosts')
        hosts_from = body.get('from', 1)
        hosts_to = body.get('to', 1)
        hosts_sort_order = body.get('sortOrder', 'desc')  # default is 'desc', but accepts 'asc'.
        hosts_sort_field = body.get('sortField', 'lastreceived')
        # ^^^ default is 'lastreceived, but accepts 'sourcepath' and 'hostname'
        # hosts_search_term = body.get('searchTerm', None)  # returns regex match of .*<value>.*

        errors = {}
        if hosts_from == 0 or hosts_to == 0:
            errors['from'] = [{'errorMessage': 'Numeric value is out of range 1 .. 1000000',
                               'errorParams': ['1', '1000000'],
                               'errorCode': 'com.vmware.loginsight.api.errors.field_value_is_out_of_range'}]
            errors['to'] = errors['from']

        if hosts_sort_order.lower() not in ['asc', 'desc']:
            errors['sortOrder'] = [{'errorMessage': 'Value should be one of (asc,desc)',
                                    'errorParams': ['asc', 'desc'],
                                    'errorCode': 'com.vmware.loginsight.api.errors.field_value_should_be_one_of'}]

        if hosts_sort_field.lower() not in ['lastreceived', 'sourcepath', 'hostname']:
            errors['sortField'] = [{'errorMessage': 'Value should be one of (hostname,sourcepath,lastreceived)',
                                    'errorParams': ['hostname', 'sourcepath', 'lastreceived'],
                                    'errorCode': 'com.vmware.loginsight.api.errors.field_value_should_be_one_of'}]

        if len(errors.keys()) > 0:
            context.status_code = 400
            return json.dumps(errors)

        context.status_code = 200
        if load_missing_hosts:
            return json.dumps({'count': len(self.known_sources), 'from': hosts_from, 'to': hosts_to,
                               'hosts': self.known_sources[hosts_from-1:hosts_to-1]}
                              )

        if not load_missing_hosts:
            return json.dumps({'count': len(self.known_hosts), 'from': hosts_from, 'to': hosts_to,
                               'hosts': self.known_hosts[hosts_from-1:hosts_to-1]}
                              )
