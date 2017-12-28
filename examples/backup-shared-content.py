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
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=args.password, provider=args.provider)
    conn = Connection(hostname=args.hostname, auth=creds, verify=False)
    namespace = 'com.{}.{}'.format(args.hostname, datetime.now().strftime('%Y.%m.%d.%H.%M'))
    content = conn.get(url='/content/sharedcontent', params={'namespace': namespace})

    print(json.dumps(content, indent=4))
