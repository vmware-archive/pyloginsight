#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import collections
from .exceptions import ResourceNotFound, Cancel, InefficientGetterUsesIteration
import abc
import warnings
from marshmallow import Schema, pre_load, post_dump, post_load
from collections import Mapping
import weakref

logger = logging.getLogger(__name__)
ABC = abc.ABCMeta('ABC', (object,), {})


def bind_to_model(cls):
    import weakref
    if cls.__model__ is not None:
        logger.error("Binding schema {} to model {}".format(cls, cls.__model__))
        cls.__model__.__schema__ = weakref.proxy(cls)
    else:
        logger.error("Binding schema {} to model skipped, no model reference.".format(cls))
    return cls


class DirectlyAddressableContainerMapping(object):
    """
    A mapping container which exposes discrete mapping objects at their own URLs,
    in the form /api/v1/collection/uuid.
    Avoids InefficientGetterUsesIteration
    """
    def __contains__(self, item):
        try:
            self._connection.get("{0}/{1}".format(self._baseurl, item))
        except ResourceNotFound:
            return False
        return True

    def __getitem__(self, item):
        """
        Retrieve details for a single item from the server. Could raise KeyError.
        """
        url = "{0}/{1}".format(self._baseurl, item)
        return self._single.from_server(self._connection, url)


