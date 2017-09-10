import requests_mock
import json
import logging
import re
from functools import wraps
from .utils import RandomDict

mockserverlogger = logging.getLogger("LogInsightMockAdapter")

example_url_matcher = re.compile('/api/v1/example/([a-z0-9-]+)$')


def has_guid(fn):
    """Server mock; fail any request which doesn't match the example object url format"""
    @wraps(fn)
    def wrapper(self, request, context):
        try:
            guid = example_url_matcher.match(request._url_parts.path).group(1)
        except:
            context.status_code = 404
            return ""
        return fn(self, request, context, guid)
    return wrapper


class MockedExampleObjectMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedExampleObjectMixin, self).__init__(**kwargs)

        self.known_examples = RandomDict(
            {
                '12345678-90ab-cdef-1234-567890abcdef': {'attribute': 'value'},
                'uuid-of-object-with-extra-attribute': {'attribute': 'value', 'extraattribute': 'included'},
                'object-with-a-datetime': {'datetime': '2000-01-01T04:05:06Z', 'timedelta': 360000000}  # 6 minutes
            }
        )

        # Collection
        self.register_uri('GET', '/api/v1/example', status_code=200, text=self.callback_list_example)
        self.register_uri('POST', '/api/v1/example', status_code=201, text=self.callback_append_example)

        # Instances
        self.register_uri('GET', example_url_matcher, status_code=200, text=self.callback_get_example)
        self.register_uri('PUT', example_url_matcher, status_code=200, text=self.callback_set_example)
        self.register_uri('DELETE', example_url_matcher, status_code=200, text=self.callback_remove_example)

    # Collections

    def callback_list_example(self, request, context):
        return json.dumps({"summary":"Examples!", "examples": self.known_examples})

    def callback_append_example(self, request, context):
        body = request.json()
        body['id'] = self.known_examples.append(body)
        return json.dumps(body)


    # Instances
    @has_guid
    def callback_get_example(self, request, context, guid):
        try:
            return json.dumps(self.known_examples[guid])
        except KeyError:
            context.status_code = 404
            return ""

    @has_guid
    def callback_set_example(self, request, context, guid):
        body = request.json()
        body['id'] = guid
        self.known_examples[guid] = body
        return json.dumps(body)

    @has_guid
    def callback_remove_example(self, request, context, guid):
        try:
            del self.known_examples[guid]
            mockserverlogger.info("Deleted example {0}".format(guid))
        except KeyError:
            mockserverlogger.info("Attempted to delete nonexistant example {0}".format(guid))
            context.status_code = 404
        return

    def prep(self):
        pass
