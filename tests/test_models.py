import pytest
import pyloginsight.models


def test_namedtupe_without_parameters():
    with pytest.raises(TypeError):
        ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass')


def test_namedtupe_with_bad_parameters():
    with pytest.raises(TypeError):
        ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', pumpkins=5)


def test_namedtuple_with_good_paramters_bad_data():
    with pytest.raises(TypeError):
        ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=5)


def test_namedtyple_with_only_fields_as_list():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['field1', 'field2'])
    assert ThingClass() == ThingClass(field1=None, field2=None)
    thing = ThingClass()
    assert thing.field1 is None
    assert thing.field2 is None
    assert ThingClass().field1 is None
    assert ThingClass().field2 is None


def test_namedtyple_with_only_fields_as_string():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields='field1 field2')
    assert ThingClass() == ThingClass(field1=None, field2=None)
    thing = ThingClass()
    assert thing.field1 is None
    assert thing.field2 is None
    assert ThingClass().field1 is None
    assert ThingClass().field2 is None


def test_namedtyple_with_values_as_list_of_strings():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['field1', 'field2'], values=['value1', 'value2'])
    assert ThingClass() == ThingClass(field1='value1', field2='value2')
    thing = ThingClass()
    assert thing.field1 == 'value1'
    assert thing.field2 == 'value2'
    assert ThingClass().field1 == 'value1'
    assert ThingClass().field2 == 'value2'

def test_namedtyple_with_values_as_list_of_empty_tuples():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['tuple1', 'tuple2'], values=[(), ()])
    assert ThingClass() == ThingClass(tuple1=(), tuple2=())
    thing = ThingClass()
    assert thing.tuple1 == ()
    assert thing.tuple2 == ()
    assert ThingClass().tuple1 == ()
    assert ThingClass().tuple2 == ()


def test_namedtyple_with_values_as_list_of_empty_strings():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['string1', 'string2'], values=['', ''])
    assert ThingClass() == ThingClass(string1='', string2='')
    thing = ThingClass()
    assert thing.string1 == ''
    assert thing.string2 == ''
    assert ThingClass().string1 == ''
    assert ThingClass().string2 == ''


def test_namedtype_setting_values_on_instance():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['string1', 'string2'], values=['', ''])
    thing = ThingClass()
    with pytest.raises(AttributeError):
        thing.string1 = 'pumpkin'
        thing.string2 = 'toothpaste'


def test_namedtyple_with_values_as_list_of_none():
    ThingClass = pyloginsight.models.named_tuple_with_defaults('ThingClass', fields=['none1', 'none2'], values=[None, None])
    assert ThingClass() == ThingClass(none1=None, none2=None)
    thing = ThingClass()
    assert thing.none1 is None
    assert thing.none2 is None
    assert ThingClass().none1 is None
    assert ThingClass().none2 is None

