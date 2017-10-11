#!/usr/bin/env python

from pyloginsight.connection import Connection, Credentials
from datetime import datetime
import argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Gets the shared content from a server.')
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--provider', default='Local')
    parser.add_argument('--hostname', required=True)
    parser.add_argument('--uuid', required=True)
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=args.password, provider=args.provider)
    conn = Connection(hostname=args.hostname, auth=creds, verify=False)

    user = conn.get(url='/users/{}'.format(args.uuid))
    username = user.get('user', {}).get('username', 'unknown')
    namespace = 'com.{}.{}.{}.{}'.format(args.hostname, args.uuid, username, datetime.now().strftime('%Y.%m.%d.%H.%M'))
    content = conn.get(url='/content/usercontent/{}'.format(args.uuid), params={'namespace': namespace})

    print(json.dumps(content, indent=4))
