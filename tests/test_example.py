# -*- coding: utf-8 -*-
from __future__ import print_function
import logging

logger = logging.getLogger(__name__)


# content of test_sample.py
def func(x):
    return x + 1


def test_answer():
    assert func(3) == 4


def test_ok():
    logger.warning("This is a warning in test_ok")
    assert True
