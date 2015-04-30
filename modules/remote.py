#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import socket
from trovitconf import trovitconf, trovitconfError
from pwd import getpwuid
from os import getuid
from getpass import getpass
from select import select
from re import sub

try:
    import paramiko
except ImportError as ie:
    print(ie)
    raise


class sshLoginException(Exception):
    pass


class serverGroup:
    def __init__(self):
        self.sckBS = 4096
        config = trovitconf()
        try:
            self.__password__ = config.getSshRootPasswd()
        except trovitconfError:
            self.__password__ = getpass(("Enter root passwd "
                                         "(for error with publickey auth): "))
        return

    def sshLogin(self, cnx, **sshOpts):
        try:
            cnx.connect(**sshOpts)
        except paramiko.AuthenticationException:
            return False
        except paramiko.SSHException as se:
            raise sshLoginException("%s" % se)
        except socket.gaierror as sckE:
            raise sshLoginException("Socket GetAddrInfo Error (%s)" % sckE)
        except socket.timeout:
            raise sshLoginException("Socket Timeout Error")
        except socket.error as sckE:
            raise sshLoginException("Socket Error (%s)" % sckE)
        return True

    def sshCmd(self, hostname, cmd):
        sshArgs = {'username': getpwuid(getuid())[0],
                   'hostname': hostname,
                   'allow_agent': True,
                   'timeout': 60,
                   'password': self.__password__}
        errorMsg = '[SSH]: <%s>' % sshArgs['hostname']
        sshCnx = paramiko.SSHClient()
        sshCnx.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshUsers = ['root']
        if sshArgs['hostname'][:7] == 'vpc-nat':
            sshUsers.insert(0, 'admin')
        try:
            while not self.sshLogin(sshCnx, **sshArgs):
                sshArgs['username'] = sshUsers.pop()
        except sshLoginException as sLE:
            raise sshLoginException("%s %s" % (errorMsg, sLE.message))
        except IndexError:
            raise sshLoginException("%s Auth Error" % errorMsg)
        sshTrans = sshCnx.get_transport()
        sshChan = sshTrans.open_session()
        sshChan.exec_command(cmd)
        while not sshChan.exit_status_ready():
            rObj, wObj, xObj = select([sshChan], [], [], 1.0)
            if len(rObj) > 0:
                if sshChan.recv_ready():
                    self._parseResponse(sshChan)
                if sshChan.recv_stderr_ready():
                    self._parseResponse(sshChan, srcType='err')
        sshChan.close()
        sshCnx.close()
        return

    def _parseResponse(self, channel, srcType='out'):
        data = ''
        color = 2 if srcType == 'out' else 1
        decorator = "\033[1;3%sm*\033[0m" % color
        while len(data) == 0 or data[-1] != '\n':
            if srcType == 'out':
                data += channel.recv(self.sckBS)
            elif srcType == 'err':
                data += channel.recv_stderr(self.sckBS)
        output = "%s %s" % (decorator, sub('\n', '\n%s ' % decorator,
                                           data[:-1]))
        print(output)
        return