class ServerDictMixin(collections.MutableMapping):
    """
    A server-backed dictionary of items.
    Deleting or updating an item usually means DELETE/PUTing a single item's resource.
    Produces items as dynamic subclass of collections.namedtuple.
    Frequently used along with `AppendableServerDictMixin`.
    Mutually-incompatible with the `ServerListMixin`.
    """
    _connection = None

    def __delitem__(self, item):
        try:
            self._connection.delete("{0}/{1}".format(self._baseurl, item))
        except ResourceNotFound:
            raise KeyError(item)
        return True

    def __getitem__(self, item):
        """
        Retrieve details for a single item from the server. Could raise KeyError.
        """
        warnings.warn(str(self.__class__), InefficientGetterUsesIteration)
        for k, v in self.items():
            if k == item:
                return v
        raise KeyError

    def items(self):
        """
        Retrieve full objects directly from the summary view. May be stale, but faster to iterate.
        This is an alternate to using d[k], which invokes __getitem__ to make an HTTP request.
        """

        if not hasattr(self, '_schema'):
            raise SyntaxWarning("Missing __model__ or @bind_to_model on {}".format(self.__class__))
        ser = self._schema()

        parse = ser.load(self._iterable, many=True, partial=False)

        if parse.errors:
            for e in parse.errors.items():
                logger.warning("Parse error when loading items: {}".format(str(e)))

        for item in parse.data:
            item['_connection'] = self._connection
            item['_url'] = "{0}/{1}".format(self._baseurl, item['id'])
            yield (item['id'], item)

    def keys(self):
        ser = self._schema()
        parse = ser.load(self._iterable, many=True, partial=True)

        if parse.errors:
            for e in parse.errors:
                logger.warning("Parse error when loading keys: {}".format(str(e)))

        return [item['id'] for item in parse.data]

    def __iter__(self):
        for key in self.keys():
            yield key

    def __len__(self):
        return len(self._iterable[self._schema.__envelope__['many']])

    def __setitem__(self, key, value):
        raise NotImplementedError

    @property
    def _iterable(self):
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
        return len(self._iterable)

    def insert(self, index, value):
        raise NotImplementedError

    def remove(self, index):
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

        :param value: any python object which will be marshaled by self._schema().dump(value):
        :return uuid: url-fragment identifier for the newly-created server-side object
        """

        ser = self._schema()

        transmit = ser.dump(value, many=False)
        if transmit.errors:
            logger.warning("Error serializing a {}: {}".format(self.__class__, transmit.errors))

        body = transmit.data

        try:
            body = ser.__envelope__['append'](body)
        except KeyError:
            pass
        resp = self._connection.post(self._baseurl, json=body)

        logger.debug("Server responded with new object {}/{}".format(self._baseurl, resp))
        # new UUID for this object, probably accessible at _baseurl/{id}

        # TODO pass marshmallow context

        # Some interfaces produce an 'id' key on the root object
        if 'id' in resp:
            return resp['id']

        # Some interfaces produce an enveloped object
        parse = ser.load(resp, many=False, partial=True)
        if parse.errors:
            logger.warning("Error deserializing to a {}: {}".format(self.__class__, parse.errors))
        item = parse.data

        if 'id' in item:
            return item['id']
        logger.warning("Created new object via {} successfully, but no ID was returned: {}".format(self._baseurl, resp))
        return None


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
        logger.debug("ServerAddressableObject -> {} GET {}".format(self.__class__, self._baseurl))
        return self._connection.get(self._baseurl)

    def __call__(self):
        """
        An idealized representation of the object.
        Default implementation returns the top-level dict; override in child class.
        """
        warnings.warn("TODO: Should a ServerAddressableObject be callable?")
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


class RemoteObjectProxy(object):
    """
    Base class for a remote object. Such an object has a URL, but the object gets to declare its own expected properties.

    Compatible with objects based on both Attribs and Python-JsonSchema-Objects.

    For simple resources consisting of a single value, use ::ServerProperty:: instead.
    """

    __connection = None
    __url = None

    def publish_new_instance_to_server(self, connection, baseurl):
        return connection.post(baseurl, json=self._serialize())

    @classmethod
    def from_dict(cls, connection, url, data, many=None):
        schema = cls.__schema__()

        schema.context.update({"url": url, "connection": connection})
        body, errors = schema.load(data, many=False)
        for e in errors:
            logger.warning("Error deserializing field {}=>{} in from_dict(data={})".format(str(e), errors[e], data))
        return body

    @classmethod
    def from_server(cls, connection, url):
        try:
            body = connection.get(url)
        except ResourceNotFound:
            raise KeyError(url)
        self = cls.from_dict(connection, url, body)
        return self

    def _serialize(self):
        """
        The instance validates & serializes itself, returning a dict suitible for json.dumps().
        Called from to_server, and from collections to create new server-side entities.
        May or may not already have an `id` or __url.
        """
        data, errors = self.__schema__().dump(self)
        for e in errors:
            logger.warning("Error serializing for sending to the server: {}".format(str(e)))

        return data

    def to_server(self, connection, url=None):
        """
        The instance validates & serializes itself, then writes back to the server at an existing URL with PUT.
        Alternatively, replace the existing instance in the collection with this instance, `d[k]=instance`.
        To create a new server-side entity, add this instance to a collection, `d.append(instance)`.
        """
        if url is None:
            url = str(object.__getattribute__(self, "__url"))
            if url is None:
                raise AttributeError("Cannot submit object to server without a url")

        return connection.put(url, json=self._serialize())

    def __enter__(self):
        connection = object.__getattribute__(self, "__connection")
        if connection is None:
            raise RuntimeError("Cannot use {0} as a content manager without a connection object.".format(self.__class__))
        url = str(self.__url)
        if not url:
            raise AttributeError("Cannot submit object to server without a url")
        # Consider returning a deep copy.
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            if exc_type == Cancel:
                return True
            logger.warning("Dropping changes to {b} due to exception {e}".format(b=self, e=exc_value))

        else:
            connection = object.__getattribute__(self, "__connection")
            self.to_server(connection, self.__url)

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(["{}={!r}".format(k, self[k]) for k in self])
        )

    @property
    def _iterable(self):
        """Default behavior is to iterate over a named child element."""
        return self.get(self._basekey)


class ServerProperty(object):
    """
    Descriptor for a server's object property. Makes outbound HTTP requests on access.
    """

    def __init__(self, clazz, url=None, readonly=False):
        self.clazz = clazz
        self.value = None
        self.url = url

        if readonly:
            self.__set__ = False

    def lookup_attrib(self, owner):
        for attrib in dir(owner):
            if getattr(owner, attrib) is self:
                return attrib

    def __get__(self, instance, objtype):
        if instance is None:
            return self
        attribute_name = self.lookup_attrib(objtype)
        self._name = attribute_name

        logger.debug("Trying to read server property {} from {}".format(attribute_name, instance))

        if callable(self.clazz):
            return self.clazz.from_server(instance._connection, self.url)
        else:
            raise AttributeError("Cannot retrieve {0} from {1}".format(self.__class__.__name__, objtype.__name__))

    def __set__(self, instance, value):
        if instance is None:
            return self
        attribute_name = self.lookup_attrib(type(instance))
        self._name = attribute_name

        logger.debug("Trying to write server property {} from {}".format(attribute_name, instance))
        self.value = value

        raise NotImplementedError


class ObjectSchema(Schema):
    @post_load
    def make_object(self, data):
        logger.debug("Inflating a new object {}: {}".format(self.__model__, data))
        logger.debug("Inflating a new object with context: {}".format(self.context))
        o = self.__model__(**data)

        for k, v in self.context.items():
            object.__setattr__(o, "__" + k, v)
        return o

class EnvelopeObjectSchema(ObjectSchema):
    # Custom options
    __envelope__ = {
        'single': None,
        'many': None
    }
    __model__ = None

    def get_envelope_key(self, many):
        """Helper to get the envelope key. None indicates no envelope."""
        key = self.__envelope__['many'] if many else self.__envelope__['single']
        if key is None:
            raise SyntaxWarning("Schema {} has __envelope__ containing None".format(self.__class__))
        return key

    @pre_load(pass_many=True)
    def unwrap_envelope(self, data, many):
        key = self.get_envelope_key(many)
        if many and key and isinstance(data[key], Mapping):
            # List-ify the collection, moving the key into the 'id' field
            def _f(x):
                if 'id' in x[1] and x[1]['id'] != x[0]:
                    warnings.warn("Object already had an 'id' property that differs from the key: {}".format(x))
                x[1]['id'] = x[0]
                return x[1]
            data[key] = list(map(_f, data[key].items()))

        return data[key] if key else data

    @post_dump(pass_many=True)
    def wrap_with_envelope(self, data, many):
        key = self.get_envelope_key(many)
        return {key: data}
