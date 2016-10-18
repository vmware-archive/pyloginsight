#!/usr/bin/env python

import argparse
import datetime
import logging
import requests
import json
import warnings


class Host(object):
    hostname = None
    lastReceived = None
    sortOrder = None
    serverTime = 0

    def __init__(self, hoststruct):
        self.hostname = hoststruct.get("hostname", None)
        self.lastReceived = datetime.datetime.fromtimestamp(hoststruct.get("lastReceived", 0)/1000)

    def __repr__(self):
        return '<Host {0} @ {1}>'.format(self.hostname, self.lastReceived)


def login(args):
    """Login and get a session token"""
    r = requests.post(
            args.apiroot+'/sessions',
            verify=False,
            data=json.dumps({'username': args.username, 'password': args.password, 'provider': 'Local'})
        )
    try:
        args.sessionID = r.json()['sessionId']
    except:
        raise RuntimeError("Authentication failure: " + str(r.text))


def hosts(args):
    lms = 'false' if not args.loadMissingHosts else 'true'
    request_length = args.batch
    hosts_from = 1
    while hosts_from >= 0:
        r = requests.post(
            args.apiroot+'/hosts',
            verify=False,
            data=json.dumps({'loadMissingHosts': lms, 'from': hosts_from, 'to': hosts_from + request_length - 1}),
            headers={'Authorization': 'Bearer '+args.sessionID}
        )
        if 'Warning' in r.headers:
            warnings.warn(r.headers.get('Warning'))
        try:
            p = r.json()
        except:
            print r.text
            raise
        for hoststruct in p.get('hosts', []):
            yield Host(hoststruct)
        hosts_from = p.get('to', -2)+1
        if p.get('to', 0) >= p.get('count', 0):
            hosts_from = -1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump full source host list from Log Insight')
    parser.add_argument('--hostname', type=str, help="Log Insight server hostname or IP")
    parser.add_argument('--port', type=int, default=9543, metavar=9543, help="SSL api port")
    parser.add_argument('--username', type=str, required=True, metavar='admin', help='Local user account with at least readonly admin permissions')
    parser.add_argument('--password', type=str, help='Insecurely specify password on command line. Will prompt if not provided.', default=None)
    parser.add_argument('--batch', type=int, default=200, metavar=200, help="Number of hosts to request at once.")
    parser.add_argument('--loadMissingHosts', action='store_true', default=False)
    parser.add_argument('--quiet', action='store_true', default=False)
    args = parser.parse_args()

    if args.quiet:
        warnings.simplefilter('ignore')
    else:
        # HTTPS Certificate and Preview API warnings dumped to stderr once each
        warnings.simplefilter("once")

    if args.password is None:
        from getpass import getpass
        args.password = getpass()

    args.apiroot = 'https://{server}:{port}/api/v1'.format(server=args.hostname, port=args.port)
    login(args)
    for h in hosts(args):
        print "{h.hostname}, {h.lastReceived}".format(h=h)
