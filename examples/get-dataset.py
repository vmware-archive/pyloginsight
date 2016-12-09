#!/usr/bin/env python


from pyloginsight.Connection import Connection, Server, Credentials
from pyloginsight.query import Constraint
from dataset import Dataset
import argparse


class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and
    datasets. """

    @property
    def datasets(self):
        """ Get a list of datasets and their properties. DISCLAIMER: At the time of writing this API was a technical preview. """
        datasets = []
        for dataset in self._get('/datasets').json()['dataSets']:

            constraints = []
            for constraint in dataset['constraints']:
                constraints.append(
                    Constraint(
                        field=constraint['name'],
                        operator=constraint['operator'],
                        value=constraint['value']
                    )
                )

            datasets.append(
                Dataset(
                    id=dataset['id'],
                    name=dataset['name'],
                    description=dataset['description'],
                    type=dataset['type'],
                    constraints=constraints
                )
            )

        return datasets


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=False, default=None)
    parser.add_argument('-p', '--password', required=False, default=None)
    parser.add_argument('-P', '--provider', required=False, default=None)
    parser.add_argument('-s', '--server', required=True)
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

    print('\n'.join([str(dataset) for dataset in server.datasets]))

