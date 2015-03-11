#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST = '192.168.10.16'
PORT = 4660
BUFF = 512

VER_TYPE    = 0xff
CMD_FLAG_TX = 0x80
CMD_FLAG_RX = 0xc0
PKT_ID      = 0x00
DATA_LENGTH = 0x05

from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM

class RBCP(object):
    def __init__(self, host=HOST, port=PORT, buff=BUFF):
        self.host = host
        self.port = port
        self.buff = buff
        self.sock = socket(AF_INET, SOCK_DGRAM)        

    def __del__(self):
        self.sock.close()
        del self

    def header(self, cmd, id=PKT_ID, d_len=DATA_LENGTH):
        return [VER_TYPE, cmd, id, d_len]

    def write(self, addr, data):
        p = self.header(CMD_FLAG_TX) + conv_int_list(addr) + conv_int_list(data)
        pkt = pack('13B', *p)
        self.sock.sendto(pkt, (self.host, self.port))
        data, addr = self.sock.recvfrom(self.buff)
        return data, addr

    def read(self, addr, data='00'*5):
        if len(addr) != 8:
            print 'Address length is mismatch (%d given)' % len(addr)
            print 'Address must be 8 length'
            exit
        p = self.header(CMD_FLAG_RX) + conv_int_list(addr) + conv_int_list(data)
        pkt = pack('13B', *p)
        self.sock.sendto(pkt, (self.host, self.port))
        data, addr = self.sock.recvfrom(self.buff)
        return data, addr

def split_str(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def conv_int_list(str):
    return [int(x, 16) for x in split_str(str, 2)]
