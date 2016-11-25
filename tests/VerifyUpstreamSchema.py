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

        stats[self.__class__.__name__] += 1

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.context)


class Empty(TestValidationError):
    """The example or schema was blank. It should be populated."""


class EmptySchema(Empty):
    """The example or schema was blank. It should be populated."""


class EmptyExample(Empty):
    """The example or schema was blank. It should be populated."""


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
            raise EmptyExample('Missing example.', context=context)

        if schema is None:
            raise EmptyExample('Missing schema.', context=context)

        try:
            example = json.loads(examplestring)
        except Exception as e:
            raise SchemaValidationError("Schema isn't valid JSON.", context=context, exception=e)
        if example == {}:
            raise EmptyExample("Example = {}", context=context)

        if args.no3 and schema['$schema'] == 'http://json-schema.org/draft-03/schema':
            raise Schema03('', context=context)

        if type(schema)==str:
            schema_string_reason = None
            try:
                json.loads(schema)
            except Exception as e:
                schema_string_reason = e
            raise SchemaValidationError("Schema is a string??", context=context, exception=schema_string_reason)

        if schema['$schema'] in [
                'http://json-schema.org/draft-03/schema',
                'http://json-schema.org/draft-04/schema',
                'http://json-schema.org/draft-03/schema#',
                'http://json-schema.org/draft-04/schema#']:
            try:
                jsonschema.validate(example, schema)
                if not args.quiet:
                    logging.debug('Valid: {}'.format(context))
                    stats['Valid'] += 1
                return True

            except jsonschema.exceptions.SchemaError as e:
                raise SchemaValidationError("Schema is valid JSON, but not valid JSON Schema", context=context, exception=e)

            except jsonschema.exceptions.ValidationError as e:
                raise ExampleVsSchemaValidationError("The example is not valid per this schema", context=context, exception=e)

        else:
            raise UnknownSchemaType("Can't test schema {}".format(schema['$schema']), context=context)

    except Empty as e:
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
        # A body isn't strictly required. For example, the server may respond with a HTTP 200 with no JSON
        # logging.warning("MissingBody: {} {} {}".format(verb, path, ctx))
        # stats['MissingBody'] += 1
        return

    for mime in body:
        critical = None
        try:
            test_example_against_schema(body[mime].example, body[mime].schema, verb, path, ctx)
        except Empty as e:
            logging.warning(str(e))
            critical = e.innerexception  # unpack inner exception, such as a jsonschema.exceptions.SchemaError
        except TestValidationError as e:
            logging.error(str(e))
            critical = e.innerexception  # unpack inner exception, such as a jsonschema.exceptions.SchemaError
        if critical and args.fastfail:
            raise critical


def skipis(resource, islist, name=""):
    if resource.is_:
        for isness in resource.is_:
            if isness in islist:
                # logging.debug("Ignoring %s for isness %s" % (name, isness))
                return True
        return False


def check_resources(resources, name=""):
    for resource in resources:
        isness = []

        if args.skipis and skipis(resources[resource], args.skipis, name=(name + resource)):
            stats['skipis'] += 1
            continue

        isness = resources[resource].is_ or []
        if 'internal' not in isness and 'supported' not in isness and 'techPreview' not in isness:
            isness.append("supported")
        if 'authenticated' in isness:
            isness.remove('authenticated')  # unimportant for logging

        supportedResource = "[%s]" % ",".join(isness)
        if resources[resource].methods:
            for method in resources[resource].methods:
                m = resources[resource].methods[method]
                if method != 'get':
                    check_body(m.body, method, name + resource, supportedResource)

                for response in m.responses:
                    if str(response) in args.skipresponse:
                        stats['skipresponse'] += 1
                        continue
                    check_body(m.responses[response].body, method, name + resource, "response " + str(response) + " " + supportedResource)

        if resources[resource].resources:
            check_resources(resources[resource].resources, name + resource)


def check_raml_file(ramlfile_path):
    import pyraml.parser

    root = pyraml.parser.load(ramlfile_path)

    check_resources(root.resources)

    return root


def parse_url_response(raml, verb, route, response, status=200, contenttype='application/json'):
    routechunks = route.split('/')[1:]

    resource = raml
    for _ in routechunks:
        resource = resource.resources['/' + _]

    body = resource.methods[verb].responses[status].body[contenttype]
    return test_example_against_schema(response, body.schema, verb=verb, path=route, ctx="example")


if __name__ == "__main__":
    global args

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s')
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
    parser.add_argument("--skipis", action="append", default=[],
                        help="ignore any resource which 'is' in this list; e.g., techPreview")
    parser.add_argument("--skipresponse", action="append", default=[],
                        help="ignore any resource response in this list; e.g., 404")
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
