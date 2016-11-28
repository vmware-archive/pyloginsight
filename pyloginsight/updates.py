#!/usr/bin/env python

"""
Determine whether upgrades are available -from- a given
version of Log Insight.

Makes an outbound HTTPS request to VMware Upgrade Path API.
This module is not imported by pyloginsight.
"""

from __future__ import unicode_literals, print_function, absolute_import, division, generators, nested_scopes

from distutils.version import StrictVersion
import requests

APIROOT = "https://simservice.vmware.com/api/v2"


def paths(productnumber=88):
    """Retrieve upgrade paths, produce generator to deal with pagination in the future"""
    r = requests.get("%s/upgrade/product/%d" % (APIROOT, productnumber))
    for _ in r.json()['upgradePaths']:
        yield _


def highest(pathlist=None):
    """
    Given a list of upgrade paths, produce a distutils.version.StrictVersion
    referencing the highest version which anyone can upgrade to. Does not
    consider the starting version.
    """
    if not pathlist:
        pathlist = paths()

    highestversion = StrictVersion("0.0.0")
    for path in pathlist:
        highestversion = max([highestversion, StrictVersion(path['toRelease']['version'])])
    return highestversion


def pathfrom(fromversion, pathlist):
    """
    Generator producing itererable set of versions which can be upgraded to, starting
    at the provided fromversion and following paths provided in the pathlist.
    Could produce an empty list, esp if there are no upgrades from fromversion.
    """
    if not pathlist:
        pathlist = paths()
    if type(fromversion) != StrictVersion:
        fromversion = StrictVersion(fromversion)
    for path in pathlist:
        if fromversion == StrictVersion(path['fromRelease']['version']):
            yield StrictVersion(path['toRelease']['version'])


def available(fromversion, pathlist=None):
    """"
    For a given fromversion, produce either a distutils.version.StrictVersion
    containing the highest version a direct upgrade to can be performed
    or a ValueError exception
    """

    if not pathlist:
        pathlist = paths()
    toversions = list(pathfrom(fromversion, pathlist))
    if not toversions:
        raise ValueError("Upgrade from version %s not found" % fromversion)
    return max(toversions)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for fromversion in sys.argv[1:]:
            print("Can upgrade from {0} to {1}".format(fromversion, available(fromversion)))
    else:
        print("Usage: python -m pyloginsight.updates 3.6")
        print(__doc__)
