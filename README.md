# pyloginsight [![build status](https://api.travis-ci.org/vmware/pyloginsight.svg?branch=master)](https://travis-ci.org/vmware/pyloginsight)


Python API client bindings for [VMware vRealize Log Insight](https://vmw-loginsight.github.io/).

This is in a very early state right now.

# Running tests

None of the tests require a connection to a live server. They're either unittests or using mocks.

You will need a virtualenv with `tox` installed and a checkout of this repository. Running `tox` will install test-centric dependencies (`pytest`, `requests_mock`) in `tox`'s own virtualenvs (`.tox/py{27,35}/`), along with the pyloginsight package and its requirements, then run tests and style checks (`pytest`, `pep8`, `pyflakes`).

```
virtualenv pyloginsight-virtualenv
source pyloginsight-virtualenv/bin/activate
pip install tox
git clone https://github.com/vmware/pyloginsight.git
cd pyloginsight
tox
```
