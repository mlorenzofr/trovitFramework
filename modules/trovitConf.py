#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser

CONF_FILE = 'trovit.conf'


class trovitConfError(Exception):
    pass


class trovitConf:

    def __init__(self):
        self.conf = ConfigParser.SafeConfigParser()
        try:
            self.conf.read(CONF_FILE)
        except ConfigParser.Error as CE:
            raise trovitConfError("Error reading configuration file %s"
                                  % CONF_FILE)
            print(CE)
        return

    def getRacktables(self):
        """ Retrieve configuration parameters for RacktablesDb
            Return a list of tuples: [(key, value), ...]
        """
        values = []
        try:
            values = self.conf.items('racktablesDb')
        except ConfigParser.NoSectionError:
            raise trovitConfError("No configuration section for racktablesDb")
        return values

    def getSshRootPasswd(self):
        """ Retrieve root password for remote module
            Return a String with the default root password
        """
        passwd = ''
        try:
            passwd = self.conf.get('ssh', 'password')
        except ConfigParser.NoSectionError:
            raise trovitConfError("No configuration section for SSH")
        return passwd

    def getGlobalDb(self):
        values = []
        try:
            values = self.conf.items('trovit_global')
        except ConfigParser.NoSectionError:
            raise trovitConfError("No configuration section"
                                  " for trovit_global DB")
        return values
