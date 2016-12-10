#!/usr/bin/env python

from pyloginsight.Connection import Server
from pyloginsight.query import Constraint
import argparse


class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and
    datasets. """

    def add_dataset_to_group(self, dataset, group):
        pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-g', '--group', required=True)
    parser.add_argument('-d', '--dataset', required=True)
    args = parser.parse_args()

    server = ServerPlus(args.server, verify=False)
    server.login( username=args.username, password=args.password, provider=args.provider)
    server.add_dataset_to_group(group=args.group, dataset=args.dataset)


