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
        print("| %30s | %10s | %10s |" % ('server', 'support', 'hardware'))
        print("|%s|%s|%s|" % ('-' * 32, '-' * 12, '-' * 12))
        rt.connect()
        try:
            for server in rt.getPhysicalServers():
                # server: (id,name,type)
                if not rt.isRetired(server[0]):
                    dates = [[0, ''], [0, '']]
                    dates[0][0] = rt.getServerSupportExpiration(server[0])
                    dates[1][0] = rt.getServerHardwareExpiration(server[0])
                    for date in dates:
                        if date[0] == 0:
                            date[1] = ''
                        else:
                            date[1] = strftime('%Y-%m-%d',
                                               localtime(date[0]))
                    print("| %30s | %10s | %10s |"
                          % (server[1], dates[0][1], dates[1][1]))
        except KeyboardInterrupt:
            sys.exit(2)
        print("|%s|%s|%s|" % ('-' * 32, '-' * 12, '-' * 12))
    return

if __name__ == "__main__":
    main()
