#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST = '192.168.10.16'
PORT = 4660
BUFF = 255

# RBCP packet format
VER_TYPE    = 0xff
CMD_FLAG_TX = 0x80
CMD_FLAG_RX = 0xc0
PKT_ID      = 0x00
DATA_LENGTH = 0x01

# ads4249/dac3283 register map
ADDR_ADC = ['00', '01', '03', '25', '29', '2b', '3d', '3f',
            '40', '41', '42', '45', '4a', '58', 'bf', 'c1',
            'cf', 'ef', 'f1', 'f2', '02', 'd5', 'd7', 'db']
DATA_ADC = ['00' for i in range(24)]
ADDR_DAC = ['%02X' % i for i in range(32)]
DATA_DAC = ['70', '11', '00', '10', 'ff', '00', '00', '00',
            '00', '7a', 'b6', 'ea', '45', '1a', '16', 'aa',
            'c6', '24', '02', '00', '00', '00', '00', '04',
            '83', '00', '00', '00', '00', '00', '24', '12']

FS = 200e6 # ADC sample rate

from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM, timeout

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
        self.sock.setblocking(0)
        self.sock.settimeout(1)

    def __del__(self):
        self.sock.close()
        del self

    def write(self, addr, data):
        d_len = len(data)/2 # byte
        if d_len > 247:
            raise RBCPError('Data is long. Data length must be less than 247 bytes.')
        p   = [VER_TYPE, CMD_FLAG_TX, PKT_ID, d_len]
        p  += conv_int_list(addr)
        p  += conv_int_list(data)
        pkt = pack(str(8+d_len)+'B', *p)
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

    def wr(self, addr, data):
        d_len = len(data)/2 # byte
        data, addr = self.write(addr, data)
        if d_len == 0: raise RBCPError('Bus Error: Data lost')
        bus = [hex(x) for x in unpack(str(8+d_len)+'B', data)]
        if bus[1] == '0x89':
            raise RBCPError('Bus Error')
        b_addr = bus[4:8]
        b_data = bus[8:]
        return b_addr, b_data

    def rd(self, addr, d_len=DATA_LENGTH):
        data, addr = self.read(addr, d_len)
        if d_len == 0: raise RBCPError('Bus Error: Data lost')
        bus = [hex(x) for x in unpack(str(8+d_len)+'B', data)]
        if bus[1] == '0xc9':
            raise RBCPError('Bus Error')
        b_addr = bus[4:8]
        b_data = bus[8:]
        return b_addr, b_data

    def adc_reset(self):
        self.wr('10000000', '02')

    def adc_read_enable(self):
        self.wr('10000000', '01')
    
    def adc_write_enable(self):
        self.wr('10000000', '00')

    def dac_4ena(self):
        self.wr('20000017', '04')

    def wr_adc(self, regAddr=None, regData=None):
        self.adc_write_enable()
        if (regAddr is None) and (regData is None):
            regAddr, regData = ADDR_ADC[1:], DATA_ADC[1:]
        if isinstance(regAddr, str) and isinstance(regData, str):
            addr, data = self.wr('100000'+regAddr, regData)
#             print '\t[%02X] <= %02X' % (int(addr[3], 16), int(data[0], 16))
            return addr, data
        elif isinstance(regAddr, list) and isinstance(regData, list):
            addr_list = []
            data_list = []
            for addr, data in zip(regAddr, regData):
                _addr, _data = self.wr('100000'+addr, data)
                addr_list.append(_addr)
                data_list.append(_data)
#                 print '\t[%02X] <= %02X' % (int(_addr[3], 16), int(_data[0], 16))
            return addr_list, data_list
        else:
            raise RBCPError('Write failed.')

    def rd_adc(self, regAddr=None):
        self.adc_read_enable()
        if regAddr == None:
            for addr in ADDR_ADC[1:]:
                a, d = self.rd('110000'+addr)
                print '\t[%02X]: %02X' % (int(a[3], 16), int(d[0], 16))
        elif regAddr in ADDR_ADC:
            addr, data = self.rd('110000'+regAddr)
            print '\t[%02X]: %02X' % (int(addr[3], 16), int(data[0], 16))
        else:
            raise RBCPError('Address must be string.')            

    def wr_dac(self, regAddr=None, regData=None):
        self.dac_4ena()
        if (regAddr is None) and (regData is None):
            regAddr, regData = ADDR_DAC, DATA_DAC
        if isinstance(regAddr, str) and isinstance(regData, str):
            addr, data = self.wr('200000'+regAddr, regData)
#             print '\t[%02X] <= %02X' % (int(addr[3], 16), int(data[0], 16))
            return addr, data
        elif isinstance(regAddr, list) and isinstance(regData, list):
            addr_list = []
            data_list = []
            for addr, data in zip(regAddr, regData):
                _addr, _data = self.wr('200000'+addr, data)
                addr_list.append(_addr)
                data_list.append(_data)
            return addr_list, data_list
#                 print '\t[%02X] <= %02X' % (int(_addr[3], 16), int(_data[0], 16))
        else:
            raise RBCPError('Write failed.')

    def rd_dac(self, regAddr=None):
        self.dac_4ena()
        if regAddr is None:
            for addr in ADDR_DAC:
                a, d = self.rd('210000'+addr)
                print '\t[%02X]: %02X' % (int(a[3], 16), int(d[0], 16))
        elif regAddr in ADDR_DAC:
            addr, data = self.rd('210000'+regAddr)
            print '\t[%02X]: %02X' % (int(addr[3], 16), int(data[0], 16))
        else:
            raise RBCPError('Read failed.')

    def adc_snapshot(self):
        self.wr('30000000', '00')

    def iq_rd(self):
        self.wr('50000000', '00')
    
    def reset(self):
        try:
            self.wr('f0000000', '00')
        except timeout:
            pass

    def set_freq(self, freq=1e6): # freq [Hz]
        if freq < 0:
            self.wr('40000000', format(int((FS+freq)/FS*2**32), 'x').zfill(8))
        else:
            self.wr('40000000', format(int(freq/FS*2**32), 'x').zfill(8))

    def check_freq(self):
        return self.rd('61000000', 0x01)

    @property
    def register_init(self):
        """
        Initialize ADC/DAC register
        """
        self.wr_adc('42', 'f8')                 # delay data clock
        self.wr_dac(['01', '13'], ['01', 'c0']) # disable interpolation


def split_str(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def conv_int_list(str):
    return [int(x, 16) for x in split_str(str, 2)]

def dict_reg(addr, data):
    if len(addr) != len(data):
        raise Exception('Error: Addess and Data length must be same')
    reg = dict()
    for a, d in zip(addr, data): reg[a] = d
    return reg
