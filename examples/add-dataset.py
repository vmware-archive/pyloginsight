#!/usr/bin/env python

import argparse
import pyloginsight.models as pyli
       

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-n', '--name', required=True)
    parser.add_argument('-d', '--description', required=False, default="")
    parser.add_argument('-f', '--field', required=True)
    parser.add_argument('-v', '--value', required=True)

    args = parser.parse_args()

    creds = pyli.Credentials(username=args.username, password=args.password, provider=args.provider)
    server = pyli.Server(hostname=args.server, verify=False, auth=creds)

    server.datasets.append(name=args.name, description=args.description, field=args.field, value=args.value)
