def list(conn):
    """ Given a connection, return a list of content namespaces. """
    return [contentpack['namespace'] for contentpack in conn.get(url='/content/contentpack/list')['contentPackMetadataList']]


def get(conn, namespace):
    """ Given a connection and a namespace, return dictionary describing the content. """
    return dict(conn.get('/content/contentpack/{namespace}'.format(namespace=namespace)))


def put(conn, dataset):
    """ Given a connection and a dictionary, create a dataset. """
    pass