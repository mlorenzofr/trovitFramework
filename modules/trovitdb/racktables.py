#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module is used to manage objects stored in Racktables DB"""

import re
from struct import pack, unpack
from socket import inet_ntoa, inet_aton
from . import trovitdb

_OS = {
    # Jessie
    '8': '50055',
    # Wheezy
    '7': '1709',
    # Squeeze
    '6': '1395',
    # Lenny
    '5': '954'
}


class racktables(trovitdb):
    _confSection = 'racktables'
    _ipTypeSet = ['regular', 'shared', 'virtual']

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
            if not self.hasTag(server[0], ['free', 'retired',
                                           'to be retired']) \
               and self.isRunning(server[0]) \
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

    def getAwsInstances(self):
        """
        Return the instances registered into the Racktables dictionary
        Return: dict{str(instance-type): int(id)}
        """
        instances = {}
        regInstances = self.query("select dict_key, dict_value \
                                   from Dictionary \
                                   where chapter_id = 10001;")
        for instEntry in regInstances:
            instances[instEntry[1]] = instEntry[0]
        return instances

    def getPhysicalServers(self):
        """
        Return a server list just with physical machines (no VM's)
        Return: list[(id,name,type), ...]
        """
        phyServers = []
        phyServers = self.query("select id,name,objtype_id from Object \
                                 where objtype_id = 4;")
        return phyServers

    def getServerAttribute(self, serverId, attrId):
        """
        Retrieve the attribute matching with serverId & attrId given
        Return: str(data)
        """
        data = ''
        attr = self.query("select uint_value from AttributeValue \
                           where object_id = %s \
                             and attr_id = %s" % (serverId, attrId))
        if len(attr) > 0:
            data = attr[0][0]
        return str(data)

    def getServerAttrDict(self, serverId, attrId):
        """
        Take the value from a racktables dictionary and return it
        Return: str(data)
        """
        data = ''
        sql = "select dict_value from Dictionary \
               inner join AttributeMap \
                 on Dictionary.chapter_id = AttributeMap.chapter_id \
               inner join AttributeValue \
                 on (AttributeValue.uint_value = Dictionary.dict_key \
                   and AttributeMap.objtype_id = AttributeValue.object_tid) \
               inner join Object \
                 on Object.id = AttributeValue.object_id \
               where Object.id = %s \
                 and AttributeMap.attr_id = %s;" % (serverId, attrId)
        dictVal = self.query(sql)
        if len(dictVal) > 0:
            data = dictVal[0][0]
        return data

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
        attrOS = self.getServerAttribute(serverId, 4)
        if attrOS != '':
            for attrVal in _OS.keys():
                if _OS[attrVal] == attrOS:
                    data = attrVal
            if data == '':
                data = 'Unknown value'
        return data

    def getServerHwEnd(self, serverId):
        """
        Retrieve the expiration date for the hardware
        Return: int (timestamp date)
        """
        timestamp = self.getServerAttribute(serverId, 22)
        if timestamp == '':
            return 0
        return int(timestamp)

    def getServerModel(self, serverId):
        """
        Return the hardware type (model) for a server given
        Return: str(server hardware model)
        """
        return self.getServerAttrDict(serverId, 2)

    def getServerSupportEnd(self, serverId):
        """
        Get the expiration date for hardware support
        Return: int (timestamp date)
        """
        timestamp = self.getServerAttribute(serverId, 21)
        if timestamp == '':
            return 0
        return int(timestamp)

    def getServiceTag(self, searchVal, useServerId=True):
        """
        Get the machine ServiceTag using ServerID or ServerName
        Return: str (ServiceTag)
        """
        svcTag = ''
        if useServerId:
            whereFilter = 'id'
        else:
            whereFilter = 'name'
        svcTag = self.query("select asset_no from Object \
                             where %s = %s;" %
                            (whereFilter, searchVal))
        return svcTag[0][0]

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

    def isRetired(self, serverId):
        """
        Check if the server is retired or will be soon
        Return: boolean
        """
        srvTags = self.getServerTags(serverId)
        if 'retired' in srvTags \
           or 'to be retired' in srvTags:
            return True
        return False

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

    def getIfaceIPs(self, serverId, ifaceName):
        """
        Get IP addresses allocated to given server/iface
        Keywords:
            @serverId: Server Object ID
            @ifaceName: iface name (example: eth0)
        Return: list[str(ipaddr1), str(ipaddr2), ...]
        """
        ips = []
        data = self.query("select ip from IPv4Allocation \
                           where object_id = %s \
                               and name = '%s';" %
                          (serverId, ifaceName))
        map(lambda x: ips.append(int2ip(x[0])), data)
        return ips

    def getServerIPs(self, serverId):
        """
        Get all IP addresses and interfaces for given server
        Keywords:
            @serverId: Server Object ID
        Return: dict{str(if-name): list[str(ipaddr1), ...]}
        """
        interfaces = dict()
        data = self.query("select name, ip from IPv4Allocation \
                           where object_id = %s;" % serverId)
        for iface, ip in data:
            if iface in interfaces:
                interfaces[iface].append(int2ip(ip))
            else:
                interfaces[iface] = [int2ip(ip)]
        return interfaces

    def getServerInterfaces(self, serverId):
        """
        Get the network interfaces and its MAC address for a server
        Keywords:
            @serverId: Server Object ID
        Return: dict{str(iface-name): str(MAC-addr)}
        """
        interfaces = dict()
        data = self.query("select name, l2address from Port \
                           where object_id = %s;" % serverId)
        for iface, mac in data:
            interfaces[iface] = mac
        return interfaces

    def getIpInfo(self, ip):
        """
        Retrieve IP related info (serverId, server, port) from racktables
        database.
        Keywords:
            @ip: (str) IP in human readable format
        Return: list[tuple(int(serverId), str(serverName), str(port)), ...]
        """
        data = self.query("select Object.id, Object.name, IPv4Allocation.name \
                           from Object \
                           left join IPv4Allocation \
                           on Object.id = IPv4Allocation.object_id \
                           where IPv4Allocation.ip = %s;" % ip2int(ip))
        return data

    def isAllocatedIp(self, ip, ipType='all'):
        """
        Check if the given IP address is into IPv4Allocation table
        Keywords:
            @ip: (str) IP address in human readable format
            @ipType: (str) racktables IP type [regular, shared, virtual, all]
        Return: boolean
        """
        if ipType == 'all':
            queryType = ('\'%s\'' % '\',\''.join(self._ipTypeSet))
        elif ipType in self._ipTypeSet:
            queryType = ipType
        else:
            raise trovitdb.trovitdbException("Wrong IP type %s. Choose: "
                                             "[all, %s]"
                                             % (ipType, queryType))
        data = self.query("select * from IPv4Allocation \
                           where ip = %s \
                             and type in (%s);"
                          % (ip2int(ip), queryType))
        if len(data) > 0:
            return True
        return False

    def allocateIp(self, ip, serverId, port, ipType='regular'):
        """
        Allocate an IPv4 address
        Keywords:
            @ip: (str) IP address in human readable format
            @serverId: (int) Server Object ID
            @port: (str) Port name
            @ipType: (str) One of (regular, shared, virtual)
        Return:
            null
        """
        if ipType not in self._ipTypeSet:
            raise trovitdb.trovitdbException("Wrong IP type %s." % ipType)
        self.query("insert into IPv4Allocation \
                    (object_id, ip, name, type) \
                    values (%s, %s, '%s', '%s');"
                   % (serverId, ip2int(ip), port, ipType),
                   'insert')
        return

    def updateIp(self, ip, serverId, port, ipType='regular'):
        """
        Update an IPv4 address data
        Keywords:
            @ip: (str) IP address in human readable format
            @serverId: (int) Server Object ID
            @port: (str) Port name
            @ipType: (str) One of (regular, shared, virtual)
        Return:
            null
        """
        if ipType not in self._ipTypeSet:
            raise trovitdb.trovitdbException("Wrong IP type %s." % ipType)
        self.query("update IPv4Allocation \
                    set object_id = %s, \
                        name = '%s', \
                        type = '%s' \
                    where ip = %s;"
                   % (serverId, port, ipType, ip2int(ip)),
                   'update')
        return


def ip2int(addr):
    """
    Transform an human readable IP address to integer
    """
    return unpack("!I", inet_aton(addr))[0]


def int2ip(addr):
    """
    Transform an integer to a human readable IP address
    """
    return inet_ntoa(pack("!I", addr))
