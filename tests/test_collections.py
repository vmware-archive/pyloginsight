# -*- coding: utf-8 -*-
from __future__ import print_function
import pytest
from pyloginsight.abstracts import ServerAddressableObject, ServerDictMixin, ServerListMixin


def test_ServerDictMixin_incompatible_with_ServerListMixin():
    """Try (and fail) to use the ServerDictMixin and ServerListMixin together."""

    class ImpossibleObject(ServerAddressableObject, ServerDictMixin, ServerListMixin):
        _baseurl = None
        pass

    with pytest.raises(TypeError):
        ImpossibleObject(None)
