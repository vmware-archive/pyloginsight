# -*- coding: utf-8 -*-
import requests_mock
import json
import logging
import uuid
import random

from .utils import requiresauthentication

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


def generate_hosts(quantity, host_type):
    """ Given a quantity an a type, generate fake hosts values without a sortOrder. The sortOrder is added by the
    sort_hosts function. """
    assert type(quantity) == int
    assert host_type in ['source', 'host']
    for n in range(0, quantity, 1):
        if host_type == 'host':
            yield {'hostname': 'host-{}'.format(uuid.uuid4()),
                   'lastReceived': random.randint(1154394061 * 1000, 1505330380 * 1000)}
        elif host_type == 'source':
            yield {'sourcePath': ".".join(map(str, (random.randint(0, 254) for _ in range(4)))),
                   'lastReceived': random.randint(1154394061 * 1000, 1505330380 * 1000)}


def sort_hosts(hosts, order):
    """ Given a list of hosts, sort the list and add a sortOrder value. """
    reverse = True if order == 'desc' else False
    counter = 0
    for host in sorted(hosts, key=lambda k: k['lastReceived'], reverse=reverse):
        host['sortOrder'] = counter
        counter += 1
        yield host


class MockedHoststMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedHoststMixin, self).__init__(**kwargs)
        self.known_sources = [_ for _ in generate_hosts(300, 'source')]
        self.known_hosts = [_ for _ in generate_hosts(300, 'host')]
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
            payload = [_ for _ in sort_hosts(self.known_sources, order=hosts_sort_order)]
            return json.dumps({'count': len(payload), 'from': hosts_from, 'to': hosts_to,
                               'hosts': payload[hosts_from - 1:hosts_to]}
                              )

        if not load_missing_hosts:
            payload = [_ for _ in sort_hosts(self.known_hosts, order=hosts_sort_order)]
            return json.dumps({'count': len(payload), 'from': hosts_from, 'to': hosts_to,
                               'hosts': payload[hosts_from - 1:hosts_to]}
                              )
