#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import argparse

try:
    import remote
    import racktablesDb
except ImportError as ie:
    print(ie)
    sys.exit(1)


def main():
    hlpDsc = "Send a command to multiple servers"
    optParser = argparse.ArgumentParser(description=hlpDsc)
    optParser.add_argument("-k", "--key", help="pattern in servername",
                           metavar="STRING", required=False, type=str,
                           dest="key", default='')
    optParser.add_argument("command", help="command line to execute",
                           metavar="shell command", nargs='*')
    args = optParser.parse_args()
    if len(args.command) == 0:
        optParser.print_help()
        sys.exit(2)
    try:
        rt = racktablesDb.rackTablesDB()
        sshOps = remote.serverGroup()
        for server in rt.getServersByName(args.key):
            if not rt.hasTag(server[0], ['free', 'retired']) and \
               rt.isRunning(server[0]):
                print('\n\033[1;33m=====> %s <=====\033[0m' % server[1])
                try:
                    sshReply = sshOps.sshCmd(server[1], ' '.join(args.command))
                    for x, y in zip((0, 1), (2, 1)):
                        map(lambda x: print("\033[1;3%sm*\033[0m %s"
                            % (y, x.strip('\n'))), sshReply[x])
                except remote.sshLoginException as sLE:
                    print(sLE)
    except KeyboardInterrupt:
        sys.exit(3)
    except racktablesDb.rackTablesException as rte:
        print("[RackTables]: %s" % rte)
        sys.exit(4)
    return

if __name__ == "__main__":
    main()
