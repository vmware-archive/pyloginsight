#!/usr/bin/env python

import logging
import collections
from .exceptions import ServerError, ResourceNotFound, TransportError, Unauthorized
import abc
import attr


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
        try:
            resp = self._connection.delete("{0}/{1}".format(self._baseurl, item))
        except ResourceNotFound:
            raise KeyError(item)
        return True

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
        resp = self._connection.post(self._baseurl, json=self._createspec(value)._asdict())
        try:
            return resp['id']  # new UUID for this object, probably accessible at _baseurl/{id}
        except KeyError:
            return True

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

    """
    def __get__(self, obj, objtype):
        if callable(self):
            self.__init__(obj)
            return self()
        else:
            raise AttributeError("Cannot retrieve {0} from {1}".format(self.__class__.__name__, objtype.__name__))

    def __set__(self, obj, value):
        raise AttributeError()

    """

    @property
    @abc.abstractmethod
    def _baseurl(self):
        """Path to the server-hosted object collection root. Must be implemented by child classes. For example, `_baseurl='/licenses'`."""
        raise NotImplementedError

    def asdict(self):
        """GET against the collection's base url, producing a collection-specific summary. Used as the basis for all getters/iterators."""
        return self._connection.get(self._baseurl)

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

class ServerProperty(object):
    """
    Descriptor for a server's object property. Writes updates to the server on property change.
    """

    def __init__(self, clazz, readonly=False):
        self.clazz = clazz
        self.value = None

        if readonly:
            self.__set__ = False

    def lookup_attrib(self, owner):
        for attrib in dir(owner):
            if getattr(owner, attrib) is self:
                return attrib
        #print ("Fallthrough lookup_attrib on", owner)

    def __get__(self, instance, objtype):
        if instance is None:
            return self
        attribute_name = self.lookup_attrib(objtype)
        self._name = attribute_name

        print("Trying to read server property", attribute_name, "from", instance)

        #return self.value
        if callable(self.clazz):
            return self.clazz.from_server(instance._connection)
        else:
            raise AttributeError("Cannot retrieve {0} from {1}".format(self.__class__.__name__, objtype.__name__))

    def __set__(self, instance, value):
        if instance is None:
            return self
        attribute_name = self.lookup_attrib(type(instance))
        self._name = attribute_name

        print("Trying to write server property", attribute_name, "from", instance)
        self.value = value

        #raise AttributeError()


@attr.s
class Entity(object):
    _url = attr.ib(default=None)
    _raw = None

    @classmethod
    def from_server(cls, connection, url=None):
        if cls._url == None and url == None:
            raise AttributeError("Cannot read object from server without a url")
        body = connection.get(url or cls._url)
        instance = cls(url=url, **body)
        instance._raw = body
        return instance

    def to_server(self, connection, url=None):
        if url is None:
            url = self._url
        body = attr.asdict(self)
        del body['_url']
        response = connection.put(url, json=body)
        return response

    def __get__(self, instance, objtype):
        print("__get__(", instance, objtype)