#!/usr/bin/python
# -*- coding: utf-8 -*-

__module_name__ = 'rackTablesDB'
__module_description__ = 'Conector to work with Racktables DB'
__module_version__ = '0.1'
__module_author__ = 'Manuel Lorenzo Frieiro'

from getpass import getpass
import re
import trovitConf

try:
    import mysql.connector as mdb
except ImportError as ie:
    print "Error loading mysql-connector module. Is it installed?"
    raise


OS = {
    # Wheezy
    '7': 1709,
    # Squeeze
    '6': 1395,
    # Lenny
    '5': 954
}


class rackTablesException(Exception):
    pass


class rackTablesDB:
    def __init__(self):
        try:
            config = trovitConf.trovitConf()
            self.DB = {}
            self.DB.update(config.getRacktables())
        except trovitConf.trovitConfError:
            raise rackTablesException(trovitConf.trovitConfError.message)
        self.__cnx = False
        self.__errorMsg = '[DB]: '
        if self.DB['password'] == '':
            self.DB['password'] = getpass('Enter MySQL password for %s@%s: ' %
                                          (self.DB['user'], self.DB['host']))
        self.connect(**self.DB)
        return

    def __enter__(self):
        return self

    def __exit__(self):
        self.__cnx.close()
        return

    def connect(self, **options):
        """
        Do the connection to the Racktables DB.
        The connection is stored in self.__cnx variable
        """
        try:
            self.__cnx = mdb.connect(**options)
        except mdb.Error as err:
            if err.errno == mdb.errorcode.ER_ACCESS_DENIED_ERROR:
                raise rackTablesException("Wrong user or password")
            elif err.errno == mdb.errorcode.ER_BAD_DB_ERROR:
                raise rackTablesException("Database does not exists")
            else:
                print(err)
                raise
        return True

    def destroy(self):
        self.__exit__()
        return

    def query(self, sqlStmt, op='select'):
        """
        Send a sql statement to the Racktables DB.
        Return: list[tuple(field1, field2, ...), ...]
        """
        data = ''
        try:
            cursor = self.__cnx.cursor()
            cursor.execute(sqlStmt)
            if op == 'select':
                # data = map(lambda x: str(x[0]), cursor.fetchall())
                data = cursor.fetchall()
            self.__cnx.commit()
            cursor.close()
        except mdb.Error as err:
            print('%s Error retrieving data from db' % self.__errorMsg)
            print('%s %s' % (self.__errorMsg, err))
        return data

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
               and self.isRunning(server[0]):
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
        tags = []
        data = self.query("select entity_id,tag from TagStorage \
                           left join TagTree \
                           on TagStorage.tag_id = TagTree.id \
                           where entity_id = %s;" % serverId)
        map(lambda x: tags.append(x[1]), data)
        return tags

    def hasTag(self, serverId, tags):
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
        data = ''
        attrOS = self.query("select uint_value from AttributeValue \
                             where object_id = %s \
                               and attr_id = 4;" % serverId)
        if len(attrOS) > 0:
            for attrVal in OS.keys():
                if OS[attrVal] == attrOS[0][0]:
                    data = attrVal
            if data == '':
                data = 'Unknown value'
        return data

    def insertVersion(self, serverId, serverType, osversion):
        if osversion in OS:
            self.query("insert into AttributeValue \
                        values (%s,%s,4,NULL,%s,NULL);" %
                       (serverId, serverType, OS[osversion]),
                       'insert')
        else:
            print("Unknown OS version: \'%s\'" % osversion)
        return

    def isRunning(self, serverId):
        check = self.query("select uint_value from AttributeValue \
                            where attr_id = 10010 \
                              and object_id = %s;" % serverId)
        if len(check) > 0:
            if check[0][0] == 50053:
                return False
        return True

    def updateVersion(self, serverId, osversion):
        if osversion in OS:
            self.query("update AttributeValue \
                        set uint_value=%s \
                        where object_id = %s \
                            and attr_id = 4;" %
                       (OS[osversion], serverId),
                       'update')
        else:
            print("%s Wrong OS version \'%s\' for ID %s" %
                  (self.__errorMsg, osversion, serverId))
        return
