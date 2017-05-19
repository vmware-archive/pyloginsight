def list(conn):
    """ Given a connection, return a list of group ids. """
    return [group['id'] for group in conn.get(url='/groups')['groups']]


def get(conn, id):
    """ Given a connection and group id, return a dictionary describing the group. """
    return {
        'summary': dict(conn.get('/groups/{id}'.format(id=id))),
        'datasets': [x['id'] for x in conn.get('/groups/{id}/datasets'.format(id=id))['dataSets']],
        'users': [x['id'] for x in conn.get('/groups/{id}/users'.format(id=id))['users']],
        'capabilities': [x['id'] for x in conn.get('/groups/{id}/capabilities'.format(id=id))['capabilities']]
    }

def put(conn, name, capabilities):
    """ Given a connection, name, and capabilities, create a group. """
    pass