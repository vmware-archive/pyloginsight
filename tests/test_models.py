import pyloginsight.models


def test_named_tuple_with_defaults():

    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields='field1 field2')
    assert ThingClass() == ThingClass(field1=None, field2=None)

    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['field1', 'field2'])
    assert ThingClass() == ThingClass(field1=None, field2=None)

    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['field1', 'field2'], values=['value1', 'value2'])
    assert ThingClass() == ThingClass(field1='value1', field2='value2')

    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['tuple1', 'tuple2'], values=[(), ()])
    assert ThingClass() == ThingClass(tuple1=(), tuple2=())

