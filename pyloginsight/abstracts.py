#!/usr/bin/env python

import logging
import collections
from .connection import ServerError  # Consider refactoring exceptions out of the `connection` module
import abc

logger = logging.getLogger(__name__)
ABC = abc.ABCMeta('ABC', (object,), {})


class ServerDictMixin(collections.MutableMapping):
    """
    A server-backed dictionary of items.
    Deleting or updating an item usually means DELETE/PUTing a single item's resource.
    Produces items as dynamic subclass of collections.namedtuple.
    Frequently used along with `AppendableDictMixin`.
    Mutually-incompatible with the `ServerListMixin`.
    """
    def __delitem__(self, item):
        resp = self._connection._delete("{0}/{1}".format(self._baseurl, item))
        if resp.status_code == 200:
            return True
        elif resp.status_code == 404:
            raise KeyError("Unknown license key uuid {0}".format(item))
        else:
            raise ServerError(resp.json()['errorMessage'])
        # TODO: Should raise KeyError on unknown license key.

    def __getitem__(self, item):
        """
        Retrieve details for a single item from the summary of all items. Could raise KeyError.
        If `_fromserver()` is defined, call it to instantiate an object. Otherwise, produce a collections.namedtuple"""
        x = self._iterable[item]
        if hasattr(self, "_fromserver"):
            return self._fromserver(**x)
        else:
            return collections.namedtuple(self.__class__.__name__, x.keys())(**x)

    def keys(self):
        return self._iterable.keys()

    def __iter__(self):
        for key in self.keys():
            yield key

    def __len__(self):
        return len(self._iterable)

    def __setitem__(self, key, value):
        raise NotImplementedError

    @property
    def _iterable(self):
        """
        How to navigate from the top-level container summary to a list/dict of child items.
        Default implementation returns the top-level dict; override in child class.
        """
        return self.asdict()


class ServerListMixin(collections.MutableSequence):
    """
    A server-backed list of items.
    Removing, inserting or appending an item usually means making a pair of GET/POST requests to the server.
    Mutually-incompatible with the `ServerDictMixin`.
    """

    def append(self, value):
        raise NotImplementedError

    def __add__(self, value):
        self.append(value)

    def __len__(self):
        return self.count()

    def insert(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    @property
    def _iterable(self):
        """
        How to navigate from the top-level container summary to a list/dict of child items.
        Default implementation returns the top-level dict; override in child class.
        """
        return self.asdict()


class AppendableServerDictMixin(object):
    """
    A list-like interface for adding a new item to a server-backed collection.
    The server will assign a new UUID when inserting into the mapping.
    A subsequent request to keys/iter will include the new item.
    Mix into :class:ServerAddressableObject:
    """
    def append(self, value):
        """
        Add a new item to the server-backed collection.
        The server will assign a new UUID when inserting into the mapping.
        If the server response includes the new UUID, return it.
        A subsequent request to keys/iter will include the new item.

        :param value: any python object which will be passed to and marshaled by :func:self._createspec:
        :return uuid: url-fragment identifier for the newly-created server-side object
        """
        resp = self._connection._post(self._baseurl, json=self._createspec(value)._asdict())
        if resp.status_code in [400, 409, 500]:
            raise ValueError(resp.json()['errorMessage'])
        elif resp.status_code == 201:
            try:
                return resp.json()['id']  # new UUID for this object, probably accessible at _baseurl/{id}
            except KeyError:
                return True
        try:
            raise ServerError(resp.status_code, resp.json()['errorMessage'])
        except KeyError:
            raise ServerError(resp.status_code, resp.text)

    @abc.abstractmethod
    def _createspec(self, value):
        """
        Structure to marshal a new entity being created on the server. Must contain a json-serializable `_asdict()` method.
        These examples are equivalent:

            _createspec = collections.namedtuple("License", ("key",))

            class _createspec(object):
                def __init__(self, key):
                    self.key = key
                def _asdict(self):
                    return {"key": self.key}
        """
        pass


class ServerAddressableObject(ABC):
    """
    Base class for all sever-addressable objects.
    Children are expected to use adjacent *Mixin classes in conjunction with this.
    """
    def __init__(self, connection):
        self._connection = connection
        if ServerDictMixin in self.__class__.__mro__ and ServerListMixin in self.__class__.__mro__:
            raise TypeError("ServerDictMixin and ServerListMixin are mutually-exclusive concepts. They both try to define __iter__")

    @property
    @abc.abstractmethod
    def _baseurl(self):
        """Path to the server-hosted object collection root. Must be implemented by child classes. For example, `_baseurl='/licenses'`."""
        raise NotImplementedError

    def asdict(self):
        """GET against the collection's base url, producing a collection-specific summary. Used as the basis for all getters/iterators."""
        return self._connection._get(self._baseurl).json()

    def __call__(self):
        """
        An idealized representation of the object.
        Default implementation returns the top-level dict; override in child class.
        """
        return self.asdict()

    # The combination of __dir__ and __getattr__ makes it seem like realized objects have properties that are populated on-demand,
    # even when inspected with hasattr() or dir() or a debugger(), albeit with a server round-trip.
    def __dir__(self):
        """Make a remote request to determine the remote object's keys, added to the client's methods and properties."""
        names = list(self.asdict().keys()) + list(self.__class__.__dict__.keys())
        return [x for x in sorted(set(names)) if not x.startswith("_")]

    def __getattr__(self, name):
        # return self().get(name) # Delegate?
        t = self.asdict()
        if name in t:
            return t[name]
        raise AttributeError(name)
