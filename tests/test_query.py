import pytest
import warnings
from pyloginsight.query import Constraint, Parameter
from pyloginsight import operator

"""Examples from "Specifying constraints" section of https://vmw-loginsight.github.io/#Querying-data"""


def test_constraint_example1_text_contains():
    assert "/text/CONTAINS%20ERROR" == str(Constraint(field="text", operator=operator.CONTAINS, value="ERROR"))


def test_constraint_example2_timestamp_greaterthan():
    assert "/timestamp/%3E1451606400000" == str(Constraint(field="timestamp", operator=operator.GT, value="1451606400000"))


def test_constraint_example3_compound():
    assert "/timestamp/%3E0/text/CONTAINS%20ERROR" == ''.join([
        str(Constraint(field="timestamp", operator=operator.GT, value="0")),
        str(Constraint(field="text", operator=operator.CONTAINS, value="ERROR"))
    ])


def test_constraint_LAST_with_timestamp():
    # Constraints LAST must be used with a number, and cannot be used with non-timestamp
    assert "/timestamp/LAST60000" == str(Constraint(field="timestamp", operator=operator.LAST, value=60000))
    assert "/timestamp/LAST60000" == str(Constraint(field="timestamp", operator=operator.LAST, value="60000"))
    with pytest.raises(ValueError):
        assert str(Constraint(field="not-timestamp-field", operator=operator.LAST, value=60000))


def test_constraint_numeric_operators_reject_strings():
    with pytest.raises(ValueError):
        assert str(Constraint(field="x", operator=operator.GT, value="string"))
    with pytest.raises(ValueError):
        assert str(Constraint(field="timestamp", operator=operator.LAST, value="string"))


def test_constraint_pathalogical_encoding():
    pathalogic = '''field @#$%^&/;\,.<a>'"value'''
    encoded = '''field%20%40%23%24%25%5E%26%2F%3B%5C%2C.%3Ca%3E%27%22value'''
    assert "/" + encoded + "/HAS%20" + encoded == str(Constraint(field=pathalogic, operator=operator.HAS, value=pathalogic))


def test_constraint_exists():
    # Exists; cannot pass a non-empty value
    with warnings.catch_warnings(record=True) as w:
        assert "/x/EXISTS" == str(Constraint(field="x", operator=operator.EXISTS, value="something"))
        assert len(w) == 1


def test_parameters():
    x = Parameter(order="ASC", limit=4, timeout=20, contentpackfields="x,y,z", super="abc")
    print(x)
