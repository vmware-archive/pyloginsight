# -*- coding: utf-8 -*-

from requests import HTTPError


class ServerError(BaseException):
    """A generic error reported by the server."""


class ResourceNotFound(ValueError):
    """A resource, like a User or Dataset, was not found on the remote Log Insight server."""


class TransportError(HTTPError):
    """Base class for all communication problems with a remote Log Insight server."""


class Unauthorized(TransportError):
    """Credentials are invalid, expired, or not suitible for attempted operation."""


class Cancel(RuntimeError):
    """Update to server intentionally cancelled from within a context manager."""


class ServerWarning(UserWarning):
    """The remote Log Insight server emitted a warning for an API resource."""


class NotBootstrapped(ServerError):
    """The server has not yet been bootstrapped."""


class AlreadyBootstrapped(ServerError):
    """The server has already been bootstrapped, you can't bootstrap it again."""
