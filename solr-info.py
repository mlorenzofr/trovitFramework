#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser

try:
    from trovitdb.racktables import racktables
    import solrXml
except ImportError as ie:
    print(ie)
    sys.exit(1)


def humanReadable(number):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(number)
    counter = 0
    while size > 1024:
        size = size / 1024
        counter += 1
    return "%0.2f %s" % (size, units[counter])


def main():
    cores = dict()
    solrTypes = ['search', 'keywords', 'premium', 'solr-extra']
    optParser = ArgumentParser()
    optParser.add_argument('-t', '--type',
                           help='Index type: [%s]' % '|'.join(solrTypes),
                           metavar='TYPE', required=False, type=str,
                           choices=solrTypes, default='search',
                           dest='solrType')
    optParser.add_argument('-c', '--cores',
                           help='Show core information',
                           action='store_true', required=False,
                           default=False, dest='showCores')
    optParser.add_argument('-s', '--servers',
                           help='Show servers information',
                           action='store_true', required=False,
                           default=True, dest='showServers')
    try:
        args = optParser.parse_args()
    except IOError as ioe:
        print("%s: %s" % (ioe.filename, ioe.strerror))
        sys.exit(1)
    with racktables() as rt:
        rt.connect()
        solrParser = solrXml.solrXmlParser()
        servers = []
        map(lambda x: servers.append(x[1]), rt.getServersByName(args.solrType))
        for server in servers:
            results = solrParser.getSizes(solrParser.getXml(server))
            for core in results.keys():
                if core == 'total':
                    cores[server] = results[core]
                else:
                    if core not in cores:
                        cores[core] = results[core]
                    else:
                        if cores[core] != results[core]:
                            # print "%s has different size !!!" % core
                            cores[core] = results[core]
        for key in cores.keys():
            printInfo = False
            if args.showServers and key in servers:
                printInfo = True
            if args.showCores and key not in servers:
                printInfo = True
            if printInfo:
                print "%s: %d (%s)" % (key, int(cores[key]),
                                       humanReadable(int(cores[key])))
    return

if __name__ == "__main__":
    main()
