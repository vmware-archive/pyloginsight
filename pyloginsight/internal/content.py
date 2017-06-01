import logging
import time
from pyloginsight.exceptions import TransportError

def list(conn):
    """ Given a connection, return a list of content namespaces. """
    return [contentpack['namespace'] for contentpack in conn.get(url='/content/contentpack/list')['contentPackMetadataList']]


def get(conn, namespace):
    """ Given a connection and a namespace, return dictionary describing the content. """
    t0 = time.perf_counter()
    product = conn.get('/content/contentpack/{namespace}'.format(namespace=namespace))
    t1 = time.perf_counter()
    #logging.info("Get content took {:4f}".format(t1-t0))
    return product

def create(conn, content):
    """ Given a connection and a dictionary, create a dataset. """
    try:
        logging.info('Importing {id}'.format(id=content['contentPackId']))
        return conn.post(url='/content/contentpack?overwrite=true', json=content)
    except TransportError:
        logging.info('Error importing {id}'.format(id=content['contentPackId']))
        pass

