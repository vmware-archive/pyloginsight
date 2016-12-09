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
   
