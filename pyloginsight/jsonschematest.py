#!/usr/bin/env python
from __future__ import print_function
import python_jsonschema_objects
import sys
import logging
import json


def main(q):
    
    
    EVENTSSCHEMA='''                {
                  "$schema": "http://json-schema.org/draft-04/schema",
                  "properties": {
                    "events": {
                      "description": "Lists events that match the query.",
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "text": {
                            "description": "The full text of the event.",
                            "type": "string"
                          },
                          "timestamp": {
                            "description": "The time the event was reported, in milliseconds since 00:00:00 UTC on 1 January 1970",
                            "type": "integer"
                          },
                          "fields": {
                            "description": "The fields of the event.",
                            "type": "array",
                            "items": [
                              {
                                "type": "object",
                                "properties": {
                                  "name": {
                                    "description": "The field name.",
                                    "type": "string"
                                  },
                                  "content": {
                                    "description": "The content of the field.",
                                    "type": "string"
                                  }
                                }
                              }
                            ]
                          }
                        }
                      }
                    },
                    "complete": {
                        "description": "Indicates whether all matching events were returned (true), or if only some of them where, because the timeout expired (false).",
                        "type": "bool"
                    },
                    "duration": {
                        "description": "The time required to compute the results, in milliseconds.",
                        "type": "number"
                    }
                  },
                  "type": "object"
                }'''
    SESSIONSCHEMA='''{
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
    s4 = json.loads(SESSIONSCHEMA)
    
    if "title" not in s4:
        s4["title"]="Session"
    
    #print (SESSIONSCHEMA)
    builder = python_jsonschema_objects.ObjectBuilder(s4)
    ns = builder.build_classes()
    print(ns)
    print(dir(ns))
    
    example = ""
    s = getattr(ns, "Session")()
    print (s)
    print (dir(s))
    
    s.username="userGuy"
    s.password="a"
    print(s)
    print(s.serialize())
    
    return ns
    




if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    main(None)