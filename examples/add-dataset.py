#!/usr/bin/env python

from pyloginsight.Connection import Connection, Server, Credentials
#from pyloginsight.query import Constraint
from dataset import DatasetSpec
import argparse
import sys

class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and
    datasets. """


    def add_dataset(self, name, constraints, description=""):
        """ Given a Dataset class instance, create it on the server. """

        data = DatasetSpec(name=name, description=description, constraints=constraints).json()
        response = server._post('/datasets',data=data)
        
        return response
       

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=False, default=None)
    parser.add_argument('-p', '--password', required=False, default=None)
    parser.add_argument('-P', '--provider', required=False, default=None)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-n', '--name', required=True)
    parser.add_argument('-d', '--description', required=False, default="")
    parser.add_argument('-f', '--field', required=True)
    parser.add_argument('-v', '--value', required=True)
    parser.add_argument('-c', '--operator', required=True)
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

    field_list = ["appname","hostname","procid","__li_source_path","vc_details","vc_event_type","vc_username","vc_vm_name"] 

    # Creating a dataset requires at least one constraint.
    # TODO: The existing Constraint class in the query module has some limitations I
    # need fo fix later.
    constraints = [{'name': args.field, 'operator': args.operator, 'value':args.value, 'fieldType': 'STRING'}]  
    
    response = server.add_dataset(name=args.name, description=args.description, constraints=constraints)

    if not response.ok and 'name' in response.json()['errorDetails']:
        try:
            print(response.json()['errorDetails']['name'][0]['errorMessage'].replace('Value', 'The --field value'))
        except:
            pass

    if not response.ok and 'operator' in response.json()['errorDetails']:
        try:
            print(response.json()['errorDetails']['operator'][0]['errorMessage'].replace('Value', 'The --operator value'))
        except:
            pass
        

