#!/usr/bin/env python

from pyloginsight.Connection import Server
from pyloginsight.query import Constraint
from models import PostGroupIdDatasetSpec
import argparse


class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and datasets. """

    def add_dataset_to_group(self, dataset_id, group_id):
        
        data = PostGroupIdDatasetSpec(
            group_id = group_id,
            dataset_add_list = [dataset_id],
            dataset_remove_list = []
        ).json()

        response = self._patch('/groups/{group_id}/datasets'.format(group_id=group_id, data=data))

        if not response.ok:
            print(response.json())


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-g', '--group_id', required=True)
    parser.add_argument('-d', '--dataset_id', required=True)
    args = parser.parse_args()

    server = ServerPlus(args.server, verify=False)
    server.login( username=args.username, password=args.password, provider=args.provider)
    server.add_dataset_to_group(group_id=args.group_id, dataset_id=args.dataset_id)


