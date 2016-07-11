#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from time import strftime, localtime

try:
    from trovitdb.racktables import racktables
except ImportError as ie:
    print(ie)
    sys.exit(1)


fieldLen = [13, 32, 50, 12, 12]


class fieldLenException(Exception):
    pass


def fmtLine(sep, fields, pad=' '):
    if len(fields) != len(fieldLen):
        raise fieldLenException
    line = ''
    for idx in xrange(0, len(fields)):
        line += '%s%s%s' % (sep, fields[idx].center(fieldLen[idx], pad), sep)
    return line


def border(header=True):
    print(fmtLine('+', ['-', '-', '-', '-', '-'], '-'))
    if header:
        headers = ['Service Tag', 'Server', 'Model', 'Support', 'Hardware']
        print(fmtLine('|', headers))
        print(fmtLine('+', ['-', '-', '-', '-', '-'], '-'))
    return


def fmtTime(timestamp):
    if timestamp == 0:
        value = ''
    else:
        value = strftime('%Y-%m-%d', localtime(timestamp))
    return value


def main():
    with racktables() as rt:
        border()
        rt.connect()
        try:
            for server in rt.getPhysicalServers():
                # server: (id,name,type)
                if not rt.isRetired(server[0]):
                    values = []
                    values.append(rt.getServiceTag(server[0]))
                    values.append(server[1])
                    values.append(rt.getServerModel(server[0]))
                    values.append(fmtTime(rt.getServerSupportEnd(server[0])))
                    values.append(fmtTime(rt.getServerHwEnd(server[0])))
                    print(fmtLine('|', values))
        except fieldLenException:
            print("Wrong array length for values")
            sys.exit(2)
        except KeyboardInterrupt:
            sys.exit(3)
        border(False)
    return

if __name__ == "__main__":
    main()
