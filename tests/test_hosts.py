# -*- coding: utf-8 -*-
from __future__ import print_function
from pyloginsight.models import Hosts
import logging
import random

logger = logging.getLogger(__name__)


def test_iterate_over_hosts(connection):
    hostsobject = Hosts(connection)
    counter = 0
    known_hosts = []
    for h in hostsobject:
        assert hasattr(h, "hostname")
        assert hasattr(h, "last_received")
        assert hasattr(h, "source")
        counter += 1
        assert h not in known_hosts
        known_hosts.append(h)
        print(h.last_received)

    assert counter > 0
    assert counter == len(hostsobject)


def test_reverse_hosts(connection):
    hostsobject = Hosts(connection)
    first = hostsobject[0]
    last = hostsobject[-1]
    for _ in reversed(hostsobject):
        print(_.last_received)
    assert list(reversed(hostsobject))[0] == last
    assert list(reversed(hostsobject))[-1] == first


def test_contains_hosts(connection):
    hostsobject = Hosts(connection)
    host = random.choice(hostsobject)
    assert host in hostsobject
