#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST = '192.168.10.16'
PORT = 4660
BUFF = 255

VER_TYPE    = 0xff
CMD_FLAG_TX = 0x80
CMD_FLAG_RX = 0xc0
PKT_ID      = 0x00
DATA_LENGTH = 0x01

from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM

class RBCPError(Exception):
    def __init__(self, msg):
        self.msg = 'RBCP Error: %s' % str(msg)

    def __str__(self):
        return self.msg

class RBCP(object):
    def __init__(self, host=HOST, port=PORT, buff=BUFF):
        self.host = host
        self.port = port
        self.buff = buff
        self.sock = socket(AF_INET, SOCK_DGRAM)        

    def __del__(self):
        self.sock.close()
        del self

    def write(self, addr, data):
        d_len = len(data)/2 # byte
        if d_len > 247:
            raise RBCPError('Data is too long. Data length must be less than 247 bytes.')
        p   = [VER_TYPE, CMD_FLAG_TX, PKT_ID, d_len]
        p  += conv_int_list(addr)
        p  += conv_int_list(data)
        pkt = pack(str(8+d_len) + 'B', *p)
        self.sock.sendto(pkt, (self.host, self.port))
        data, addr = self.sock.recvfrom(self.buff)
        return data, addr

    def read(self, addr, d_len=DATA_LENGTH):
        p   = [VER_TYPE, CMD_FLAG_RX, PKT_ID, d_len]
        p  += conv_int_list(str(addr))
        pkt = pack('8B', *p)
        self.sock.sendto(pkt, (self.host, self.port))
        data, addr = self.sock.recvfrom(self.buff)
        return data, addr

    def wr(self, addr='10000000', data='01'):
        d_len = len(data)/2 # byte
        data, addr = self.write(addr, data)
        if d_len == 0: raise RBCPError('Bus Error: Data lost')
        bus = [hex(x) for x in unpack(str(8+d_len) + 'B', data)]
        if bus[1] == 137: # 137 = 0x89
            raise RBCPError('Bus Error')
        b_addr = bus[4:8]
        b_data = bus[8:]
        return b_addr, b_data

    def rd(self, addr='20000005', d_len=DATA_LENGTH):
        data, addr = self.read(addr, d_len)
        if d_len == 0: raise RBCPError('Bus Error: Data lost')
        bus = [hex(x) for x in unpack(str(8+d_len) + 'B', data)]
        if bus[1] == 201: # 201 = 0xc9
            raise RBCPError('Bus Error')
        b_addr = bus[4:8]
        b_data = bus[8:]
        return b_addr, b_data

def split_str(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def conv_int_list(str):
    return [int(x, 16) for x in split_str(str, 2)]
