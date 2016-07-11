#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from remote import serverGroup, sshLoginException
    from trovitdb.racktables import racktables
except ImportError as ie:
    print(ie)
    sys.exit(1)


def main():
    with racktables() as rt:
        rt.connect()
        sshOps = serverGroup()
        try:
            for server in rt.getActiveServers():
                # server: (id,name,type)
                try:
                    # Get 1 char to know the OS version
                    osVer = sshOps.sshCmd(server[1], "cat "
                                          "/etc/debian_version",
                                          sync=True)[0][0][0]
                except sshLoginException as sLE:
                    print(sLE)
                else:
                    if osVer != '':
                        rtVer = rt.getServerVersion(server[0])
                        if rtVer == '':
                            print("Adding OS version (%s) for %s"
                                  % (osVer, server[1]))
                            rt.insertVersion(server[0], server[2], osVer)
                        else:
                            if osVer != rtVer:
                                print("Changing OS version for %s "
                                      "from \'%s\' to \'%s\'"
                                      % (server[1], rtVer, osVer))
                                rt.updateVersion(server[0], osVer)
                    else:
                        print("Error getting OS version from %s" % server[1])
        except KeyboardInterrupt:
            sys.exit(2)
    return

if __name__ == "__main__":
    main()
