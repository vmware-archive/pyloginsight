#!/usr/bin/env python

from models import PostGroupIdDatasetSpec
import argparse

from pyloginsight.connection import Connection, Credentials


class ServerPlus(Connection):

    def add_dataset_to_group(self, dataset_id, group_id):
        """ Add a dataset to a group. DISCLAIMER: At the time of writing this API was a technical preview. """

        data = PostGroupIdDatasetSpec(
            group_id=group_id,
            dataset_add_list=[dataset_id],
            dataset_remove_list=[]
        ).json()

        response = self.post('/groups/{group_id}/datasets'.format(group_id=group_id), data=data)

        if not response.ok:
            print(response.json())


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-g', '--group-id', required=True)
    parser.add_argument('-d', '--dataset-id', required=True)
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=args.password, provider=args.provider)
    conn = ServerPlus(args.server, verify=False, auth=creds)
    conn.add_dataset_to_group(group_id=args.group_id, dataset_id=args.dataset_id)
