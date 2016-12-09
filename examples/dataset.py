#!/usr/bin/env python

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

    def __init__(self, name, description, constraints):
        self.name = name
        self.description = description
        self.constraints = constraints

    def dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'constraints': self.constraints
        }

    def __repr__(self):
        """A human-readable representation of the constraint, in constructor form."""
        return '{cls}(id={x.name!r}, description={x.description!r}, constraint_list={x.constraints})'.format(cls=self.__class__.__name__, x=self)

