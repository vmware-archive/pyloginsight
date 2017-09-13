# -*- coding: utf-8 -*-
from __future__ import print_function
from pyloginsight.models import Hosts
import logging
import random


logger = logging.getLogger(__name__)


def test_iterate_over_hosts(connection):
    hostsobject = Hosts(connection)
    counter = 0
    for h in hostsobject:
        assert hasattr(h, "hostname")
        assert hasattr(h, "last_received")
        assert hasattr(h, "source")
        counter += 1
    assert counter > 0
    assert counter == len(hostsobject)


def test_reverse_hosts(connection):
    hostsobject = Hosts(connection)
    first = hostsobject[0]
    last = hostsobject[-1:][0]
    assert list(reversed(hostsobject))[0] == last
    assert list(reversed(hostsobject))[-1:][0] == first


def test_contains_hosts(connection):
    hostsobject = Hosts(connection)
    host = random.choice(hostsobject)
    assert host in hostsobject


