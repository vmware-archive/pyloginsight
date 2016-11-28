#!/usr/bin/env python

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from pyloginsight import __version__ as pyloginsightversion  # TODO Replace with a static variant?


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
    version=pyloginsightversion,
    url='http://github.com/vmware/pyloginsight/',
    license='Apache Software License 2.0',
    author='Alan Castonguay',
    install_requires=['requests', 'ramlfications', 'six', 'jsonschema'],
    tests_require=["requests_mock", "pytest"],
    description='Log Insight API SDK',
    author_email='acastonguay@vmware.com',
    long_description=open('README.md').read(),
    packages=find_packages(),
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
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
