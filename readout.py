#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST = '192.168.10.16'
PORT = 24 # TCP
BUFF = 1024

from socket import socket, error
from contextlib import closing
from struct import unpack, calcsize
from time import sleep
from os import system
from os.path import getsize
from errno import EWOULDBLOCK, ETIMEDOUT
from slowCtrl import RBCPError, RBCP

class ReadoutError(Exception):
    def __init__(self, msg):
        self.msg = 'Readout Error: %s' % str(msg)

    def __str__(self):
        return self.msg

class Readout(object):
    def __init__(self, host=HOST, port=PORT, buff=BUFF):
        self.host = host
        self.port = port
        self.buff = buff
        self.sock = socket()
        self.sock.setblocking(0)
        self.sock.settimeout(0.1)

    def connect(self):
        self.sock.connect((self.host, self.port))

    def close(self):
        self.sock.close()

    def read(self):
        return self.sock.recv(self.buff)

    def write(self, fname, fsize):
        f = open(fname, 'w')
#         while True:
        while getsize(fname) < fsize:
            try:
                d = self.read()
                if not d:
                    print 'connection closed'
                    f.close()
                    self.close()
                    break
                else:
                    f.write(d)
                    f.flush()
            except error, e:
                if e.args[0] == EWOULDBLOCK:
                    print 'EWOULBLOCK'
                    sleep(1)
                else:
                    print e
                    break

def adc_snapshot(fname, dsize=11*131072):
    s = RBCP()
    s.adc_snapshot()
    r = Readout()
    r.connect()
    r.write(fname, dsize)
    
    for i, x in enumerate(unpack_data(fname)):
        if i% 11 == 10:
            print '%02X' % x
        else:
            print '%02X' % x,

    print '-'*10
    fsize = getsize(fname)
    if dsize == fsize:
        print 'Succeeded in readout data'
    else:
        print 'Failed in readout data'
        print '%d bytes drop' % (dsize - fsize)
    print 'File size is %d bytes (%d KB)' % (fsize, fsize/1024)
    
    r.close()

def unpack_data(fname):
    f = open(fname, 'r')
    b = f.read()
    return list(unpack('B'*len(b), b))
    
if __name__ == '__main__':
    adc_snapshot('data/binary')
