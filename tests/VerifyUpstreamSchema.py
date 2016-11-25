#!/usr/bin/env python

# Rough and dirty validation of upstream RAML+JsonSchema

from __future__ import print_function
import logging
import json
import jsonschema
import sys
import argparse
import collections

stats = collections.Counter()

class TestValidationError(RuntimeError):
    def __init__(self, message, context, exception=None):
        super(RuntimeError, self).__init__(message)
        self.innerexception = exception
        self.context = context

        stats[self.__class__.__name__]+=1

    def __str__(self):
        #if self.innerexception is None:
        return "%s: %s" % (self.__class__.__name__, self.context)
        #else:
        #    return "%s: %s:\n%s" % (self.__class__.__name__, self.context, self.innerexception)

class EmptyBody(TestValidationError):
    """The example or schema body was blank. It should be populated."""

class SchemaValidationError(TestValidationError):
    """The schema was invalid."""

class ExampleVsSchemaValidationError(TestValidationError):
    """The example was invalid according to the schema."""

class Schema03(SchemaValidationError):
    """JSONSchema03 shouldn't be used."""

class UnknownSchemaType(TestValidationError):
    """Schema isn't JSONSchema03 or JSONSchema04"""

def test_example_against_schema(examplestring, schema, verb=None, path=None, ctx=None):
    """
    Example is a raw blob of JSON.
    Schema has already been parsed to an OrderedDict.
    """
    context = "{} {} {}".format(verb, path, ctx)

    try:
        if examplestring is None:
            raise EmptyBody('Missing example.', context=context)

        if schema is None:
            raise EmptyBody('Missing schema.', context=context)

        try:
            example = json.loads(examplestring)
        except Exception as e:
            raise SchemaValidationError("Schema isn't valid JSON.", context=context, exception=e)
        if example == {}:
            raise EmptyBody("Example = {}", context=context)

        if args.no3 and schema['$schema'] == 'http://json-schema.org/draft-03/schema':
            raise Schema03('', context=context)

        if schema['$schema'] in [
                'http://json-schema.org/draft-03/schema',
                'http://json-schema.org/draft-04/schema',
                'http://json-schema.org/draft-03/schema#',
                'http://json-schema.org/draft-04/schema#']:
            try:
                jsonschema.validate(example, schema)
                if not args.quiet:
                    logging.debug('Valid: context={}'.format(context))
                    stats['Valid']+=1
                return True

            except jsonschema.exceptions.SchemaError as e:
                raise SchemaValidationError("Schema is valid JSON, but not valid JSON Schema", context=context, exception=e)

            except jsonschema.exceptions.ValidationError as e:
                raise ExampleVsSchemaValidationError("The example is not valid per this schema", context=context, exception=e)

        else:
            raise UnknownSchemaType("Can't test schema {}".format(schema['$schema']), context=context)

    except EmptyBody as e:
        if not args.ignoremissing:
            raise e
    except SchemaValidationError as e:
        if not args.ignoreinvalidschema:
            raise e

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
        critical = None
        try:
            test_example_against_schema(body[mime].example, body[mime].schema, verb, path, ctx)
        except TestValidationError as e:
            logging.error(str(e))
            critical = e.innerexception  # unpack inner exception, such as a jsonschema.exceptions.SchemaError
        if critical and args.fastfail:
            raise critical


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
    routechunks = route.split('/')[1:]

    resource = raml
    for _ in routechunks:
        resource = resource.resources['/'+_]

    body = resource.methods[verb].responses[status].body[contenttype]
    return test_example_against_schema(response, body.schema)



if __name__ == "__main__":
    global args

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    try:
        import coloredlogs
        coloredlogs.install(level='DEBUG')
    except ImportError:
        pass  # if we don't get colors, that's not a big deal

    parser = argparse.ArgumentParser()


    parser.add_argument("filename",
                        help="Existing RAML file to be read. Required.")
    parser.add_argument("--fastfail", action="store_true", default=False,
                        help="Instead of processing all items, halt with the first exception.")
    parser.add_argument("--quiet", action="store_true", default=False,
                        help="Don't report success.")
    parser.add_argument("--ignoreinvalidschema", action="store_true", default=False,
                        help="If the schema is invalid, ignore it.")
    parser.add_argument("--ignoremissing", action="store_true", default=False,
                        help="If the schema/example is Blank or {}, ignore it.")
    parser.add_argument("--no3", action="store_true", default=False,
                        help="Treat JSONSchema Draft 3 as an error.")
    # supported

    args = parser.parse_args()
    if args.filename is None:
        parser.error("filename required")

    parsedramlroot = check_raml_file(args.filename)
    logger.info(stats)

    example = """{
      "masterAddress": "10.0.0.123",
      "masterUiPort": 80,
      "workerAddress": "10.0.0.124",
      "workerPort": 16520,
      "workerToken": "0ae94cb9-550a-4c01-85b9-3b7095e92321"
    }"""

    assert(parse_url_response(raml=parsedramlroot, verb='post', route='/deployment/join', status=200, response=example))
