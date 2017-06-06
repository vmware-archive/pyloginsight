#!/usr/bin/env python

import argparse
import logging
import requests
import getpass
import warnings
import time

from pyloginsight.internal import config, users, groups, datasets, content

from pyloginsight.connection import Connection, Credentials
from requests.packages.urllib3.exceptions import InsecureRequestWarning


# Configuring logging date/time format.
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

logging.info("Suppressing SSL warnings.")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.info('Suppressing API warnings.')
warnings.simplefilter('ignore')

parser = argparse.ArgumentParser()
parser.add_argument('--source-username', required=True)
parser.add_argument('--source-provider', default='Local', help='(Default = "Local")')
parser.add_argument('--source-server', required=True)
parser.add_argument('--destination-username', required=True)
parser.add_argument('--destination-provider', default='Local', help='(Default = "Local")')
parser.add_argument('--destination-server', required=True)

args = parser.parse_args()

logging.info('Creating session for source.')
src_creds = Credentials(
    username=args.source_username,
    password=getpass.getpass('Source({server}) password:'.format(server=args.source_server)),
    provider=args.source_provider,
)
src_conn = Connection(hostname=args.source_server, verify=False, auth=src_creds)

logging.info('Creating session for destination.')
dst_creds = Credentials(
    username=args.destination_username,
    password=getpass.getpass('Destination({server}) password:'.format(server=args.destination_server)),
    provider=args.destination_provider,
)
dst_conn = Connection(hostname=args.destination_server, verify=False, auth=dst_creds)

logging.info('Confirming that source and destination are the same version.')
assert dst_conn.server.version == src_conn.server.version

logging.info('Exporting source cluster configuration.')
src_config = config.download(src_conn)

logging.info('Exporting source groups (roles).')
src_groups = [groups.get(src_conn, group_id) for group_id in groups.list(src_conn)[:5]]

logging.info('Exporting source datasets.')
src_datasets = [datasets.get(src_conn, dataset_id) for dataset_id in datasets.list(src_conn)[:5]]

logging.info('Exporting source users.')
src_users = [users.get(src_conn, user_id) for user_id in users.list(src_conn)[:5]]

logging.info('Exporting source content.')
src_content = [content.get(src_conn, content_id) for content_id in content.list(src_conn)[:5]]

logging.info('Importing source cluster configuration to destination.')
config.upload(dst_conn, src_config)

logging.info('Importing source cluster content to destination.')
dst_content = [(pack, content.create(dst_conn, pack)) for pack in src_content]

logging.info('Skipped: Creating groups on destination.')
"""
src_to_dst_group_mapping = {}
for group in src_groups:
    try:
        logging.info('Creating "{name}" group.'.format(name=group['summary']['group']['name']))
        results = groups.create(
            conn=dst_conn,
            name=group['summary']['group']['name'],
            capabilities=group['capabilities']
        )
        src_to_dst_group_mapping[group['summary']['group']['id']] = results['group']['id']

    except ValueError:
        logging.info('Error creating "{name}" group.'.format(name=group['summary']['group']['name']))
"""

logging.info('Skipped: Creating datasets on destination.')
"""
src_to_dst_dataset_mapping = {}
for dataset in src_datasets:
    try:
        new_constraints = []
        for constraint in dataset['dataSet']['constraints']:
            new_constraints.append(
                {
                    'name': constraint['name'],
                    'operator': constraint['operator'],
                    'value': constraint['value'],
                    'fieldType': constraint['fieldType']
                }
            )

        logging.info('Creating "{name}" dataset.'.format(name=dataset['dataSet']['name']))
        results = datasets.create(
            conn=dst_conn,
            name=dataset['dataSet']['name'],
            description=dataset['dataSet']['description'],
            constraints=new_constraints
        )
        src_to_dst_dataset_mapping[dataset['dataSet']['id']] = results['dataSet']['id']

    except ValueError:
        logging.info('Error creating "{name}" dataset.'.format(name=dataset['dataSet']['name']))

"""

logging.info('Skipped: Creating users on destination.')
"""
for user in src_users:
    try:
        logging.info('Creating "{name}" user.'.format(name=user['summary']['user']['username']))

        results = users.create(
            conn=dst_conn,
            name=user['summary']['user']['username'],
            password='',
            email=user['summary']['user']['email'],
            groups=user['groups']
            )

    except ValueError:
        logging.info('Error creating "{name}" dataset.'.format(name=dataset['dataSet']['name']))
"""
