

from requests import HTTPError


class ServerError(BaseException): pass


class ResourceNotFound(ValueError):
    """A resource, like a User or Dataset, was not found on the remote Log Insight server."""


class TransportError(HTTPError):
    """Base class for all communication problems with a remote Log Insight server"""


class Unauthorized(TransportError):
    """Credentials are invalid, expired, or not suitible for attempted operation."""


class Cancel(RuntimeError):
    """Update to server intentionally cancelled from within a context manager."""
