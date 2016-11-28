#!/usr/bin/env python

from setuptools import setup, find_packages
from pyloginsight import __version__ as pyloginsightversion


requires = ['requests', 'ramlfications', 'six', 'jsonschema']

testrequires = requires + ["requests_mock"]

setup(
    name='pyloginsight',
    version=pyloginsightversion,
    url='http://github.com/vmware/pyloginsight/',
    license='Apache Software License 2.0',
    author='Alan Castonguay',
    install_requires=requires,
    tests_require=testrequires,
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
    }
)
