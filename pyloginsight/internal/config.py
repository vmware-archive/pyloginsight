def download(conn):
    """ Given a connection, return a the cluster configuration as a binary blob. """
    return conn.get(url='/config/data')


def upload(conn, config):
    """ Given a connection and a binary blob, attempt to import the cluster configuration."""
    return conn.post(
        url='/config/data',
        data=config.encode('utf-8'),
        headers={'Content-type': 'application/octet-stream'}
    )

