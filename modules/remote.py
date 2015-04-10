#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
from trovitconf import trovitconf, trovitconfError
from pwd import getpwuid
from os import getuid
from getpass import getpass

try:
    import paramiko
except ImportError as ie:
    print(ie)
    raise


class sshLoginException(Exception):
    pass


class serverGroup:
    def __init__(self):
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
        output = ''
        error = ''
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
        stdin, stdout, stderr = sshCnx.exec_command(cmd)
        output = stdout.readlines()
        error = stderr.readlines()
        sshCnx.close()
        return (output, error)
