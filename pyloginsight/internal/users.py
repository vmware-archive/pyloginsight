def list(conn):
    """ Given a connection, return a list of user id values."""
    return [user['id'] for user in conn.get(url='/users')['users']]


def get(conn, id):
    """ Given a connection and a user id, return a dictionary describing the user, including datasets, roles, capabilities, 
    and content. """
    return {
        'summary': dict(conn.get('/users/{id}'.format(id=id))),
        'datasets': [x['id'] for x in conn.get('/users/{id}/datasets'.format(id=id))['dataSets']],
        'groups': [x['id'] for x in conn.get('/users/{id}/groups'.format(id=id))['groups']],
        'capabilities': [x['id'] for x in conn.get('/users/{id}/capabilities'.format(id=id))['capabilities']],
        'content': conn.get(url='/content/usercontent/{id}?namespace=com.private.content.{id}'.format(id=id))
    }


def put(conn, user):
    """ Given a connection and a dictionary, create a user. """
    pass