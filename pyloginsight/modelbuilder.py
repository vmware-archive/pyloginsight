#!/usr/bin/env python

import python_jsonschema_objects as pjs
import json
import io
import os
import sys


# Basic help.
if len(sys.argv) != 2:
    print('Specify one schema file.')
    sys.exit()


# Load the specified schema file.
with open(sys.argv[1]) as f:
    schema_dict = json.load(f)

# Generate a title (assumed missing for now).
title = '_'.join(os.path.basename(sys.argv[1]).split('.')[:-1])

# Generate a class name.  python_jsonschema_objects may have a function that
# does this already.
class_name = ''.join([x.title() for x in os.path.basename(sys.argv[1]).split('.')[:-1] if not x.isspace()])

# Modify the schema to include a title.
schema_dict['title'] = title

# Provide ObjectBuilder with the modified dict.
builder = pjs.ObjectBuilder(schema_dict)

# Build the classes.
ns = builder.build_classes()

# Print some information.
print("Generated title: {}".format(title))
print("Generated class_name: {}".format(class_name))
print("Detected the following classes: {}".format(str(dir(ns))))


# Store the types in a dict using the class_name.
classes = {}
classes[class_name] = getattr(ns, class_name)

# Create a variable using class that was detected.
variable = classes[class_name]()

# Output the type of the variable.
print("Created variable of type: {}".format(str(type(variable))))
