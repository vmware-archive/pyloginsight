#!/usr/bin/env python

from pyloginsight.models import Server
from models import DatasetSpec
import argparse
import sys


class ServerPlus(Server):


    def add_dataset(self, name, constraints, description=""):
        """ Add a dataset. DISCLAIMER: At the time of writing this API was a technical preview. """

        data = DatasetSpec(name=name, description=description, constraints=constraints).json()
        response = server._post('/datasets',data=data)

        if not response.ok:
            for (field, errors) in response.json()['errorDetails'].items():

                if field == 'name':
                    print('The --field {m}'.format(m=errors[0]['errorMessage'].replace('Value','value')))

                if field == 'operator':
                    print('The --operator {m}'.format(m=errors[0]['errorMessage'].replace('Value','value')))
                
                if field == 'fieldType':
                    print('The --type {m}'.format(m=errors[0]['errorMessage'].replace('Value','value')))
            sys.exit(1)
       

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-P', '--provider', required=True)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-n', '--name', required=True)
    parser.add_argument('-d', '--description', required=False, default="")
    parser.add_argument('-f', '--field', required=True)
    parser.add_argument('-v', '--value', required=True)
    parser.add_argument('-c', '--operator', default='CONTAINS')
    parser.add_argument('-t', '--type', default='STRING')
    args = parser.parse_args()

    server = ServerPlus(args.server, verify=False)
    server.login( username=args.username, password=args.password, provider=args.provider)

    constraints = [{'name': args.field, 'operator': args.operator, 'value':args.value, 'fieldType': args.type}]  
    server.add_dataset(name=args.name, description=args.description, constraints=constraints)

       
