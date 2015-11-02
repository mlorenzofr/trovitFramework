#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from time import strftime, localtime

try:
    from trovitdb.racktables import racktables
except ImportError as ie:
    print(ie)
    sys.exit(1)


def main():
    with racktables() as rt:
        print("| %30s | %10s |" % ('server', 'date'))
        print("|%s|%s|" % ('-' * 32,'-' * 12))
        rt.connect()
        try:
            for server in rt.getPhysicalServers():
                # server: (id,name,type)
                if not rt.isRetired(server[0]):
                    expireDate = rt.getServerMaintenanceHW(server[0])
                    if expireDate == 0:
                        humanDate = ''
                    else:
                        humanDate = strftime('%Y-%m-%d',
                                             localtime(expireDate))
                    print("| %30s | %10s |" % (server[1], humanDate))
        except KeyboardInterrupt:
            sys.exit(2)
        print("|%s|%s|" % ('-' * 32,'-' * 12))
    return

if __name__ == "__main__":
    main()
