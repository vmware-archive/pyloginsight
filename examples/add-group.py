#!/usr/bin/env python

from pyloginsight.Connection import Server
from models import GroupSpec
import argparse
import sys


class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and datasets. """

    def add_group(self, name, capabilities, description=''):
        """ Given a Group class instance, create it on the server. """


        known_capabilities = ('ANALYTICS', 'DASHBOARDS', 'EDIT_ADMIN', 'EDIT_SHARED', 'INTERNAL', 'INVENTORY', 'STATISTICS', 'VIEW_ADMIN')
        data = GroupSpec(name=name, description=description, capabilities=capabilities).json()
        response = self._post('/groups', data=data)

        if not response.ok:
            print(response.json()['errorMessage'])
            if response.json()['errorDetails']['errorCode'] == 'com.vmware.loginsight.api.errors.rbac.wrong_capability_id_specified':
                print('The --capabilities values must be ond of {l}'.format(l=known_capabilities))
            sys.exit(1)



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

    server = ServerPlus(args.server, verify=False)
    server.login(username=args.username, password=args.password, provider=args.provider)
    server.add_group(name=args.name, description=args.description, capabilities=args.capabilities)


