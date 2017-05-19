def list(conn):
    """ Given a connection, return a list of dataset ids. """
    return [dataset['id'] for dataset in conn.get(url='/datasets')['dataSets']]


def get(conn, id):
    """ Given a connection and an id, return dictionary describing the dataset. """
    return dict(conn.get('/datasets/{id}'.format(id=id)))


def put(conn, dataset):
    """ Given a connection and a dictionary, create a dataset. """
    pass