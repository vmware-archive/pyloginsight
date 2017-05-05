#!/usr/bin/env python


from pyloginsight.connection import Connection, Credentials

import argparse
import pprint


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=args.password, provider=args.provider)
    conn = Connection(hostname=args.server, verify=False, auth=creds)

    pprint.pprint({k: v for (k, v) in conn.server.roles.items()})
