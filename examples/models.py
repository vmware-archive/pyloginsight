#!/usr/bin/env python

import json

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
    # TODO: This needs to support constraints.  We may want to add constraints
    # to datasets as a separate operation.
   
    def __init__(self, name, description="", constraints=[]):
        self.name = name
        self.description = description
        self.constraints = constraints

    def json(self):
        return json.dumps({
            'name': self.name,
            'description': self.description,
            'constraints': self.constraints
            })

    def __repr__(self):
        """A human-readable representation of the DatasetSpec, in constructor form."""
        return '{cls}(name={x.name!r}, description={x.description!r})'.format(cls=self.__class__.__name__, x=self)

 
class Capability():
    """ Class used to interact with and existing capability on the Log Insight server. """

    def __init__(self, id):
        self.id = id

    def json(self):
        return json.dumps({
            'id': self.id
            })

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


class GroupSpec():
    """ Class that defines a group that needs to be created. """

    def __init__(self, name, capabilities, description="", datasets=[]):
        self.name = name
        self.capabilities = capabilities
        self.description = description
        self.datasets = datasets

    def json(self):
        return json.dumps({
            'name': self.name,
            'description': self.description,
            'capabilities': self.capabilities,
            'datasets': self.datasets
            })

    def __repr__(self):
        """A human-readable representation of the group specification, in constructor form."""
        return '{cls}(name={x.name!r}, capabilities={x.capabilities!r}, description={x.description!r}, datasets={x.datasets!r})'.format(cls=self.__class__.__name__, x=self)


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


