#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Base module for managing connections with different MySQL backends inside
the Trovit Platform
"""

__all__ = ['global', 'racktables', 'trovitdb']
__version__ = '0.1'


from getpass import getpass
from trovitconf import trovitconf, trovitconfError

try:
    import mysql.connector as mdb
except ImportError as ie:
    print "Error loading mysql-connector module. Is it installed?"
    raise


class trovitdbException(Exception):
    pass


class trovitdb:
    _confSection = ''

    def __init__(self):
        self._cnx = None
        self._errorMsg = '[trovitDB]: '
        self.catchExcpts = ['trovitconfError',
                            'trovitdbException']
        return

    def __enter__(self):
        return self

    def __exit__(self, xcpType, xcpValue, traceback):
        if self._cnx is not None:
            self._cnx.close()
        if xcpType is not None:
            if xcpType.__name__ in self.catchExcpts:
                print("[%s]: %s" % (xcpType.__name__, xcpValue))
                return True
        return

    def connect(self):
        """ Do the connection to the MySQL database
        Return: None
        """
        try:
            self._cnx = mdb.connect(**self.getConfig())
        except mdb.Error as err:
            raise trovitdbException("[mysql-connector (#%s)] %s"
                                    % (err.errno, err.msg))
        return

    def getConfig(self):
        """ Retrieve the configuration values for the DB connection from the
        configuration file
        Return: dict{str(key): str(value), ...}
        """
        DB = {}
        try:
            config = trovitconf()
            DB.update(config.getConfig(self._confSection))
        except trovitconfError as confError:
            raise trovitconfError(confError.message)
        if DB['password'] == '':
            DB['password'] = getpass('Enter MySQL password for %s@%s: ' %
                                     (DB['user'], DB['host']))
        return DB

    def query(self, sqlStmt, op='select'):
        """ Send a sql statement to the MySQL database
        Return: list[tuple(field1, field2, ...), ...]
        """
        data = ''
        try:
            cursor = self._cnx.cursor()
            cursor.execute(sqlStmt)
            if op == 'select':
                # data = map(lambda x: str(x[0]), cursor.fetchall())
                data = cursor.fetchall()
            self._cnx.commit()
            cursor.close()
        except mdb.Error as err:
            print('%s Error retrieving data from db' % self._errorMsg)
            print('%s %s' % (self._errorMsg, err))
        return data
