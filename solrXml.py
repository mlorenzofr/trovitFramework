#!/usr/bin/python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import urllib2


class solrXmlParser:

    def __init__(self):
        return

    def getCores(self, xmlData):
        """ Return a list with all core names inside a xmlData list """
        cores = list()
        root = ET.fromstringlist(xmlData)
        # for each core in result (getting names)
        map(lambda x: cores.append(x.text),
            root.findall(".//*[@name='name']"))
        return cores

    def getSizes(self, xmlData):
        """ Return a dict with all cores and its size (bytes) """
        dictCores = dict()
        dictCores['total'] = 0
        root = ET.fromstringlist(xmlData)
        # for each core in result (getting names)
        for core in self.getCores(xmlData):
            # Search core root object
            coreRoot = root.findall((".//*[@name='sizeInBytes']/"
                                     "..[@name='index']/"
                                     "..[@name='%s']" % core))
            # Search sizeInBytes in the core object
            findSize = coreRoot[0].findall(".//*[@name='sizeInBytes']")
            # format to int
            coresize = int(findSize[0].text)
            dictCores[core] = coresize
            dictCores['total'] += coresize
        return dictCores

    def getXml(self, srvname):
        """ Retrieve XML information through an HTTP request """
        url = ("http://%s:8080/"
               "trovit_solr/admin/cores?action=STATUS" % srvname)
        try:
            httpReq = urllib2.urlopen(url)
        except urllib2.HTTPError as h:
            print("Error getting STATUS from %s (%s: %s)" %
                  (srvname, h.code, h.reason))
        else:
            xmlInfo = httpReq.readlines()
        finally:
            httpReq.close()
        return xmlInfo
