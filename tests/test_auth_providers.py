# -*- coding: utf-8 -*-

from pyloginsight.internal import auth_providers


def test_list(connection):
    product = auth_providers.list(connection)
    assert type(product) == list
    assert len(product) >= 1
    assert 'Local' in product
