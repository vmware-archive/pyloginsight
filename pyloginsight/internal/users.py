import logging
import time

def list(conn):
    """
    Given a connection, return a list of user id values.
    
    :param conn: A connection object. 
    :return: A list of user ids.
    """
    return [user['id'] for user in conn.get(url='/users')['users']]


def get(conn, id):
    """ Given a connection and a user id, return a dictionary describing the user, including datasets, roles, capabilities, 
    and content. """

    logging.info("Get information for user {id}".format(id=id))

    t0 = time.perf_counter()
    summary = conn.get('/users/{id}'.format(id=id))
    t1 = time.perf_counter()
    logging.info("Get summary took {:4f} seconds.".format(t1-t0))

    t0 = time.perf_counter()
    datasets = [x['id'] for x in conn.get('/users/{id}/datasets'.format(id=id))['dataSets']]
    t1 = time.perf_counter()
    logging.info("Get dataset took {:4f} seconds.".format(t1-t0))

    t0 = time.perf_counter()
    groups = [x['id'] for x in conn.get('/users/{id}/groups'.format(id=id))['groups']]
    t1 = time.perf_counter()
    logging.info("Get groups took {:4f} seconds.".format(t1-t0))

    t0 = time.perf_counter()
    capabilities = [x['id'] for x in conn.get('/users/{id}/capabilities'.format(id=id))['capabilities']]
    t1 = time.perf_counter()
    logging.info("Get capabilities took {:4f} seconds.".format(t1-t0))

    t0 = time.perf_counter()
    content = conn.get(url='/content/usercontent/{id}?namespace=com.private.content.{id}'.format(id=id))
    t1 = time.perf_counter()
    logging.info("Get content took {:4f} seconds.".format(t1-t0))


    return {
        'summary': summary,
        'datasets': datasets,
        'groups': groups,
        'capabilities': capabilities,
        'content': content
    }



def name_to_ids(conn, name):
    """
    Given a connection and a name, return the id of the user.
    
    :param conn: A connection object. 
    :param name: A name of one or more users.
    :return: A list of user ids.
    """
    return [user['id'] for user in conn.get(url='/users')['users'] if user['name'] == name]


def create(conn, name, password, email, groups, generate_api_key=False):
    """
    Given a connection and a dictionary, create a user.
    
    :param conn: A Connection object. 
    :param name: An username.
    :param password: A password.
    :param email: An e-mail address.
    :param groups: A list of groups for that the user will belong to.
    :param generate_api_key: True or false.
    :return: The id of the user as a string.
    """

    """
    return conn.post(url='/users', json={
        'username': name,
        'password': password,
        'email': email,
        'groupIds': groups,
        'generateApiKey': generate_api_key
    })['user']['id']
    """
    raise NotImplemented