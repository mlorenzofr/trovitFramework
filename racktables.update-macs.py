#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re

try:
    from remote import serverGroup, sshLoginException
    from trovitdb.racktables import racktables
except ImportError as ie:
    print(ie)
    sys.exit(1)


def parseIproute(stdout, cmpls):
    iface = ''
    netInfo = dict()
    for line in stdout:
        ifaceInfo = cmpls['iface'].search(line)
        ipInfo = cmpls['ip'].search(line)
        macInfo = cmpls['mac'].search(line)
        if ifaceInfo is not None:
            iface = ifaceInfo.group('iface')
            netInfo[iface] = dict()
            netInfo[iface]["ip"] = list()
            netInfo[iface]["mac"] = '000000000000'
        if ipInfo is not None:
            netInfo[iface]["ip"].append(ipInfo.group('ip'))
        if macInfo is not None:
            netInfo[iface]["mac"] = macInfo.group('mac').upper().replace(':',
                                                                         '')
    return netInfo


def main():
    with racktables() as rt:
        rt.connect()
        sshOps = serverGroup()
        ptrns = dict()
        ptrns['iface'] = re.compile('^[0-9]+: (?P<iface>[^:@]+)')
        ptrns['ip'] = re.compile('inet (?P<ip>[0-9\.\/]+)')
        ptrns['mac'] = re.compile('link\/ether (?P<mac>[0-9a-f:]+)')
        ignoredIfaces = ['lo', 'kvm']
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
                    realInfo = parseIproute(ipOutput, ptrns)
                    dbInfo = dict()
                    dbIps = rt.getServerIPs(server[0])
                    dbIfaces = rt.getServerInterfaces(server[0])
                    for i in dbIps.keys():
                        dbInfo[i] = dict()
                        if i in dbIfaces:
                            dbInfo[i]["mac"] = dbIfaces[i]
                            # if i not in ignoredIfaces:
                            #    print("=> %s %s %s" % (i, dbIfaces[i],
                            #          ','.join(dbInfo[i])))
                        else:
                            dbInfo[i]["mac"] = '000000000000'
                            print("!!! %s interface is not registered" % i)
                            # print("=> %s %s" % (i, ','.join(dbInfo[i])))
                        dbInfo[i]["ip"] = dbIps[i]
                    for i in dbIfaces.keys():
                        if i not in dbInfo:
                            dbInfo[i] = dict()
                            dbInfo[i]["mac"] = dbIfaces[i]
                            dbInfo[i]["ip"] = list()
                    for i in realInfo.keys():
                        # if i not in ignoredIfaces:
                        #    print("|- %s %s %s" % (i, realInfo[i]["mac"],
                        #          ','.join(realInfo[i]["ip"])))
                        if i not in ignoredIfaces:
                            if i not in dbInfo:
                                print("insert into Port (object_id, name, "
                                      "iif_id, type, l2address) values (%s, "
                                      "'%s', 1, 24, '%s');" %
                                      (server[0], i, realInfo[i]["mac"]))
                            else:
                                if realInfo[i]["mac"] != dbInfo[i]["mac"]:
                                    print("!!! %s MAC mismatch: %s <=> %s" %
                                          (i, realInfo[i]["mac"],
                                           dbInfo[i]["mac"]))
                                for ip in realInfo[i]["ip"]:
                                    if ip.split("/")[0] not in dbInfo[i]["ip"] \
                                       and ip.split("/")[1] != 32:
                                           print("!!! Unregistered IP %s "
                                                   "(%s:%s)" % (ip, server[1],
                                                                i))
        except KeyboardInterrupt:
            sys.exit(2)
    return

if __name__ == "__main__":
    main()
