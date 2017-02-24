

from requests import HTTPError


class ServerError(BaseException): pass

class ResourceNotFound(ValueError): pass

class TransportError(HTTPError): pass

class Unauthorized(TransportError): pass

