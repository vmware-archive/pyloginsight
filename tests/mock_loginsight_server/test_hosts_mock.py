# -*- coding: utf-8 -*-
from __future__ import print_function
from .hosts import generate_hosts, sort_hosts
import random


def test_generate_hosts():
    hosts = [_ for _ in generate_hosts(300, host_type='host')]
    sources = [_ for _ in generate_hosts(300, host_type='source')]

    assert 'lastReceived' in random.choice(hosts).keys()
    assert 'lastReceived' in random.choice(sources).keys()
    assert 'hostname' in random.choice(hosts).keys()
    assert 'sourcePath' in random.choice(sources).keys()
    assert 'sortOrder' not in random.choice(sources).keys()
    assert 'sortOrder' not in random.choice(hosts).keys()


def test_sort_hosts():

    for host_type in ['host', 'source']:
        hosts = [_ for _ in generate_hosts(300, host_type=host_type)]
        asc_hosts = [_ for _ in sort_hosts(hosts, order='asc')]
        desc_hosts = [_ for _ in sort_hosts(hosts, order='desc')]

        assert 'sortOrder' in random.choice(hosts).keys()
        assert asc_hosts[0]['lastReceived'] == desc_hosts[-1]['lastReceived']
        assert asc_hosts[-1]['lastReceived'] == desc_hosts[0]['lastReceived']
        assert asc_hosts[0]['lastReceived'] < desc_hosts[0]['lastReceived']
        assert desc_hosts[-1]['lastReceived'] < asc_hosts[-1]['lastReceived']

        asc_host_chunk = [asc_hosts[0:99],
                          asc_hosts[100:199]]

        desc_host_chunk = [desc_hosts[0:99],
                           desc_hosts[100:199]]

        assert asc_host_chunk[0][0]['lastReceived'] < asc_host_chunk[1][0]['lastReceived']
        assert desc_host_chunk[0][0]['lastReceived'] > desc_host_chunk[1][0]['lastReceived']

