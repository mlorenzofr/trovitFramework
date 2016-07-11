#!/usr/bin/env python
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


class remoteServer:
    def __init__(self, hostname, password):
        self._sckBS = 4096
        self._sshCli = paramiko.SSHClient()
        self._sshCli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._sshCred = {'username': getpwuid(getuid())[0],
                         'hostname': hostname,
                         'allow_agent': True,
                         'timeout': 60,
                         'password': password}
        self._catchExcpts = ['sshLoginException']
        self._sshLogin()
        return

    def __enter__(self):
        return self

    def __exit__(self, xcpType, xcpValue, traceback):
        if self._sshCli is not None:
            self._sshCli.close()
        if xcpType is not None:
            if xcpType.__name__ in self._catchExcpts:
                print("[%s]: %s" % (xcpType.__name__, xcpValue))
                return True
        return

    def _sshConnection(self):
        """
        Establish the connection with the remote server and handle possible
        errors.

        Keywords:
          None
        Return:
          None
        """
        try:
            self._sshCli.connect(**self._sshCred)
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

    def _sshLogin(self):
        """
        Create a new connection (login included) to a remote server.

        Keywords:
          None
        Return:
          None
        """
        errorMsg = '[SSH]: <%s>' % self._sshCred['hostname']
        sshUsers = ['root']
        if self._sshCred['hostname'][:7] == 'vpc-nat':
            sshUsers.insert(0, 'admin')
        try:
            while not self._sshConnection():
                self._sshCred['username'] = sshUsers.pop()
        except sshLoginException as sLE:
            raise sshLoginException("%s %s" % (errorMsg, sLE.message))
        except IndexError:
            raise sshLoginException("%s Auth Error" % errorMsg)
        return

    def _parseResponse(self, channel, srcType='out'):
        """
        Print in fancy mode the stdout or stderr streams of a SSH Channel.

        Keywords:
          @channel (SSHChannel): Paramiko SSH Channel to work in
          @srcType (str): Type of message [ out | err ]
        Return:
          None
        """
        data = ''
        color = 2 if srcType == 'out' else 1
        decorator = "\033[1;3%sm*\033[0m" % color
        while len(data) == 0 or data[-1] != '\n':
            if srcType == 'out':
                data += channel.recv(self._sckBS)
            elif srcType == 'err':
                data += channel.recv_stderr(self._sckBS)
        output = "%s %s" % (decorator, sub('\n', '\n%s ' % decorator,
                                           data[:-1]))
        print(output)
        return

    def sshStreamCmd(self, cmd):
        """
        Execute one command on the remote server and prints the output (and
        error).

        Keywords:
          @cmd (str): command to execute
        Return:
          None
        """
        sshTrans = self._sshCli.get_transport()
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
        return

    def sshSyncCmd(self, cmd):
        """
        Execute one command on the remote server and return a tuple with stdout
        and stderr lines.

        Keywords:
          @cmd (str): command to execute
        Return:
          tuple(list[stdout], list[stderr])
        """
        output, error = '', ''
        stdin, stdout, stderr = self._sshCli.exec_command(cmd)
        output = stdout.readlines()
        error = stderr.readlines()
        return (output, error)


class serverGroup:
    def __init__(self):
        config = trovitconf()
        try:
            self.__password = config.getSshRootPasswd()
        except trovitconfError:
            self.__password = getpass(("Enter root passwd "
                                       "(for error with publickey auth): "))
        return

    def sshCmd(self, hostname, cmd, sync=False):
        with remoteServer(hostname, self.__password) as server:
            if sync:
                return server.sshSyncCmd(cmd)
            else:
                server.sshStreamCmd(cmd)
        return
