def export_cluster_configuration(conn):
    """ Given a connection, return a the cluster configuration as a binary blob. """
    try:
        return conn.get(url='/config/data')
    except SystemError as e:
        raise e


def import_cluster_configuration(conn, config):
    """ Given a connection and a binary blob, attempt to import the cluster configuration."""
    try:
        return conn.post(url='/config/data', data=config.encode('utf-8'), headers={'Content-type': 'application/octet-stream'})
    except SystemError as e:
        raise e
