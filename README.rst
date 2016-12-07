.. image:: https://api.travis-ci.org/vmware/pyloginsight.svg?branch=master
    :target: https://travis-ci.org/vmware/pyloginsight
    :alt: Build Status

Python API client bindings for `VMware vRealize Log Insight <https://www.vmware.com/go/loginsight/docs>`_'s `API <https://www.vmware.com/go/loginsight/api>`_.

Getting Started
===============

The ``master`` branch is code that's in development right now. To install in develop mode, create a `virtual environment <https://virtualenv.pypa.io/en/stable/>`_ and clone+install with ``pip``::

    virtualenv pyloginsight
    cd pyloginsight
    source bin/activate
    pip install -e git+https://github.com/vmware/pyloginsight.git#egg=pyloginsight
    cd src/pyloginsight/


Running tests
==============

None of the tests require a connection to a live server. They're either unittests or using ``requests_mock``.

You will need `tox <https://tox.readthedocs.io/>`_ installed and a checkout of this repository. Running ``tox`` will install test-centric dependencies (``pytest``, ``requests_mock``) in ``tox``'s own virtualenvs (``.tox/py{27,35}/``), along with the pyloginsight package and its requirements, then run tests and style checks (``pytest``, ``pep8``, ``pyflakes``).::

    virtualenv pyloginsight
    cd pyloginsight
    source bin/activate
    pip install -e git+https://github.com/vmware/pyloginsight.git#egg=pyloginsight
    cd src/pyloginsight/
    pip install tox
    tox

