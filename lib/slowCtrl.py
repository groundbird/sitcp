#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SiTCP slow controller for RHEA
"""

HOST = '192.168.10.16'
PORT = 4660
BUFF = 255

# RBCP packet parameter
VER_TYPE    = 0xff
CMD_FLAG_TX = 0x80
CMD_FLAG_RX = 0xc0
PKT_ID      = 0x00
DATA_LENGTH = 0x01

# ads4249/dac3283 register map
ADDR_ADC = ['00', '01', '03', '25', '29', '2b', '3d', '3f',
            '40', '41', '42', '45', '4a', '58', 'bf', 'c1',
            'cf', 'ef', 'f1', 'f2', '02', 'd5', 'd7', 'db']
DATA_ADC = ['00' for _i in range(24)]
ADDR_DAC = ['%02X' % _i for _i in range(32)]
DATA_DAC = ['70', '11', '00', '10', 'ff', '00', '00', '00',
            '00', '7a', 'b6', 'ea', '45', '1a', '16', 'aa',
            'c6', '24', '02', '00', '00', '00', '00', '04',
            '83', '00', '00', '00', '00', '00', '24', '12']

FS = 200e6     # ADC sample rate
N_CHANNEL = 2  # Number of multiplexing

from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from time import sleep
from sys import exit, argv
from os.path import abspath, getctime
from datetime import datetime
import numpy as np

__author__ = 'ISHITSUKA Hikaru <hikaru@post.kek.jp>'
__date__   = '%s' % datetime.fromtimestamp(getctime(abspath(__file__)))

class RBCPError(Exception):
    def __init__(self, msg):
        self.msg = 'RBCP Error: %s' % str(msg)

    def __str__(self):
        return self.msg

class RBCP(object):
    u"""RHEA を slow-control 制御するときに使う.
    引数に SiTCP の IP address (default 値は 192.168.10.16) と
    port 番号 (4660), 1 アクセスのデータ長 (最大 255) をとる.
    """

    def __init__(self, host=HOST, port=PORT, buff=BUFF):
        self.host = host
        self.port = port
        self.buff = buff
        self.sock = socket(AF_INET, SOCK_DGRAM)
#         self.sock.setblocking(1)
        self.sock.settimeout(1)

    def __del__(self):
        self.sock.close()
        del self

    def write(self, addr, data):
        d_len = len(data)/2  # bytes
        if d_len > BUFF-8:  # VER_TYPE + CMD_FLAG + ID + ADDR = 8 bytes
            raise RBCPError('Data is long. Data length must be < 247 B.')
        p   = [VER_TYPE, CMD_FLAG_TX, PKT_ID, d_len]  # header
        p  += conv_int_list(addr)                     # RBCP address
        p  += conv_int_list(data)                     # RBCP data
        pkt = pack(str(8+d_len)+'B', *p)
        self.sock.sendto(pkt, (self.host, self.port))
        data, addr = self.sock.recvfrom(self.buff)
        if data[1] == '\x89':
            raise RBCPError('Write failed.')
        return data, addr

    def read(self, addr, d_len=DATA_LENGTH):
        p   = [VER_TYPE, CMD_FLAG_RX, PKT_ID, d_len]
        p  += conv_int_list(str(addr))
        pkt = pack('8B', *p)
        self.sock.sendto(pkt, (self.host, self.port))
        data, addr = self.sock.recvfrom(self.buff)
        return data, addr

    def wr(self, addr, data):
        d_len = len(data)/2 # bytes
        _data, _addr = self.write(addr, data)
        bus = [hex(x) for x in unpack(str(8+d_len)+'B', _data)]
        if bus[1] == '0x89':
            raise RBCPError('Bus error.')
        b_addr = bus[4:8]
        b_data = bus[8:]
        return b_addr, b_data

    def rd(self, addr, d_len=DATA_LENGTH):
        data, addr = self.read(addr, d_len)
        bus = [hex(x) for x in unpack(str(8+d_len)+'B', data)]
        if bus[1] == '0xc9':
            raise RBCPError('Bus error.')
        b_addr = bus[4:8]
        b_data = bus[8:]
        return b_addr, b_data

    @property
    def adc_reset(self):
        self.wr('10000000', '02')

    @property
    def adc_read_enable(self):
        """ADC register read enable
        (see ADC4249 datasheet, P. 23)
        """
        self.wr('10000000', '01')

    @property
    def adc_write_enable(self):
        """ADC register write enable
        (see ADC4249 datasheet, P. 23)
        """
        self.wr('10000000', '00')

    @property
    def dac_4ena(self):
        """DAC register read/write enable
        (see DAC3283 datasheet, P. 23)
        """
        self.wr('20000017', '04')

    def wr_adc(self, regAddr=None, regData=None):
        """ADC register write method
        When you write ADC register, use this method (not use write() or wr())
        unless there is a particular reason.
        """
        self.adc_write_enable
        if (regAddr is None) and (regData is None):
            regAddr, regData = ADDR_ADC[1:], DATA_ADC[1:]
        if (regAddr in ADDR_ADC) and isinstance(regData, str):
            addr, data = self.wr('100000'+regAddr, regData)
            return addr, data
        elif isinstance(regAddr, list) and isinstance(regData, list):
            addr_list = []
            data_list = []
            for addr, data in zip(regAddr, regData):
                _addr, _data = self.wr('100000'+addr, data)
                addr_list.append(_addr)
                data_list.append(_data)
            return addr_list, data_list
        else:
            raise RBCPError('Write failed.')

    def rd_adc(self, regAddr=None, debug=False):
        """ADC register read method
        When you read ADC register, use this method (not use read() or rd())
        unless there is a particular reason.
        """
        self.adc_read_enable
        ret = {}
        if regAddr is None:
            for addr in ADDR_ADC[1:]:
                addr_rx, data_rx = self.rd('110000'+addr)
                _addr = format(int(addr_rx[3], 16), 'X').zfill(2)
                _data = format(int(data_rx[0], 16), 'X').zfill(2)
                ret[_addr] = _data
                if debug:
                    print '\t[%02X]: %02X' % (int(addr_rx[3], 16),
                                              int(data_rx[0], 16))
            return ret
        elif regAddr in ADDR_ADC:
            addr, data = self.rd('110000'+regAddr)
            _addr = format(int(addr[3], 16), 'X').zfill(2)
            _data = format(int(data[0], 16), 'X').zfill(2)
            ret[_addr] = _data
            if debug:
                print '\t[%02X]: %02X' % (int(addr[3], 16), int(data[0], 16))
            return ret
        else:
            raise RBCPError('Address must be string')

    def wr_dac(self, regAddr=None, regData=None):
        """DAC register write method
        When you write DAC register, use this method (not use write() or wr())
        unless there is a particular reason.
        """
        self.dac_4ena
        if (regAddr is None) and (regData is None):
            regAddr, regData = ADDR_DAC, DATA_DAC
        if (regAddr in ADDR_DAC) and isinstance(regData, str):
            addr, data = self.wr('200000'+regAddr, regData)
            return addr, data
        elif isinstance(regAddr, list) and isinstance(regData, list):
            addr_list = []
            data_list = []
            for addr, data in zip(regAddr, regData):
                _addr, _data = self.wr('200000'+addr, data)
                addr_list.append(_addr)
                data_list.append(_data)
            return addr_list, data_list
        else:
            raise RBCPError('write failed')

    def rd_dac(self, regAddr=None):
        """DAC register read method
        When you read DAC register, use this method (not use read() or rd())
        unless there is a particular reason.
        """
        self.dac_4ena
        if regAddr is None:
            addrList = ADDR_DAC
        elif isinstance(regAddr, (list, tuple)):
            addrList = regAddr
        elif regAddr in ADDR_DAC:
            addrList = [regAddr]
        else:
            raise RBCPError('read failed')
        ret = {}
        for addr in addrList:
            addr_rx, data_rx = self.rd('210000'+addr)
            _addr = format(int(addr_rx[3], 16), 'X').zfill(2)
            _data = format(int(data_rx[0], 16), 'X').zfill(2)
            ret[_addr] = _data
        return ret

    @property
    def snapshot(self):
        self.wr('30000000', '00')

    @property
    def iq_tgl(self):
        self.wr('50000000', '00')

    def iq_toggle(self, state):
        """Toggle switch of IQ data gate
        Specify 'start' or 'stop' in the first argument.
        """
        addr, data = self.rd('61000000')
        if state is 'start' and data[0] == '0x0':
            self.iq_tgl
        elif state is 'stop' and data[0] == '0x1':
            self.iq_tgl
        elif data[0] == '0x0':
            print 'start'
            sleep(0.5)
            self.iq_toggle('start')
        elif data[0] == '0x1':
            print 'stop'
            sleep(0.5)
            self.iq_toggle('stop')
        else:
            raise RBCPError('Failed IQ toggle switch')

    @property
    def chk_stat(self):
        """Check RHEA module state
        """
        addr, data = self.rd('61000000')
        return data[0]

    @property
    def reset(self):
        """Reset from PC
        """
        self.wr('80000000', '00')

    @property
    def dds_en(self):
        self.wr('70000000', '00')

    @property
    def sitcp_reset(self):
        """SiTCP reset
        (see SiTCP manual)
        """
        print 'SiTCP reset\nwait 10 seconds...'
        self.wr('ffffff10', '81')  # SiTCP Reset
        sleep(10)                  # build up time (> 8 sec)
        self.wr('ffffff10', '01')  # RBCP_ACT <= '1'

    def wr_phase(self, ch, poff, pinc):
        """Write phase data (POFF, PINC)
        """
        wrData = poff + pinc
        rdData = self.wr('40000'+format(ch, 'x').zfill(2)+'0', wrData)[1]
        if chunk_byte(wrData) != rdData:
            raise RBCPError('write data and read data not match')
        poff = rdData[:4]
        pinc = rdData[4:]
        return poff, pinc

    def rd_phase(self, ch):
        """Read phase data (POFF, PINC)
        """
        data = []
        for i in range(8):
            d = self.rd('41000'+format(ch, 'x').zfill(2)+str(i))[1][0]
            data.append(d)
        poff = data[:4]
        pinc = data[4:]
        return poff, pinc

    def set_freq(self, freq=1e6, phase=0, channel='ALL', dds_en=True):
        """Set wave parameter
        (frequency [Hz], phase [degree])
        """
        if channel is 'ALL':
            for ch in range(N_CHANNEL):
                self.wr_phase(ch, get_poff(phase), get_pinc(freq))
        else:
            self.wr_phase(channel, get_poff(phase), get_pinc(freq))
        if dds_en:
            self.dds_en

    @property
    def register_init(self):
        """Initialize ADC/DAC register
        """
        self.wr_adc('42', 'f8')                  # delay data clock
        self.wr_dac(['01', '13'], ['01', 'c0'])  # disable 2/4x interpolation

    @property
    def dac_temp(self):
        """Read the DAC temperature in degrees of Celsius
        """
        return int(self.rd_dac('05').values()[0], 16)


def split_str(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def conv_int_list(str):
    return [int(x, 16) for x in split_str(str, 2)]

def get_poff(phase, width=32, flatten=True):
    """Get phase offset values
    Specifyed phase is a degree (e.g., 45, 60, ...).
    """
    while phase < 0:
        phase += 360
    if phase >= 360:
        poff = format(int(phase/360.*2**width), 'x')[-width/4:]
        if flatten:
            return poff
        else:
            return chunk_byte(poff)
    else:
        poff = format(int(phase/360.*2**width), 'x').zfill(width/4)
        if flatten:
            return poff
        else:
            return chunk_byte(poff)

def get_pinc(freq, width=32, fs=FS, flatten=True):
    """Get phase increment values
    """
    if -fs <= freq < 0:
        pinc = format(int((fs+freq)/fs*2**width), 'x').zfill(width/4)
        if flatten:
            return pinc
        else:
            return chunk_byte(pinc)
    elif 0 <= freq <= fs:
        pinc = format(int(freq/fs*2**width), 'x').zfill(width/4)[-width/4:]
        if flatten:
            return pinc
        else:
            return chunk_byte(pinc)
    else:
        raise ValueError('invalid value: %s' % freq)

def chunk_byte(data):
    """Convert hex string data to splited byte list.
    (i.e., 'ffff' -> ['0xff', '0xff'])
    """
    return [hex(int(data[i:i+2], 16)) for i in range(0, len(data), 2)]
