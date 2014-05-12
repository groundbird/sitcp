#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import *
from time import ctime
from contextlib import closing

def main():
    host = '127.0.0.1'
    port = 14512
    buff = 1024
    user = 'Server'

    ss = socket(AF_INET, SOCK_DGRAM)
    with closing(ss):
        ss.bind((host, port))
        while True:            
            print 'Waiting for message...'
            msg, addr = ss.recvfrom(buff)
            ss.sendto('%s > %s [%s]' % (user, msg, ctime()), addr)
            print 'Received from', addr

if __name__ == '__main__':
    main()
    
