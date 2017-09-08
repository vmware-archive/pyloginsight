#!/usr/bin/env python

import argparse
import logging
import requests
import getpass
import warnings
import sys
import csv

from pyloginsight.connection import Connection, Credentials
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pyloginsight.internal import users

# Configuring logging date/time format.
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

logging.info("Suppressing SSL warnings.")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.info('Suppressing API warnings.')
warnings.simplefilter('ignore')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--source-password')
    parser.add_argument('--source-username')
    parser.add_argument('--source-provider', default='Local', help='(Default = "Local")')
    parser.add_argument('--source-server', required=True)
    parser.add_argument('--destination-password')
    parser.add_argument('--destination-username')
    parser.add_argument('--destination-provider', default='Local', help='(Default = "Local")')
    parser.add_argument('--destination-server', required=True)
    args = parser.parse_args()

    if args.source_username:
        source_username = args.source_username
    else:
        source_username = input('Source({server}) username:')

    if args.destination_username:
        destination_username = args.destination_username
    else:
        destination_username = input('Destination({server}) username:')

    if args.destination_password:
        destination_password = args.destination_password
    else:
        destination_password = getpass.getpass('Destination({server}) password:'.format(server=args.destination_server))

    if args.source_password:
        source_password = args.source_password
    else:
        source_password = getpass.getpass('Source({server}) password:'.format(server=args.source_server))

    logging.info('Creating session for source.')
    src_creds = Credentials(
        username=source_username,
        password=source_password,
        provider=args.source_provider,
    )
    src_conn = Connection(hostname=args.source_server, verify=False, auth=src_creds)

    logging.info('Creating session for destination.')
    dst_creds = Credentials(
        username=args.destination_username or input('Destination({server}) username:'),
        password=args.destination_password or
                 getpass.getpass('Destination({server}) password:'.format(server=args.destination_server)),
        provider=args.destination_provider,
    )
    dst_conn = Connection(hostname=args.destination_server, verify=False, auth=dst_creds)

    src_users = users.summary(src_conn)
    dst_users = users.summary(dst_conn)

    logging.info('Getting source user names.')
    src_usernames = [user['username'] for user in src_users]
    logging.info('Found {count} users.'.format(count=len(src_users)))

    logging.info('Getting destination user names.')
    dst_usernames = [user['username'] for user in dst_users]
    logging.info('Found {count} users.'.format(count=len(dst_users)))

    logging.info('Generating list of user names on both source and destination.')
    common_usernames = list(set(src_usernames).intersection(dst_usernames))
    logging.info('Found {count} users.'.format(count=len(common_usernames)))

    logging.info('Generating list of user names that are only on the source.')
    src_usernames_not_in_dst = [user for user in src_usernames if user not in dst_usernames]
    logging.info('Found {count} users.'.format(count=len(src_usernames_not_in_dst)))

    fieldnames = [
        'username',
        'src_host',
        'src_id',
        'src_fields',
        'src_queries',
        'src_alerts',
        'src_dashboards',
        'src_type',
        'dst_host',
        'dst_id',
        'dst_fields',
        'dst_queries',
        'dst_alerts',
        'dst_dashboards',
        'dst_type'
    ]

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    for common_user in common_usernames:
        if common_user == 'jjosh':
            continue
        else:
            logging.info('Generating output for {user}'.format(
                src=args.source_server,
                dst=args.destination_server,
                user=common_user,))
            for src_id in [user['id'] for user in src_users if user['username'] == common_user]:
                logging.info('Getting content from {id} at {src}'.format(src=args.source_server, id=src_id))
                src_content = users.get_content(src_conn, src_id)

                for dst_id in [user['id'] for user in dst_users if user['username'] == common_user]:
                    logging.info('Getting content from {id} at {dst}'.format(dst=args.destination_server, id=dst_id))
                    dst_content = users.get_content(dst_conn, dst_id)

                    writer.writerow(
                        {
                            'username': common_user,
                            'src_host': args.source_server,
                            'src_id': src_id,
                            'src_fields': len(src_content['extractedFields']),
                            'src_queries': len(src_content['queries']),
                            'src_alerts': len(src_content['alerts']),
                            'src_dashboards': len(src_content['dashboardSections']),
                            'src_type': [user['type'] for user in src_users if user['id'] == src_id][0],
                            'dst_host': args.destination_server,
                            'dst_id': dst_id,
                            'dst_fields': len(dst_content['extractedFields']),
                            'dst_queries': len(dst_content['queries']),
                            'dst_alerts': len(dst_content['alerts']),
                            'dst_dashboards': len(dst_content['dashboardSections']),
                            'dst_type': [user['type'] for user in dst_users if user['id'] == dst_id][0]
                        }
                    )


    for src_user in src_usernames_not_in_dst:
        logging.info('Generating output for {user}'.format(user=src_user))
        for src_id in [user['id'] for user in src_users if user['username'] == src_user]:
            logging.info('Getting content from {id} at {src}'.format(src=args.source_server, id=src_id))
            src_content = users.get_content(src_conn, src_id)

            writer.writerow(
                {
                    'username': src_user,
                    'src_host': args.source_server,
                    'src_id': src_id,
                    'src_fields': len(src_content['extractedFields']),
                    'src_queries': len(src_content['queries']),
                    'src_alerts': len(src_content['alerts']),
                    'src_dashboards': len(src_content['dashboardSections']),
                    'src_type': [user['type'] for user in src_users if user['id'] == src_id][0],
                    'dst_host': args.destination_server,
                    'dst_id': None,
                    'dst_fields': 0,
                    'dst_queries': 0,
                    'dst_alerts': 0,
                    'dst_dashboards': 0,
                    'dst_type': None
                }
            )
