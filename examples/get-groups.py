#!/usr/bin/env python

from pyloginsight.models import Server
from models import Group, Capability
import argparse


class ServerPlus(Server):

    @property
    def groups(self):
        """ Get groups. DISCLAIMER: At the time of writing this API was a technical preview. """

        groups = []
        for group in self._get('/groups').json()['groups']:
            capabilities = []

            for capability in group['capabilities']:
                capabilities.append(Capability(id=capability['id']))

            groups.append(
                Group(
                    id=group['id'],
                    name=group['name'],
                    description=group['description'],
                    required=bool(group['required']),
                    editable=bool(group['editable']),
                    capabilities=capabilities
                ))

        return groups


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    args = parser.parse_args()

    server = ServerPlus(args.server, verify=False)
    server.login(username=args.username, password=args.password, provider=args.provider)

    print('\n'.join([str(group) for group in server.groups]))

