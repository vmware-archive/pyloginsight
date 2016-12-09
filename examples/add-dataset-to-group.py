#!/usr/bin/env python

from pyloginsight.Connection import Connection, Server, Credentials
from pyloginsight.query import Constraint
import argparse


class Capability():
    """ Class that helps interact with existing capability on the Log Insight server. """

    def __init__(self, id=""):
        self.ANALYTICS = 'ANALYTICS'
        self.DASHBOARD = 'DASHBOARD'
        self.EDIT_ADMIN = 'EDIT_ADMIN'
        self.EDIT_SHARED = 'EDIT_SHARED'
        self.INTERNAL = 'INTERNAL'
        self.INVENTORY = 'INVENTORY'
        self.STATISTICS = 'STATISTICS'
        self.VIEW_ADMIN = 'VIEW_ADMIN'
        self._CAPABILITIES = [self.ANALYTICS, self.DASHBOARD, self.EDIT_ADMIN,
                              self.EDIT_SHARED, self.INTERNAL, self.INVENTORY, self.STATISTICS, self.VIEW_ADMIN]
        self.id = id
        assert self.id in self._CAPABILITIES

    def dict(self):
        return {'id': self.id}

    def __repr__(self):
        """A human-readable representation of the capability, in constructor form."""
        return '{cls}(id={x.id!r})'.format(cls=self.__class__.__name__, x=self)


class Group():
    """ Class that helps interact an existing group on the Log Insight server. """

    def __init__(self, id, name, description, capabilities, required, editable):
        self.id = id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.required = required
        self.editable = editable

    def __repr__(self):
        """A human-readable representation of the group, in constructor form."""
        return '{cls}(id={x.id!r}, name={x.name!r}, description={x.description!r}, capabilities={x.capabilities!r}, required={x.required!r}, editable={x.editable!r})'.format(cls=self.__class__.__name__, x=self)


class Dataset():
    """ Class used to interact with and existing dataset on the Log Insight server. """

    def __init__(self, id, name, description, constraints, type):
        self.id = id
        self.name = name
        self.description = description
        self.constraints = constraints
        self.type = type

    def __repr__(self):
        """A human-readable representation of the dataset, in constructor form."""
        return '{cls}(id={x.id!r}, name={x.name!r}, description={x.description!r}, constraints={x.constraints!r}, type={x.type!r}'.format(cls=self.__class__.__name__, x=self)


class DatasetSpec():
    """ Class that defines a dataset that needs to be created. """
   
    def __init__(self, id="", name="", description="", constraints=[], type=""):
        self.name = name
        self.description = description
        self.constraints = constraints

    def __repr__(self):
        """A human-readable representation of the DatasetSpec, in constructor form."""
        return '{cls}(name={x.name!r}, description={x.description!r}, constraints={x.constraints!r}'.format(cls=self.__class__.__name__, x=self)
   

class PostDatasetSpec():
    """ Class that enforces the data being sent to LI when creating a dataset. """

    def __init__(self, name, description, constraint_list):
        self.name = name
        self.description = description
        self.constraint_list

    def dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'constraints': self.constraint_list
        }

    def __repr__(self):
        """A human-readable representation of the constraint, in constructor form."""
        return '{cls}(id={x.name!r}, description={x.description!r}, constraint_list={x.constraint_list})'.format(cls=self.__class__.__name__, x=self)


class PostGroupIdDatasetSpec():
    """ Class that helps validate and format the data being sent to LI when
    modifying datasets associated to a group. DISCLAIMER: At the time of
    writing this API was a technical preview. """

    def __init__(self, group_id, dataset_add_list, dataset_remove_list):
        self.group_id = group_id
        self.dataset_add_list = dataset_add_list
        self.dataset_remove_list = dataset_remove_list

    def dict(self):
        return {
            'dataSetsToAdd': self.dataset_add_list,
            'dataSetsToRemove': self.dataset_remove_list
        }

    def __repr__(self):
        """A human-readable representation of the constraint, in constructor form."""
        return '{cls}(group_id={x.group_id!r}, dataset_add_list={x.dataset_add_list!r}, dataset_remove_list={x.dataset_remove_list})'.format(cls=self.__class__.__name__, x=self)


class ServerPlus(Server):
    """ Extends the functionality of the Server class by adding groups, and
    datasets. """

    @property
    def groups(self):
        """ Get a list of groups and their properties. DISCLAIMER: At the time of writing this API was a technical preview. """

        groups = []
        for group in self._get('/groups').json()['groups']:
            capabilities = []

            for capability in group['capabilities']:
                capabilities.append(Capability(id=capability['id']))

            groups.append(
                Group(
                    id=group['id'],
                    name=group['name'],
                    description=group['description'],
                    required=bool(group['required']),
                    editable=bool(group['editable']),
                    capabilities=capabilities
                ))

        return groups

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


    def create_dataset(self, dataset):
        """ Given a Dataset class instance, create it on the server. """



        self._post('/datasets')
        pass

    def add_dataset_to_group(self, dataset, group):
        pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=False, default=None)
    parser.add_argument('-p', '--password', required=False, default=None)
    parser.add_argument('-P', '--provider', required=False, default=None)
    parser.add_argument('-s', '--server', required=True)
    parser.add_argument('-g', '--group', required=False, default=None)
    parser.add_argument('-d', '--dataset', required=False, default=None)
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


    if not args.group:
        print('\nNo group detected.  Getting groups: ')
        print('\n'.join([' - '.join([x.id, x.name]) for x in server.groups]))


    if not args.dataset:
        print('\nNo dataset detected.  Geting datasets: ')
        print('\n'.join([' - '.join([x.id, x.name]) for x in server.datasets]))

