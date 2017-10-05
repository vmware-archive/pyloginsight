#!/usr/bin/env python

from pyloginsight.content import PackSchema, AlertSchema
from collections import OrderedDict
import json
import argparse
import logging


def is_schema(data, schema):
    errors = schema().loads(schema().dumps(data).data).errors
    if errors == {}:
        logging.info('Matches schema {}'.format(schema.__name__))
        return True
    else:
        logging.info('Does not match {} with error: {}'.format(schema.__name__, errors))
        return False


def iterate(data, schema, itemlist=[]):
    if isinstance(data, (dict, OrderedDict)):
        logging.info('Found dict with {} key/value pairs.'.format(len(data.keys())))
        if is_schema(data, schema):
            itemlist.append(data)
        else:
            for key, value in data.items():
                if value is not None:
                    logging.info('Iterating over key {}'.format(key))
                    iterate(value, schema, itemlist)

    if isinstance(data, list):
        logging.info('Found list with {} records'.format(len(data)))
        for item in data:
            logging.info('Iterating over index {}'.format(data.index(item)))
            iterate(item, schema, itemlist)

    return itemlist


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('pack')
    args = parser.parse_args()

    log_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s'
    if args.debug:
        logging.basicConfig(format=log_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=log_format, level=logging.WARN)

    with open(args.pack, 'r') as f:
        pack = PackSchema().loads(f.read())

    results = iterate(data=pack.data, schema=AlertSchema)
    print(json.dumps(results, indent=2, sort_keys=True))

