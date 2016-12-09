#!/usr/bin/env python

from pyloginsight.Connection import Connection, Server, Credentials
from pyloginsight.query import Constraint
import argparse


class Capability():
    """ Class represoenting a single capability. """

    def __init__(self, id=""):
        self.ANALYTICS = 'ANALYTICS'
        self.DASHBOARD = 'DASHBOARD'
        self.EDIT_ADMIN = 'EDIT_ADMIN'
        self.EDIT_SHARED = 'EDIT_SHARED'
        self.INTERNAL = 'INTERNAL'
        self.INVENTORY = 'INVENTORY'
        self.STATISTICS = 'STATISTICS'
        self.VIEW_ADMIN = 'VIEW_ADMIN'
        self._CAPABILITIES = [self.ANALYTICS, self.DASHBOARD, self.EDIT_ADMIN, self.EDIT_SHARED, self.INTERNAL, self.INVENTORY, self.STATISTICS, self.VIEW_ADMIN]
        self.id = id
        assert self.id in self._CAPABILITIES

    def dict(self):
        return {'id': self.id}

    def __repr__(self):
        """A human-readable representation of the constraint, in constructor form."""
        return '{cls}(id={x.id!r})'.format(cls=self.__class__.__name__, x=self)


class Group():
    """ Class that represents a single log insight group. """
    # Depending on how vIDM and AD groups appear, there may be room for a
    # subclass here.

    def __init__(self, group_id="", name="", description="", capabilities=[], required=False, editable=True, **kwargs):
        self.id = group_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.required = required
        self.editable = editable


    def __repr__(self):
        """A human-readable representation of the constraint, in constructor form."""
        return '{cls}(id={x.id!r}, name={x.name!r}, description={x.description!r}, capabilities={x.capabilities!r}, required={x.required!r}, editable={x.editable!r})'.format(cls=self.__class__.__name__, x=self)


class PostDatasetSpecification():
    """ Class that enforces the data being sent to LI when creating a
    dataset. DISCLAIMER: This API may be experimental and not supported. """

    def __init__(self, name, description, constraint_list):
        self.name = name
        self.description = description
        self.constraint_list

    def __repr__(self):
        return {
            'name': self.name,
            'description': self.description,
            'constraints': self.constraint_list
        }


class PostGroupIdDatasetSpec():
    """ Class that helps validate and format the data being sent to LI when
    modifying datasets associated to a group. DISCLAIMER: At the time of
    writing this API was a technical preview. """

    def __init__(self, group_id, dataset_add_list, dataset_remove_list):
        self.group_id = group_id
        self.dataset_add_list = dataset_add_list
        self.dataset_remove_list = dataset_remove_list

    def __repr__(self):
        return {
            'dataSetsToAdd': self.dataset_add_list,
            'dataSetsToRemove': self.dataset_remove_list
        }


class ServerPlus(Server):

    @property
    def users(self):
        """ Get a list of users and their properties. DISCLAIMER: At the time of writing this API was a technical preview. """
        #return self._get('/users').json()['users']
        raise NotImplemented

    @property
    def groups(self):
        """ Get a list of groups and their properties. DISCLAIMER: At the time of writing this API was a technical preview. """

        # Too complext for list comprehensions, my refactor later.
        # Iterate over all of the groups to create instances of the Group class.
        groups = []
        for group in self._get('/groups').json()['groups']:
            capabilities = []
            
            # Iterate over all of the capabilities to create instances of
            # Capability class
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
    def ad_groups(self):
        """ Get a list of active directory groups and their properties.  DISCLAIMER: At the time of writing this API was a technical preview. """
        #return self._get('/authgroups/ad').json()
        raise NotImplemented

    @property
    def datasets(self):
        """ Get a list of datasets and their properties. DISCLAIMER: At the time of writing this API was a technical preview. """
        #return self._get('/datasets').json()['datasets']
        raise NotImplemented



if __name__ == "__main__":

    # Basic CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('password')
    parser.add_argument('provider')
    parser.add_argument('server')
    args = parser.parse_args()

    # Credentials
    creds = Credentials(
        username=args.username,
        password=args.password,
        provider=args.provider)

    # Use modified Server class.
    server = ServerPlus(
        args.server,
        auth=creds,
        verify=False)

