#!/usr/bin/env python

import python_jsonschema_objects as pjs
import json
import io
import os
import sys

if len(sys.argv) != 2:
    print('Specify one schema file.')
    sys.exit()

filename = sys.argv[1]
schema = open(filename).read()
schema_dict = json.loads(schema)
title = '_'.join(os.path.basename(filename).split('.')[:-1])
schema_dict['title'] = title
schema = io.StringIO(json.dumps(schema_dict))
builder = pjs.ObjectBuilder(schema_dict)
ns = builder.build_classes()

print(title)
print(dir(ns))
