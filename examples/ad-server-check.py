#!/usr/bin/env python

import argparse
import getpass
import xml.etree.ElementTree as ET
from pyloginsight.connection import Connection, Credentials
from pyloginsight.internal import internal_config
from pyloginsight.exceptions import Unauthorized

# Suppress SSL warnings.
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Logging
import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Check AD configuration values across multiple hosts with the same credentials.')
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--provider', required=True)
    parser.add_argument('-s', '--servers', nargs='+', required=True)
    args = parser.parse_args()

    creds = Credentials(username=args.username, password=getpass.getpass('Password: '), provider=args.provider)
    for server in args.servers:
        try:
            conn = Connection(hostname=server, verify=False, auth=creds)
            config = internal_config.xml(conn)
            root = ET.fromstring(config)
        except Unauthorized:
            logging.error('Skipping {server} since provided credentials do not work.'.format(server=server))
            continue
        except requests.ConnectionError:
            logging.error('Skipping {server} due to connection error.  Check IP or FQDN.'.format(server=server))
            continue

        try:
            ad_domain_servers = root.find('./authentication/auth-method/ad-domain-servers').get('value')
        except AttributeError:
            ad_domain_servers = ''

        try:
            krb_domain_servers = root.find('./authentication/auth-method/krb-domain-servers').get('value')
        except AttributeError:
            krb_domain_servers = ''

        logging.info('The {server} server has a ad-domain-server value of "{ad}", and a krb-domain-servers '
                     'value of "{krb}".'.format(
                server=server,
                ad=ad_domain_servers,
                krb=krb_domain_servers
            )
        )
