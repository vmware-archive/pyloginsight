#!/usr/bin/python

import argparse
import json
import sys
from pyloginsight.models import Server, Credentials

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-t', '--tenant', required=True)
    args = parser.parse_args()

    # connect to li instance
    li = Server(
        hostname=args.server, verify=False,
        auth=Credentials(
            username=args.username,
            password=args.password,
            provider=args.provider)
    )

    # create a role
    role_data = json.dumps(
        {
            'name': 'The {} tenant role'.format(args.tenant),
            'description': 'Role for {} tenant.'.format(args.tenant),
            'capabilities': ["ANALYTICS", "VIEW_ADMIN", "INTERNAL", "EDIT_SHARED", "EDIT_ADMIN", "STATISTICS",
                             "INVENTORY", "DASHBOARD" ]
        }
    )
    role_response = li._post('/groups', data=role_data)

    if not role_response.ok:
        print('An error occurred when attempting to create "{tenant} role" on {server}.'.format(**args.__dict__))
        print('The error returned from the server is:')
        print(role_response.text)
        sys.exit(1)

    # create a dataset
    dataset_data = json.dumps(
        {
            'name':'The {} tenant dataset'.format(args.tenant),
            'description': 'Dataset for {} tenant.'.format(args.tenant),
            'constraints': [
                {
                    'name': 'tenant',
                    'operator': 'CONTAINS',
                    'value': args.tenant,
                    'fieldType': 'STRING'
                }
            ]
        }
    )
    dataset_response = li._post('/datasets', data=dataset_data)

    if not dataset_response.ok:
        print('An error occurred when attempting to create "{tenant} dataset" on {server}.'.format(**args.__dict__))
        print('You may need to delete the "{tenant} role" from {server} before running this tool again.'.format(**args.__dict__))
        print('The error returned from the server is:')
        print(dataset_response.text)
        sys.exit(1)

    # Get ID for the dataset and role to perform addition.
    role_id = role_response.json()['group']['id']
    dataset_id = dataset_response.json()['dataSet']['id']

    # add dataset to role
    dataset_to_role_data = json.dumps(
        {
            'dataSetsToAdd': [ dataset_id ],
            'dataSetsToRemove': [ ]
        }
    )
    dataset_add_response = li._post('/groups/{group_id}/datasets'.format(group_id=role_id), data=dataset_to_role_data)

    if not dataset_add_response.ok:
        print('An error occurred when attempting to add "The {tenant} tenant role" to "The {tenant} tenant dataset" on {server}.'.format(**args.__dict__))
        print('You may need to delete the "The {tenant} tenant role" and "The {tenant} tenant dataset" on {server} before running this tool again.'.format(**args.__dict__))
        print('The error returned from the server is:')
        print(dataset_response.text)
        sys.exit(1)
