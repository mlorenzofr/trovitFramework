#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from trovitdb.racktables import racktables, int2ip
except ImportError as ie:
    print(ie)
    sys.exit(1)


def main():
    with racktables() as rt:
        rt.connect()
        print int2ip(rt.getFreeIP('Backend', 205))
    return

if __name__ == "__main__":
    main()
