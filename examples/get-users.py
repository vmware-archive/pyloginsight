#!/usr/bin/env python

from pyloginsight.connection import Connection, Credentials
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Gets the shared content from a server.')
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--provider', default='Local')
    parser.add_argument('--hostname', required=True)
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=args.password, provider=args.provider)
    conn = Connection(hostname=args.hostname, auth=creds, verify=False)

    response = conn.get(url='/users')
    for user in response['users']:
        print('{} {}'.format(user.get('id', 'unknown'), user.get('username', 'unknown')))
