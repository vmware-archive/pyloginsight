import json
import python_jsonschema_objects
import logging

def _declare_object(jsonschema, name=None):
    global _container
    _ = json.loads(jsonschema)
    if name:
        _['title'] = name
    else:
        name = _['title']
    builder = python_jsonschema_objects.ObjectBuilder(_)
    ns = builder.build_classes()
    _container[name] = ns

    print("Created object %s" % name )

def get(name):
    global _container
    try:
        return getattr(_container[name], name)
    except:
        print(_container[name])
        print(dir(_container[name]))
        raise

def create(name, jsonstring):
    global _container
    clazz = get(name)
    try:
        return clazz.from_json(jsonstring)
    except ValueError:
        logging.exception("Failed to parse JSON: %s" % jsonstring)
        raise
    except python_jsonschema_objects.validators.ValidationError:
        logging.exception("Failed to marshal JSON object to %s" % clazz)
        raise
_container = {}



SESSION='''{
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
              "username": {
                  "type": "string"
              },
              "password": {
                  "type": "string"
              },
              "provider": {
                  "type": "string",
                  "pattern": "^(Local|ActiveDirectory)$"
              }
            },
            "required": ["username", "password"],
            "type": "object",
            "additionalProperties": false
          }'''

_declare_object(SESSION, "Createsession")

_declare_object('''{
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
              "userId": {
                  "type": "string"
              },
              "sessionId": {
                  "type": "string"
              },
              "ttl": {
                  "type": "integer"
              }
            },
            "required": ["userId", "sessionId"],
            "type": "object",
            "additionalProperties": false
        }''', "Activesession")

_declare_object('''{
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
              "releaseName": {"type": "string"},
              "version": {"type":"string"}
            },
            "required": ["releaseName", "version"],
            "type": "object",
            "additionalProperties": false
        }''', "Serverversion")

_declare_object('''{
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
              "username": {"type": "string"}
            },
            "required": ["username"],
            "type": "object",
            "additionalProperties": false
        }''', "Newdeployment")


_declare_object('''{
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
              "errorMessage": {"type": "string"},
              "errorCode": {"type":"string"},
              "errorDetails": {"type":"string"}
            },
            "type": "object",
            "additionalProperties": true
        }''', "Servererror")

_declare_object('''{
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
              "errorMessage": {"type": "string", "pattern": "^This call isn't allowed after the LI server is bootstrapped$"},
              "errorCode": {"type":"string"},
              "errorDetails": {"type":"string"}
            },
            "type": "object",
            "additionalProperties": true
        }''', "Serveralreadybootstrapped")
