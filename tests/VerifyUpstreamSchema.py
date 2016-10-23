#!/usr/bin/env python

# Rough and dirty validation of upstream RAML+JsonSchema

from __future__ import print_function
import python_jsonschema_objects
import sys
import logging
import json
import os
import jsonschema
import traceback
import ramlfications


d = None

def test():
    BASEDIR = "../../../strata/loginsight/components/webservice/docs/src/"

    known_examples = os.listdir(os.path.join(BASEDIR,"examples"))
    known_schemas = os.listdir(os.path.join(BASEDIR,"schema"))

    # Validate Example against Schema
    validate = [
        ("users.id.get.response.json", "users.id.get.response.schema.json"),
        ("users.get.response.json", "users.get.response.schema.json"),
        ("ad.request.json", "ad.schema.json"),
        ("ad.response.json", "ad.schema.json"),


        #'adgroups.get.response.json', 'adgroups.type.domain.name.capabilities.get.response.json',
         #'adgroups.type.domain.name.get.response.json', 'aggregated-events.get.response.basic.json',
        # 'aggregated-events.get.response.json', 'aggregated-events.get.response.simple.json',
        #('events.get.response.json', 'events.get.response.simple.json',

        ('alert.history.record.get.response.json','alert.history.record.get.response.schema.json'),
        ('alert.history.record.put.request.json','alert.history.record.put.request.schema.json'),
        ('alert.get.response.json','alert.get.response.schema.json'),
        ('alert.history.records.get.response.json','alert.history.records.get.response.schema.json'),
        ('alerts.get.response.json','alerts.get.response.schema.json'),
        ('deployment.new.post.request.json','deployment.new.post.request.schema.json'),
        ('users.post.request.json','users.post.request.schema.json'),
        ('users.post.response.json','users.post.response.schema.json'),


        #'error.detailed.schema.json',
        #'error.message.schema.json', 'events.get.response.schema.json', ,

        ('events.get.response.simplewarnings.json', 'events.get.response.schema.json'),
        ('events.get.response.simple.json', 'events.get.response.schema.json'),
        ('events.get.response.json', 'events.get.response.schema.json'),

        ('aggregated-events.get.response.json', 'aggregated-events.get.response.schema.json'),

        ('aggregated-events.get.response.simple.json', 'aggregated-events.get.response.schema.json'),
        ('aggregated-events.get.response.simplewarnings.json', 'aggregated-events.get.response.schema.json'),


        ('events.ingest.post.request.json','events.ingest.post.request.schema.json'),
        ('events.ingest.post.response.json', 'events.ingest.post.response.schema.json'),
        ('deployment.join.post.request.json','deployment.join.post.request.schema.json'),
        ('deployment.join.post.response.json', 'deployment.join.post.response.schema.json'),
        ('deployment.approve.post.request.json', 'deployment.approve.post.request.schema.json'),
        ('deployment.approve.post.response.json', 'deployment.approve.post.response.schema.json'),


        ('error.deploymenterror.json', 'error.detailed.schema.json'),
        ('error.ad.wrong_credentials.json', 'error.detailed.schema.json'),
        ('error.deployment.not_boostrapped.json', 'error.message.schema.json'),
        ('ad.response.json','ad.schema.json'),
        ('ad.request.json','ad.schema.json'),

        #('agent.status.get.response.json', 'agent.status.get.response.schema.json')

    ]

    for p in validate:
        with open(os.path.join(BASEDIR,"examples", p[0]),'r') as f:
            example = json.load(f)
        with open(os.path.join(BASEDIR,"schema", p[1]), 'r') as f:
            schema = json.load(f)

        try:
           jsonschema.validate(example, schema)
        except:
            sys.stderr.write("\n\n\nFailed to validate {0} against {1}\n".format(p[0],p[1]))
            traceback.print_exc()
            break

        if p[0] in known_examples:
            known_examples.remove(p[0])
        if p[1] in known_schemas:
            known_schemas.remove(p[1])

    sys.stderr.write("\n\n\n=================\nSummary\n".format(p[0], p[1]))

    sys.stderr.write("\nUntested examples:\n")
    sys.stderr.write(str(known_examples))
    sys.stderr.write("\nUntested schemas:\n")
    sys.stderr.write(str(known_schemas))
    sys.stderr.write("\n")


def test_example_against_schema(examplestring, schema, verb=None, path=None, ctx=None):
    """
    Example is a raw blob of JSON.
    Schema has already been parsed to an OrderedDict.
    """
    context = "{} {} {}".format(verb, path, ctx)
    if examplestring is None:
        print('Missing example, ignoring context={}'.format(context))
        return False
    if schema is None:
        print('Missing schema, ignoring context={}'.format(context))
        return True
    try:
        example = json.loads(examplestring)
        if example == {}:
            #print('Empty Dict Example! context={}'.format(context))
            return False
    except:
        #print('Not valid JSON example, ignoring context={}'.format(context))
        return False

    if schema['$schema'] in ['http://json-schema.org/draft-03/schema', 'http://json-schema.org/draft-04/schema']:
        # JSON Schema
        #print(" -> Can test {0} against {1}".format(example, schema))

        try:
            jsonschema.validate(example, schema)
            print('Success! context={}'.format(context))

        except jsonschema.exceptions.SchemaError:
            print('The schema is not valid! context={}'.format(context), file=sys.stderr)
            raise
        except jsonschema.exceptions.ValidationError:
            print('The example is not valid per this schema! context={}'.format(context), file=sys.stderr)
            raise
            #import time
            #time.sleep(1)
            #traceback.print_exc()

    else:
        print("Can't test schema {} context={}".format(schema['$schema'], context))

def check_body(body, verb=None, path=None, ctx=None):
    """
    A RamlBody is a set of Formats comprised of a Schema and Example, either in the Request or Response sections
    :param body:
    :return:
    """
    if body is None:
        #context = "{} {} {}".format(verb, path, ctx)
        #print('Missing body, ignoring context={}'.format(context))
        return

    for mime in body:
        test_example_against_schema(body[mime].example, body[mime].schema, verb, path, ctx)


def check_resources(resources, name=""):
    for resource in resources:
        #print("{} has methods {}".format(resource, resources[resource].methods))
        if resources[resource].methods:
            for method in resources[resource].methods:

                m = resources[resource].methods[method]

                try:
                    check_body(m.body, method, name+resource, "")
                except:
                    print("FAIL check {0} {1}{2}".format(method, name, resource))
                    raise

                for response in m.responses:
                    check_body(m.responses[response].body, method, name+resource, "response")

        if resources[resource].resources:
            check_resources(resources[resource].resources, name+resource)





def check_raml_file():
    BASEDIR = "/Users/acastonguay/workspace/strata/loginsight/components/webservice/docs/src/"

    import pyraml.parser

    root = pyraml.parser.load(os.path.join(BASEDIR, "api.raml"))

    check_resources(root.resources)

    return root


    #r = ramlfications.parse()


def parse_url_response(raml, verb, route, response, status=200, contenttype='application/json'):
    s = raml.resources[route].methods[verb].responses[status].body[contenttype].schema
    return s

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    test()

    p = check_raml_file()


    version = """{
                "releaseName": "GA",
                "version": "1.2.3-4567890"
              }"""

    example = json.loads(version)

    print(parse_url_response(raml=p, verb='get', route='/version', status=200, response=example))