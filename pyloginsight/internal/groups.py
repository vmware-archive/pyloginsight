import logging
import time

def list(conn):
    """
    Given a connection, return a list of group ids.
    
    :param conn: A connection object. 
    :return: A list of group ids.
    """
    return [group['id'] for group in conn.get(url='/groups')['groups']]


def get(conn, id):
    """
    Given a connection and an id, return dictionary describing the group.
    
    :param conn: A connection object. 
    :param id: A group id.
    :return: A dictionary describing the group with the provided id.
    """
    t0 = time.perf_counter()
    product = {
        'summary': dict(conn.get('/groups/{id}'.format(id=id))),
        'datasets': [x['id'] for x in conn.get('/groups/{id}/datasets'.format(id=id))['dataSets']],
        'users': [x['id'] for x in conn.get('/groups/{id}/users'.format(id=id))['users']],
        'capabilities': [x['id'] for x in conn.get('/groups/{id}/capabilities'.format(id=id))['capabilities']]
    }
    t1 = time.perf_counter()
    #logging.info("Get dataset took {:4f}".format(t1-t0))
    return product


def name_to_ids(conn, name):
    """
    Given a connection and a name, return a list of group ids with that name.
    
    :param conn: A connection object. 
    :param name: A name of one or more groups.
    :return: A list of group ids.
    """
    logging.info('Getting group (role) {id}'.format(id=id))
    return [group['id'] for group in conn.get(url='/groups')['groups'] if group['name'] == name]


def create(conn, name, capabilities):
    """
    Given a connection, name, and capabilities, create a group.
    
    :param conn: A connection object. 
    :param name: A name for the group.
    :param capabilities: A list of capabilities for the group.
    :return: The id of the group created as a string.
    """

    """
    Read the source code, and I believe the following is expected:
    
       ValidationErrors vErrors = new ValidationErrors().isListOf("dataSets", UUID.class, false, false)
                    .isListOf("capabilities", String.class, requireCapabilities, requireCapabilities)
                    .requiredOf("name", String.class, requireName)
                    .validate(this);
                    
    {
        "dataSets": [UUID1, UUID2],
        "capabilities": ["ANALYTICS"],
        "name": "users"
    }
    
    
    return conn.post(url='/groups', json={'name': name, 'capabilities': capabilities})['group']['id']
    """
    raise NotImplemented