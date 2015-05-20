#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re

try:
    from remote import serverGroup, sshLoginException
    from trovitdb.racktables import racktables, ip2int
except ImportError as ie:
    print(ie)
    sys.exit(1)


def parseIproute(stdout, cmpls):
    iface = ''
    netInfo = dict()
    for line in stdout:
        ifaceInfo = cmpls['iface'].search(line)
        ipInfo = cmpls['ip'].search(line)
        if ifaceInfo is not None:
            iface = ifaceInfo.group('iface')
            netInfo[iface] = dict()
            netInfo[iface] = list()
        if ipInfo is not None:
            netInfo[iface].append(ipInfo.group('ip'))
    return netInfo


def cleanIfaces(ifaces):
    ignoredIfaces = ['lo', 'kvm']
    cleaned = ifaces.copy()
    for iface in ifaces:
        if iface in ignoredIfaces:
            del cleaned[iface]
    return cleaned


def main():
    with racktables() as rt:
        rt.connect()
        sshOps = serverGroup()
        ptrns = dict()
        ptrns['iface'] = re.compile('^[0-9]+: (?P<iface>[^:@]+)')
        ptrns['ip'] = re.compile('inet (?P<ip>[0-9\.\/]+) brd')
        try:
            for server in rt.getActiveServers():
                # server: (id,name,type)
                try:
                    ipOutput = sshOps.sshCmd(server[1], "ip a l ",
                                             sync=True)[0]
                except sshLoginException as sLE:
                    print(sLE)
                else:
                    print('* %s' % server[1])
                    realInfo = cleanIfaces(parseIproute(ipOutput, ptrns))
                    dbIps = cleanIfaces(rt.getServerIPs(server[0]))
                    for i in realInfo.keys():
                        if i not in dbIps and len(realInfo[i]) > 0:
                            print("\t%s:%s is not registered [%s]"
                                  % (server[1], i, ','.join(realInfo[i])))
                            dotIp = realInfo[i][0].split("/")[0]
                            ipDbInfo = rt.getIpInfo(dotIp)
                            if len(ipDbInfo) == 0:
                                print("\tAllocate %s (%s) in %s"
                                      % (dotIp, i, server[1]))
                                rt.allocateIp(dotIp, server[0], i)
                            else:
                                for record in ipDbInfo:
                                    print("\t!! IP address %s is registered "
                                          "at %s:%s" %
                                          (dotIp, record[1], record[2]))
                        else:
                            for cidr in realInfo[i]:
                                ip = cidr.split("/")[0]
                                net = int(cidr.split("/")[1])
                                if ip not in dbIps[i] \
                                   and net != 32 \
                                   and not rt.isAllocatedIp(ip):
                                    print("\tAllocate %s (%s) in %s"
                                          % (ip, i, server[1]))
                                    rt.allocateIp(ip, server[0], i)
        except KeyboardInterrupt:
            sys.exit(2)
    return

if __name__ == "__main__":
    main()
