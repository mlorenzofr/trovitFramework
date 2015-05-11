#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module is used to manage objects stored in Racktables DB"""

import re
from . import trovitdb

_OS = {
    # Wheezy
    '7': 1709,
    # Squeeze
    '6': 1395,
    # Lenny
    '5': 954
}


class racktables(trovitdb):
    _confSection = 'racktables'

    def getServersByName(self, srvName):
        """
        Return a server list matching srvName string
        Return: list[(id,name,type), ...]
        """
        srvRegex = re.compile(srvName)
        srvList = []
        for server in self.getActiveServers():
            if srvRegex.match(server[1]) is not None:
                srvList.append(server)
        return srvList

    def getActiveServers(self):
        """
        Return a server list avoiding free, retired or power off servers
        Return: list[(id,name,type), ...]
        """
        activeServers = []
        for server in self.getAllServers():
            if not self.hasTag(server[0], ['free', 'retired']) \
               and self.isRunning(server[0])
               and server[1] is not None:
                activeServers.append(server)
        return activeServers

    def getAllServers(self):
        """
        Return a complete list with all servers in Racktables DB
        Return: list[(id,name,type), ...]
        """
        machines = self.query("select id,name,objtype_id from Object \
                               where objtype_id in (4,1504);")
        return machines

    def getServerTags(self, serverId):
        """
        Return a list with all tags associated with a server
        Return: list[str(tag), ...]
        """
        tags = []
        data = self.query("select entity_id,tag from TagStorage \
                           left join TagTree \
                           on TagStorage.tag_id = TagTree.id \
                           where entity_id = %s;" % serverId)
        map(lambda x: tags.append(x[1]), data)
        return tags

    def hasTag(self, serverId, tags):
        """
        Check if the server has the tag requested in tags parameter
        Input: int(serverId), <str(tag)|list(str(tag), ...)>
        Return: boolean
        """
        targetTags = []
        if isinstance(tags, list):
            targetTags = tags
        else:
            targetTags.append(tags)
        serverTags = self.getServerTags(serverId)
        for tag in targetTags:
            if tag in serverTags:
                return True
        return False

    def getServerVersion(self, serverId):
        """
        Retrieve OS version from racktables and validate it
        Return: int (major version of Debian OS)
        """
        data = ''
        attrOS = self.query("select uint_value from AttributeValue \
                             where object_id = %s \
                               and attr_id = 4;" % serverId)
        if len(attrOS) > 0:
            for attrVal in _OS.keys():
                if _OS[attrVal] == attrOS[0][0]:
                    data = attrVal
            if data == '':
                data = 'Unknown value'
        return data

    def insertVersion(self, serverId, serverType, osversion):
        """
        Insert the OS version attribute into racktables DB
        Return: None
        """
        if osversion in _OS:
            self.query("insert into AttributeValue \
                        values (%s,%s,4,NULL,%s,NULL);" %
                       (serverId, serverType, _OS[osversion]),
                       'insert')
        else:
            print("Unknown OS version: \'%s\'" % osversion)
        return

    def isRunning(self, serverId):
        """
        Check if the specified serverID has attribute running and it's true
        Return: boolean
        """
        check = self.query("select uint_value from AttributeValue \
                            where attr_id = 10010 \
                              and object_id = %s;" % serverId)
        if len(check) > 0:
            if check[0][0] == 50053:
                return False
        return True

    def updateVersion(self, serverId, osversion):
        """
        Update OS version attribute into racktables DB
        Return: None
        """
        if osversion in _OS:
            self.query("update AttributeValue \
                        set uint_value=%s \
                        where object_id = %s \
                            and attr_id = 4;" %
                       (_OS[osversion], serverId),
                       'update')
        else:
            print("%s Wrong OS version \'%s\' for ID %s" %
                  (self._errorMsg, osversion, serverId))
        return
