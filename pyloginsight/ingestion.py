#!/usr/bin/env python
# -*- coding: utf-8 -*-

# VMware vRealize Log Insight SDK
# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re
from datetime import datetime

import pytz

from .exceptions import ServerError

logger = logging.getLogger(__name__)

MAXIMUM_BYTES_TEXT_FIELD = 1024 * 16  # 16 KB (text field)


def datetime_in_milliseconds(dt):
    """
    :param dt: Instance of datetime.datetime
    :return: Unix timestamp in milliseconds since epoch
    """
    try:
        return int(dt.timestamp() * 1000)
    except AttributeError:
        _EPOCH = datetime(1970, 1, 1, tzinfo=pytz.utc)
        return int((dt - _EPOCH).total_seconds() * 1000)


def crush_invalid_field_name(name):
    """
    Log Insight field names must start with an underscore or an alpha character.
    :param name: A proposed field name
    :return: Field name with invalid characters replaced by underscores (_), and runs of underscores
    """
    if name[0].isdigit():
        name = "_%s" % name
    name = re.sub(r'[^a-z0-9_]', "_", name.lower())
    return re.sub(r'__*', "_", name, flags=re.I)


def serialize_cfapi_event(message, timestamp_milliseconds, fields):
    """

    :param message: A str to use as the message body
    :param timestamp_milliseconds: An integer
    :param fields: A dict of fields.
    :return:
    """
    o = {}
    if message:
        o['text'] = message[:MAXIMUM_BYTES_TEXT_FIELD]
    if timestamp_milliseconds:
        o['timestamp'] = timestamp_milliseconds
    if fields:
        pass
        o['fields'] = [{'name': crush_invalid_field_name(str(k)), 'content': str(v)} for k, v in fields.items()]
    return o


def serialize_event_object(event_object):
    try:
        ms = datetime_in_milliseconds(event_object.timestamp)
    except AttributeError:
        ms = None

    return serialize_cfapi_event(event_object.get('text', None), ms, event_object.get('fields', None))


def transmit(connection, event_objects, agent_id="1", trusted=False):
    """Transmit a single Event object to a remote Log Insight server."""
    evts = list()
    for event_object in event_objects:
        evts.append(serialize_event_object(event_object))

    r = connection.post("/events/ingest/" + agent_id, json={"events": evts}, sendauthorization=trusted)

    if r.get("status", None) == 'ok':
        return r.get("ingested", 0)

    raise ServerError(r)
