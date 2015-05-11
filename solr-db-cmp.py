#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser
import solrXml

try:
    from trovitdb.racktables import racktables
    from trovitdb.gbl import trovitGlobal
except ImportError as ie:
    print(ie)
    sys.exit(1)


def main():
    solrParser = solrXml.solrXmlParser()
    with trovitGlobal() as tg:
        tg.connect()
        servers = tg.getAllCores(dKey='server')
        for server in servers.keys():
            realCores = solrParser.getCores(solrParser.getXml(server))
            for rCore in realCores:
                if rCore not in servers[server]:
                    print "%s in %s but not in DB" % (rCore, server)
                    print "http://%s:8080/trovit_solr/admin/cores?action=UNLOAD&core=%s&deleteIndex=true" % (server, rCore)
            for dbCore in servers[server]:
                if dbCore not in realCores:
                    print "%s enabled in DB but not in %s" % (dbCore, server)
    return

if __name__ == "__main__":
    main()
