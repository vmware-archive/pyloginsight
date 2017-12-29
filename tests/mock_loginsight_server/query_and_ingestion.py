# -*- coding: utf-8 -*-
from __future__ import print_function

import requests_mock
import json
import logging
import re
from functools import wraps
import time
from six.moves import urllib
from pyloginsight import operator

from .utils import RandomDict, requiresauthentication, uuid_url_matcher, guid

logger = logging.getLogger("LogInsightMockAdapter").getChild(__name__)

"""
Minimal mock of a Log Insight events ingestion and query system.
Leaves out many edge-cases.
No support for regex matching or globs or tokenization.
No support for OR'd constraints, so `/appname/contains vpxa/appname/contains vpxd` will never match.
"""


def query_path_url_matcher(base):
    return re.compile('/api/v1/' + base + '(/.*)$')


def url_to_constraints(path):
    url_query_chunk = query_path_url_matcher('[^/]+').match(path).group(1)
    print("url_query_chunk", url_query_chunk)

    path_split = url_query_chunk.split("/")
    print("path_split", path_split)

    a = iter(path_split)
    next(a)  # leading slash

    def mutate(iterable):
        for fieldname, encoded_argument in iterable:
            argument = urllib.parse.unquote_plus(encoded_argument)
            if argument.upper() in operator._BOOLEAN:
                yield (fieldname, argument.upper(), None)
                continue

            for potential_operator in operator._NUMERIC + operator._STRING + operator._TIME:
                if argument.upper().startswith(potential_operator):
                    value = argument[len(potential_operator):]
                    yield (fieldname, potential_operator, value)
                    break
            else:
                raise ValueError("Mock cannot parse field/operator+value: %s/%s" % (fieldname, argument))

    return mutate(zip(a, a))


def query_components(fn):
    """Server mock; grab the object guid from the url"""
    @wraps(fn)
    def wrapper(self, request, context, *args, **kwargs):
        constraints = list(url_to_constraints(request.path))
        return fn(self, request=request, context=context, constraints=constraints, params={}, *args, **kwargs)

    return wrapper


class MockedEventDataMixin(requests_mock.Adapter):
    def __init__(self, **kwargs):
        super(MockedEventDataMixin, self).__init__(**kwargs)

        self.__known = RandomDict()

        # Query
        self.register_uri('GET', query_path_url_matcher('events'), status_code=200, text=self.__events)
        self.register_uri('GET', query_path_url_matcher('aggregated-events'), status_code=200, text=self.Raise418)

        self.register_uri('POST', uuid_url_matcher('events/ingest'), status_code=200, text=self.__ingest)

        # Two datasets
        self.__known = [
            {"timestamp": 0, "text": "beginning of time", "fields": [{"name": "appname", "content": "pyloginsight test"}]},
            {"timestamp": 12345678900, "text": "sequence epoch", "fields": [{"name": "appname", "content": "pyloginsight test"}]},
        ]

    @guid
    def __ingest(self, request, context, guid):
        body = request.json()
        print("Got blob from client", body)

        try:
            events = body['events']
        except KeyError:
            context.status_code = 400
            return "{'errorMessage': 'Missing events'}"

        for e in events:
            # add default values to event
            if 'timestamp' not in e:
                e['timestamp'] = int(time.time() * 1000.0)  # Now
            if 'text' not in e:
                e['text'] = ""
            if 'fields' not in e:
                e['fields'] = []
            print("e", e)

            self.__known.append(e)

        return json.dumps({'ingested': len(events), 'status': 'ok', 'message': 'events ingested'})

    def prep(self):
        pass

    @requiresauthentication
    @query_components
    def __events(self, request, context, constraints, params, session_id, user_id):
        # (?P<field>[0-9a-z_]+)/(?P<operator>[<>=] (?P)
        return json.dumps({'events': list(self.__query_filter(constraints))})

    @requiresauthentication
    def __aggregate(self, request, context, session_id, user_id):
        pass

    def __query_filter(self, constraints):
        for event in self.__known:
            if all([evaluate_constraint(event, c) for c in constraints]):
                print("Emitting event", event)
                yield event
            else:
                print("NOT emitting event", event)


def all_fields_as_dict(event):
    return dict((f['name'], f['content']) for f in event['fields'])


def evaluate_constraint(event, constraint):
    """Rudimentary query execution. Returns True if the event is permitted by this constraint, False otherwise."""
    (fieldname, op, value) = constraint
    print("Evaluating event", event, "against constraint", constraint)

    event_fields = all_fields_as_dict(event)

    # Existence operators
    if op == operator.EXISTS:
        return fieldname in ('text', 'timestamp') + tuple(event_fields.keys())

    if fieldname == "text":
        subject = event['text']
    elif fieldname == "timestamp":
        subject = event['timestamp']
    else:
        subject = event.get(fieldname, None)

    # String operators
    if op in (operator.CONTAINS, operator.HAS):
        return value in subject
    if op in (operator.NOT_CONTAINS, operator.NOT_HAS):
        return value not in subject

    # TODO: Regex operators

    # Numeric operators
    try:
        value = int(value)
    except ValueError:
        value = None

    if op == operator.EQUAL:
        return subject == value
    if op == operator.NOTEQUAL:
        return subject != value
    if op == operator.GT:
        return subject > value
    if op == operator.LT:
        return subject < value
    if op == operator.GE:
        return subject >= value
    if op == operator.LE:
        return subject <= value

    raise NotImplementedError("Support for operator '%s' not implemented by mock" % op)
