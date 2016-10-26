import sys

from ..Connection import Connection
import argparse
import logging


def main():

    print('in main')
    args = sys.argv[1:]
    print('count of args :: {}'.format(len(args)))
    for arg in args:
        print('passed argument :: {}'.format(arg))

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    parser = argparse.ArgumentParser(description="Placeholder CLI tool. TODO")
    parser.add_argument("--server")
    # TODO: When we accept credentials, support https://docs.python.org/3.6/library/netrc.html
    args = parser.parse_args()

    from .. import query

    c = query.Constraint()

    print(c)
    print(str(c))
    print(repr(c))
    conn = Connection(args.server, verify=False)

    print(conn.version())


if __name__ == '__main__':
    main()
