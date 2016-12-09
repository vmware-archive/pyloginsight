#!/usr/bin/env python

from pyloginsight.Connection import Connection, Server, Credentials
from capability import Capability
from group import Group, GroupSpec
import argparse


class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and
    datasets. """

    def add_group(self):
        """ Add a group to Log Insight. """
        raise NotImplemented



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=False, default=None)
    parser.add_argument('-p', '--password', required=False, default=None)
    parser.add_argument('-P', '--provider', required=False, default=None)
    parser.add_argument('-s', '--server', required=True)
    args = parser.parse_args()

    server = ServerPlus(args.server, verify=False)


    if not args.provider:
        # TODO: Get a list of providers for the user and display them.
        pass


    if args.username and args.password and args.provider:
        server.login(
            username=args.username,
            password=args.password,
            provider=args.provider
        )


