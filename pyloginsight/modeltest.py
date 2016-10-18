#!/usr/bin/env python

from jsonmodels import models, fields
import json
import six

class StringField(fields.StringField):
    def __repr__(self):
        return self.__get__(six.string_types)
class Cat(models.Base):

    name = fields.StringField(required=True)
    breed = fields.StringField()

    def __str__(self):
        try:
            txt = six.text_type(dict(self))
        except TypeError:
            txt = ''
        return '{name}: {text}'.format(
            name=self.__class__.__name__,
            text=txt,
        )


CAT='''{"name":"Sparks", "breed":"Whatever"}'''

CAT='''{"breed":"Whatever"}'''


def object_hook(dct):
    return Cat(**dct)

c = json.loads(CAT, object_hook=object_hook)
print(c)
print(dir(c))
