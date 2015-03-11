#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import *
from time import ctime
from contextlib import closing
from struct import unpack

def main():
    host = '127.0.0.1'
    port = 14512
    buff = 1024
    user = 'SiTCP'

    ss = socket(AF_INET, SOCK_DGRAM)
    with closing(ss):
        ss.bind((host, port))
        while True:            
            print 'Waiting for message...'
            msg, addr = ss.recvfrom(buff)
            if msg[1] == '\xC0': # read
                print 'Read SiTCP address: %x%x%x%x' % unpack('4B', msg[4:8])
                reg_data = '0000'
                ss.sendto(reg_data, addr)
            elif msg[1] == '\x80': # write
                print 'Recived data is %x%x%x%x%x' % unpack('5B', msg[8:13])
                print 'Write ADC %x%x%x%x register' % unpack('4B', msg[4:8])
                ss.sendto('Write succeessful!', addr)
            else:
                ss.sendto('%s > %s [%s]' % (user, msg, ctime()), addr)
                print '%s\nReceived from (%s, %s)' % (msg, addr[0], addr[1])

if __name__ == '__main__':
    main()
    
