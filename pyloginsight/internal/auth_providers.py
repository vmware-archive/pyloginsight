def list(conn):
    """ Given an connection, return a list of providers. """
    return conn.get(url='/auth-providers')['providers']
