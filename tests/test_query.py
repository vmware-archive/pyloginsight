# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest
import warnings
import collections
import uuid

from pyloginsight.exceptions import TransportError
from pyloginsight.query import Constraint, Parameter
from pyloginsight import operator
from pyloginsight.models import Event
from pyloginsight.ingestion import serialize_event_object, crush_invalid_field_name
from datetime import datetime
import pytz
import time
import json

"""Examples from "Specifying constraints" section of https://vmw-loginsight.github.io/#Querying-data"""


def test_constraint_example1_text_contains():
    assert "/text/CONTAINS%20ERROR" == str(Constraint(field="text", operator=operator.CONTAINS, value="ERROR"))


def test_constraint_example2_timestamp_greaterthan():
    assert "/timestamp/%3E1451606400000" == str(Constraint(field="timestamp", operator=operator.GT, value="1451606400000"))


def test_constraint_example3_compound():
    assert "/timestamp/%3E0/text/CONTAINS%20ERROR" == ''.join([
        str(Constraint(field="timestamp", operator=operator.GT, value="0")),
        str(Constraint(field="text", operator=operator.CONTAINS, value="ERROR"))
    ])


def test_constraint_LAST_with_timestamp():
    # Constraints LAST must be used with a number, and cannot be used with non-timestamp
    assert "/timestamp/LAST60000" == str(Constraint(field="timestamp", operator=operator.LAST, value=60000))
    assert "/timestamp/LAST60000" == str(Constraint(field="timestamp", operator=operator.LAST, value="60000"))
    with pytest.raises(ValueError):
        assert str(Constraint(field="not-timestamp-field", operator=operator.LAST, value=60000))


def test_constraint_numeric_operators_reject_strings():
    with pytest.raises(ValueError):
        assert str(Constraint(field="x", operator=operator.GT, value="string"))
    with pytest.raises(ValueError):
        assert str(Constraint(field="timestamp", operator=operator.LAST, value="string"))


def test_constraint_pathalogical_encoding():
    pathalogic = '''field @#$%^&/;\,.<a>'"value'''
    encoded = '''field%20%40%23%24%25%5E%26%2F%3B%5C%2C.%3Ca%3E%27%22value'''
    assert "/" + encoded + "/HAS%20" + encoded == str(Constraint(field=pathalogic, operator=operator.HAS, value=pathalogic))


def test_constraint_exists():
    # Exists; cannot pass a non-empty value
    with warnings.catch_warnings(record=True) as w:
        assert "/x/EXISTS" == str(Constraint(field="x", operator=operator.EXISTS, value="something"))
        assert len(w) == 1
    with warnings.catch_warnings(record=True) as w:
        assert "/x/EXISTS" == str(Constraint(field="x", operator=operator.EXISTS))
        assert len(w) == 0


def test_parameters():
    _ = Parameter(order="ASC", limit=4, timeout=20, contentpackfields="x,y,z", super="abc")


def test_query_conditions(connection):
    """
    Run a live query against a remote server.
    """

    # All time, default limit of 100 events
    conditions = [Constraint("source", operator.EXISTS), Constraint("timestamp", ">=", 0)]
    events = connection.server.events(conditions)

    assert isinstance(events, collections.Sized)


def test_ping_pong_message(connection):
    """Ingest a message and then query it back."""

    events = None
    e = Event(text=str(uuid.uuid4()), fields={'appname': 'pyloginsight test'}, timestamp=datetime.now(pytz.utc).replace(microsecond=0))

    connection.server.log(e)

    conditions = [Constraint("text", operator.CONTAINS, e['text']), Constraint("timestamp", "=", e['timestamp'])]

    # The event will traverse the ingestion pipeline asynchronously.
    # Poll the server 100 times with a 0.05 second delay in 5 seconds, plus request overhead
    attempt = 0
    for attempt in range(100):
        events = connection.server.events(conditions)
        assert isinstance(events, collections.Sequence)
        if len(events) > 0:
            break
        time.sleep(0.05)
    else:
        pytest.fail("Timeout waiting for event to appear in query results")

    assert len(events) > 0
    assert isinstance(events[0], Event)
    assert isinstance(events[0].fields, collections.Mapping)
    assert isinstance(events[0].timestamp, datetime)

    # Other than server-added fields...
    for f in ('event_type', 'source', 'hostname'):
        try:
            del events[0]['fields'][f]
        except KeyError:
            pass

    # The originally-send and query-result events are equal
    assert events[0] == e

    print("Completed in %d attempts" % attempt)


def test_ingest_single_message(connection):
    """
    Create and ingest a new log message with text=uuid and the current datetime.
    If the server rejects the event or cannot parse it, this raises an exception.
    """
    e = Event(
        text=str(uuid.uuid4()),
        fields={'appname': 'pyloginsight test'},
        timestamp=datetime.now(pytz.utc)
    )

    connection.server.log(e)


def test_ingest_single_empty_message(connection):
    """It is possible to ingest a completely empty Event. It serializes to {}"""
    e = Event()
    connection.server.log(e)


def test_ingest_pathalogical_field_name(connection):
    pathalogic = '''field @#$%^&/;\,.<a>'"value'''
    e = Event(
        text=str(uuid.uuid4()),
        fields={'appname': 'pyloginsight test', pathalogic: 'pyloginsight test'},
        timestamp=datetime.now(pytz.utc)
    )
    assert 'field_a_value' == crush_invalid_field_name(pathalogic)
    assert 'field_a_value' in json.dumps(serialize_event_object(e))
    connection.server.log(e)


def test_ingest_pathalogical_field_value(connection):
    pathalogic = '''field @#$%^&/;\,.<a>'"value'''
    e = Event(
        text=str(uuid.uuid4()),
        fields={'appname': 'pyloginsight test', 'pyloginsight test': pathalogic},
        timestamp=datetime.now(pytz.utc)
    )
    connection.server.log(e)


def test_event_repr():
    e = Event(
        text=str(uuid.uuid4()),
        fields={'appname': 'pyloginsight test'},
        timestamp=datetime.now(pytz.utc)
    )
    assert 'datetime' in repr(e)
    assert 'appname' in repr(e)
    assert 'text=' in repr(e)
    print(e)


def test_ingest_without_any_events_fails(connection):
    """Transmit a single garbage object to a remote Log Insight server."""
    with pytest.raises(TransportError):
        r = connection.post("/events/ingest/0", json={"foo": "bar"}, sendauthorization=False)


def test_ingest_extra_fields_succeeds(connection):
    """Transmit an empty list of events, along with extra data which should be ignored."""
    r = connection.post("/events/ingest/0", json={"events": [], "foo": "bar"}, sendauthorization=False)
