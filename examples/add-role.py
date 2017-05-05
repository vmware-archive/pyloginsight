#!/usr/bin/env python


from pyloginsight.connection import Connection, Credentials

import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-n', '--name', required=True)
    parser.add_argument('-d', '--description', default='')
    parser.add_argument('-c', '--capabilities', required=True, nargs='+')
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=args.password, provider=args.provider)
    conn = Connection(hostname=args.server, verify=False, auth=creds)

    conn.server.roles.append(name=args.name, description=args.description, capabilities=args.capabilities)
