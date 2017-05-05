#!/usr/bin/env python

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# If a version number has been written to file inside the package, use it as the package version.
# Read the file directly instead of importing the package to avoid taking a dependency on the
# package before it's installed.
try:
    version_namespace = {}
    with open('pyloginsight/__version__.py') as f:
        exec(f.read(), version_namespace)
    packageversion = version_namespace['version']
except (EnvironmentError, KeyError):
    packageversion = "0.dev0"


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]
    description = "Run tests in the current environment"

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.args = []

    def run(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest

        try:
            args = shlex.split(self.args)
        except AttributeError:
            args = []
        errno = pytest.main(args)
        sys.exit(errno)


class ToxTest(TestCommand):
    user_options = [('tox-args=', "t", "Arguments to pass to pytest")]
    description = "Run tests in all configured tox environments"

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.args = []

    def run(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        from tox.__main__ import main

        try:
            args = shlex.split(self.args)
        except AttributeError:
            args = []
        errno = main(args)
        sys.exit(errno)


setup(
    name='pyloginsight',
    version=packageversion,
    url='http://github.com/vmware/pyloginsight/',
    license='Apache Software License 2.0',
    author='Alan Castonguay',
    install_requires=['requests', 'ramlfications', 'six', 'jsonschema==2.3.0', 'python-jsonschema-objects'],
    tests_require=["requests_mock", "pytest", "pytest-catchlog", "pytest-flakes", "pytest-pep8"],
    description='VMware vRealize Log Insight Client',
    author_email='acastonguay@vmware.com',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'console_scripts': [
            'li = pyloginsight.cli.__main__:main'
        ]
    },
    cmdclass={'test': PyTest, 'tox': ToxTest}
)
