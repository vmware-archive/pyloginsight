def list(conn):
    """ Given an connection, return a list of providers. """
    try:
        return conn.get(url='/auth-providers')['providers']
    except SystemError as e:
        raise e


