#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import getcwd, symlink, sep
from os.path import lexists
from sys import exit
import argparse

try:
    from trovitdb.racktables import racktables
except ImportError as ie:
    print(ie)
    exit(1)


def main():
    hlpDsc = "Generate links for fastssh script"
    optParser = argparse.ArgumentParser(description=hlpDsc)
    optParser.add_argument("-f", "--fastssh-script", help="fastssh script"
                           " path", metavar="STRING", required=True,
                           type=str, dest="fastssh")
    optParser.add_argument("-d", "--directory", help="target directory"
                           "for the symlinks", metavar="STRING", type=str,
                           required=False, dest="dir", default=getcwd())
    args = optParser.parse_args()
    try:
        with racktables() as rt:
            rt.connect()
            for server in rt.getActiveServers():
                target = '%s%s%s' % (args.dir, sep, server[1])
                if not lexists(target):
                    symlink(args.fastssh, target)
    except KeyboardInterrupt:
        exit(2)
    return

if __name__ == "__main__":
    main()
