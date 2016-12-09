#!/usr/bin/env python

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


