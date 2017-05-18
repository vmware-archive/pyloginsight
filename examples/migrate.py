#!/usr/bin/env python

import argparse
import logging
import requests
import getpass

import pyloginsight.internal.config as li_config

from pyloginsight.connection import Connection, Credentials
from requests.packages.urllib3.exceptions import InsecureRequestWarning


# Configuring logging date/time format.
logging.basicConfig(format='%(message)s', level=logging.INFO)

logging.info("Suppressing SSL warnings.")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

parser = argparse.ArgumentParser()
parser.add_argument('--source-username', required=True)
parser.add_argument('--source-provider', default='Local')
parser.add_argument('--source-server', required=True)
parser.add_argument('--destination-username', required=True)
parser.add_argument('--destination-provider', default='Local')
parser.add_argument('--destination-server', required=True)

args = parser.parse_args()

logging.info('Creating session for source.')
src_creds = Credentials(
    username=args.source_username,
    password=getpass.getpass('Source password:'),
    provider=args.source_provider,
)
src_conn = Connection(hostname=args.source_server, verify=False, auth=src_creds)

logging.info('Creating session for destination.')
dst_creds = Credentials(
    username=args.destination_username,
    password=getpass.getpass('Destination password:'),
    provider=args.destination_provider,
)
dst_conn = Connection(hostname=args.destination_server, verify=False, auth=dst_creds)

logging.info('Exporting cluster configuration.')
src_config = li_config.export_cluster_configuration(src_conn)

logging.info('Importing cluster configuration.')
li_config.import_cluster_configuration(dst_conn, src_config)



#TODO: GET groups on source
#TODO: POST groups on destination
#TODO: GET datasets on source
#TODO: POST datasets on destination
#TODO: GET users on source
#TODO: POST users on destination

#TODO: GET system content on source
#TODO: POST system contnet on destination

# TODO: GET user content on source
#TODO: POST user content on destination
