#!/usr/bin/env python

# Rough and dirty validation of upstream RAML+JsonSchema

from __future__ import print_function
import logging
import json
import jsonschema
import sys
import argparse

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





def check_raml_file(ramlfile_path):
    import pyraml.parser

    root = pyraml.parser.load(ramlfile_path)

    check_resources(root.resources)

    return root



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

    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    parsedramlroot = check_raml_file(args.filename)

    version = """{
                "releaseName": "GA",
                "version": "1.2.3-4567890"
              }"""

    example = json.loads(version)

    print(parse_url_response(raml=p, verb='get', route='/version', status=200, response=example))
