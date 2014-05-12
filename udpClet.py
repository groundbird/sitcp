#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import *
from contextlib import closing

def main():
    host = '127.0.0.1'
    port = 14512
    buff = 1024
    user = 'Client'
    
    cs = socket(AF_INET, SOCK_DGRAM)
    with closing(cs):
        while True:
            msg = raw_input('%s > ' % user)
            if not msg: break
            cs.sendto(msg, (host, port))
            msg, addr = cs.recvfrom(buff)
            if not msg: break
            print msg

if __name__ == '__main__':
    main()
