#!/usr/bin/env python

import python_jsonschema_objects as pjs
import json
import io
import os
import sys


# Where we keep the classes.
classes = {}


# Generate a title (assumed missing for now).
def get_title(filename):
    return '_'.join(os.path.basename(filename).split('.')[:-1])


# Generate a class name.  python_jsonschema_objects may have a function that
# does this already.
def get_class_name(filename):
   return ''.join([x.title() for x in os.path.basename(filename).split('.')[:-1] if not x.isspace()])



# Get a class given a filename.
def get_class(filename):
    # Load the specified schema file.
    with open(filename) as f:
        schema_dict = json.load(f)

    # Modify the schema to include a title.
    schema_dict['title'] = get_title(filename)

    # Provide ObjectBuilder with the modified dict.
    builder = pjs.ObjectBuilder(schema_dict)

    # Build the classes.
    ns = builder.build_classes()

    # Print some information.
    print("Detected the following classes: {}".format(str(dir(ns))))

    return getattr(ns, get_class_name(filename))


# Basic help.
if len(sys.argv) != 2:
    print('Specify one schema file.')
    sys.exit()


if os.path.isdir(sys.argv[1]):
    print('Directory provided.')
    files = [os.path.join(sys.argv[1],f) for f in os.listdir(sys.argv[1])]
    #print('Found files: {}'.format(str(files)))
    for fn in files:
        print('Adding {} from {}'.format(get_class_name(fn), fn))
        classes[get_class_name(fn)] = get_class(fn)


if os.path.isfile(sys.argv[1]):
    print('File provided.')

    # Store the types in a dict using the class_name.
    classes[get_class_name(sys.argv[1])] = get_class(sys.argv[1])


print(classes)
