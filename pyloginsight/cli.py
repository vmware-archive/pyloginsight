#!/usr/bin/env python

import argparse
import logging
import sys
from Connection import Connection


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    parser = argparse.ArgumentParser(description="Placeholder CLI tool. TODO")
    parser.add_argument("--server")
    args = parser.parse_args()

    c = Connection(args.server, verify=False)
    a = c.version()

    print( c.is_bootstrapped() )
    #d = Deployment(c, username="foo")
