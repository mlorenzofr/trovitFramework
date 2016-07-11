#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import argparse

try:
    from remote import serverGroup, sshLoginException
    from trovitdb.racktables import racktables
except ImportError as ie:
    print(ie)
    sys.exit(1)


def main():
    hlpDsc = "Send a command to multiple servers"
    optParser = argparse.ArgumentParser(description=hlpDsc)
    optParser.add_argument("-k", "--key", help="pattern in servername",
                           metavar="STRING", required=False, type=str,
                           dest="key", default='')
    optParser.add_argument("-n", "--no-newline", help="don't add a new line"
                           "with the servername in the output",
                           required=False, action='store_false',
                           dest="newline", default=True)
    optParser.add_argument("command", help="command line to execute",
                           metavar="shell command", nargs='*')
    args = optParser.parse_args()
    if len(args.command) == 0:
        optParser.print_help()
        sys.exit(2)
    try:
        sshOps = serverGroup()
        with racktables() as rt:
            rt.connect()
            for server in rt.getServersByName(args.key):
                if args.newline:
                    print('\n\033[1;33m=====> %s <=====\033[0m' % server[1])
                else:
                    print('\033[1;33m%s\033[0m: ' % server[1], end='')
                try:
                    sshOps.sshCmd(server[1], ' '.join(args.command))
                except sshLoginException as sLE:
                    print(sLE)
    except KeyboardInterrupt:
        sys.exit(3)
    return

if __name__ == "__main__":
    main()
