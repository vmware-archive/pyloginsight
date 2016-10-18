#!/usr/bin/env python

from setuptools import setup, find_packages
from pyloginsight import __version__ as pyloginsightversion

with open('requirements.txt') as rfh:
    install_requires = rfh.read().splitlines()

setup(
    name='pyloginsight',
    version=pyloginsightversion,
    url='http://github.com/vmware/pyloginsight/',
    license='Apache Software License',
    author='Alan Castonguay',
    # install_requires=install_requires,
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
)
