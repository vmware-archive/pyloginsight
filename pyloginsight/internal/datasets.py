import logging
import time

def list(conn):
    """
    Given a connection, return a list of dataset ids.
    
    :param conn: A connection object. 
    :return: A list of dataset ids.
    """
    return [dataset['id'] for dataset in conn.get(url='/datasets')['dataSets']]


def get(conn, id):
    """
    Given a connection and dataset id, return a dictionary describing the dataset.
    
    :param conn: A connection object. 
    :param id: A dataset id.
    :return: A dictionary describing the dataset with the provided id.
    """
    t0 = time.perf_counter()
    product = conn.get('/datasets/{id}'.format(id=id))
    t1 = time.perf_counter()
    #logging.info("Get dataset took {:4f}".format(t1-t0))
    return product


def name_to_ids(conn, name):
    """
    Given a connection and a name, return a list of dataset ids of datasets that have that name.
    
    :param conn: A connection object. 
    :param name: A name of one more more datasets.
    :return: A list of dataset ids.
    """
    return [dataset['id'] for dataset in conn.gett(url='/datasets')['dataSet'] if dataset['name'] == name]


def create(conn, name, description, constraints):
    """
    Given a connection, name, description, and a list of constraints, create a dataset. 
    
    :param conn: A connection.
    :param name: A name for the dataset.
    :param description: A description for the dataset.
    :param constraints: A list of constraints.
    :return: The id of the dataset as a string.
    """

    """
    constraints = [{'name': field, 'operator': 'CONTAINS', 'value': value, 'fieldType': 'STRING'}]
    data = json.dumps({'name': name, 'description': description, 'constraints': constraints})
    
    return conn.post(url='/datasets', json={'name': name, 'description': description, 'constraints': json.dumps(constraints)})['dataSet']['id']
    """
    raise NotImplemented

