#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser

from sys import argv
from os.path import dirname, realpath
from os import sep
CONF_FILE = '%s%strovit.conf' % (dirname(realpath(argv[0])), sep)


class trovitconfError(Exception):
    pass


class trovitconf:
    def __init__(self, cnf_file=CONF_FILE):
        self.conf = ConfigParser.SafeConfigParser()
        try:
            self.conf.read(cnf_file)
        except ConfigParser.Error:
            raise trovitconfError("Error reading configuration file %s"
                                  % cnf_file)
        return

    def getConfig(self, section):
        """ Retrieve configuration parameters for a MySQL DB using the section
        String obtained as parameter
        Return a list of tuples: [(key, value), ...]
        """
        values = []
        try:
            values = self.conf.items(section)
        except ConfigParser.NoSectionError:
            raise trovitconfError("No configuration section for %s"
                                  % section)
        return values

    def getSshRootPasswd(self):
        """ Retrieve root password for remote module
            Return a String with the default root password
        """
        passwd = ''
        try:
            passwd = self.conf.get('ssh', 'password')
        except ConfigParser.NoSectionError:
            raise trovitconfError("No configuration section for SSH")
        return passwd
