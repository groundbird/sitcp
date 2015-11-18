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

FS        = 200e6 # ADC sample rate
N_CHANNEL = 2

from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from time import sleep
from sys import exit
import numpy as np

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
#         self.sock.setblocking(1)
        self.sock.settimeout(1)

    def __del__(self):
        self.sock.close()
        del self

    def write(self, addr, data):
        d_len = len(data)/2 # bytes
        if d_len > BUFF-8: # VER_TYPE + CMD_FLAG + ID + ADDR = 8 bytes
            raise RBCPError('Data is long. Data length must be < 247 B.')
        p   = [VER_TYPE, CMD_FLAG_TX, PKT_ID, d_len] # header
        p  += conv_int_list(addr)
        p  += conv_int_list(data)
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
        self.wr('10000000', '01')

    @property
    def adc_write_enable(self):
        self.wr('10000000', '00')

    @property
    def dac_4ena(self):
        self.wr('20000017', '04')

    def wr_adc(self, regAddr=None, regData=None):
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
            raise RBCPError('Address must be string.')            

    def wr_dac(self, regAddr=None, regData=None):
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
    def adc_snapshot(self):
        self.wr('30000000', '00')

    @property
    def iq_tgl(self):
        self.wr('50000000', '00')

    @property
    def chk_stat(self):
        return self.rd('60000000')
#         addr, data = self.rd('60000000')
#         if data == '\0x01':
#             return 'busy'
#         else:
#             return 'idle'

    @property
    def dds_en(self):
        self.wr('70000000', '00')

    @property
    def sitcp_reset(self):
        """
        SiTCP reset.
        (see SiTCP manual)
        """

        print 'SiTCP reset\nwait 10 seconds...'
        self.wr('ffffff10', '81') # SiTCP Reset
        sleep(10)                 # build up time (> 8 sec)
        self.wr('ffffff10', '01') # RBCP_ACT <= '1'

#     def set_freq(self, freq=1e6): # freq [Hz]
#         """
#         Set DAC output frequency.
#         e.g.,
#             set_freq([1e6, 1e7]) # (ch. 0, ch. 1) = (1 MHz, 10 MHz)
#             set_freq(1e6)        # All channels are set 1 MHz.
#         """

#         if isinstance(freq, list):
#             if N_CHANNEL != len(freq):
#                 raise ValueError('Frequency data length mismatch.')
#         elif isinstance(freq, (int, float)):
#             freq = [freq for i in range(N_CHANNEL)]
#         else:
#             raise TypeError("freq() argument must be a list or a number, not '%s'" % type(freq))
#         data = ''
#         for f in freq:
#             if f < 0:
#                 d = format(int((FS+f)/FS*2**32), 'x').zfill(8)
#                 if len(d) != 8:
#                     raise RBCPError('bug')
#                 data += d
#             else:
#                 d = format(int(f/FS*2**32), 'x').zfill(8)
#                 if len(d) != 8:
#                     raise RBCPError('bug')
#                 data += d
# #         data = '00' + data # symptomatic therapy
#         self.wr('40000000', data)
#         self.dds_en

#         return data

#     def set_freq2(self, freq=1e6):
#         if isinstance(freq, (list, tuple)):
#             if len(freq) != N_CHANNEL:
#                 raise ValueError('Frequency data length mismatch.')
#         elif isinstance(freq, (int, float)):
#             freq = [freq for i in range(N_CHANNEL)]
#         else:
#             raise TypeError("freq() argument must be a list or a number, not '%s'" % type(freq))
        
#         data = ''
#         for f in freq:
#             if f < 0:
#                 d = format(int((FS+f)/FS*2**32), 'x').zfill(8)
#                 print d, len(d)
#                 data += d
#             else:
#                 d = format(int(f/FS*2**32), 'x').zfill(8)
#                 print d, len(d)
#                 data += d

#         # ch. 0
#         self.wr('40000001', data[0:2])
#         self.wr('40000002', data[2:4])
#         self.wr('40000003', data[4:6])
#         self.wr('40000004', data[6:8])
#         # ch. 1
#         self.wr('40000005', data[ 8:10])
#         self.wr('40000006', data[10:12])
#         self.wr('40000007', data[12:14])
#         self.wr('40000008', data[14:16])
# #         self.wr('40000000', data)
#         self.dds_en
#         print 'set!'

#     def set_freq3(self, pinc=1e6, poff=0):
#         """
#         Set output frequency.
#         pinc: phase increment
#         poff: phase offset
#         """
#         if isinstance(pinc, (list, tuple)):
#             if len(pinc) != N_CHANNEL:
#                 raise ValueError('PINC data length mismatch')
#         elif isinstance(pinc, (int, float)):
#             pinc = [pinc for i in range(N_CHANNEL)]
#         else:
#             raise TypeError('PINC data must be a list or number: %s' % type(pinc))

#         if isinstance(poff, (list, tuple)):
#             if len(poff) != N_CHANNEL:
#                 raise ValueError('POFF data length mismatch')
#         elif isinstance(poff, (int, float)):
#             poff = [poff for i in range(N_CHANNEL)]
#         else:
#             raise TypeError('POFF data must be a list or number: %s' % type(poff))

#         ret  = []
#         data = ''
#         for ch, (freq, phase) in enumerate(zip(pinc, poff)):
#             data += get_poff(phase)
#             data += get_pinc(freq)
#             addr = '40000' + format(ch, 'x').zfill(2) + '0'
#             _addr, _data = self.wr(addr, data)
#             ret.append([_addr, _data])
#         else:
#             self.dds_en
#         return ret

    def wr_phase(self, ch, poff, pinc):
        """
        Write phase data (POFF, PINC)
        """
        wrData = poff + pinc
        rdData = self.wr('40000'+format(ch, 'x').zfill(2)+'0', wrData)[1]
        if chunk_byte(wrData) != rdData:
            raise RBCPError('write data and read data not match')
        poff = rdData[:4]
        pinc = rdData[4:]
        return poff, pinc

    def rd_phase(self, ch):
        """
        Read phase data (POFF, PINC)
        """
        data = []
        for i in range(8):
            d = self.rd('41000'+format(ch, 'x').zfill(2)+str(i))[1][0]
            data.append(d)
        poff = data[:4]
        pinc = data[4:]
        return poff, pinc

    def set_freq(self, freq=1e6, phase=0, channel='ALL'):
        if channel is 'ALL':
            for ch in range(N_CHANNEL):
                self.wr_phase(ch, get_poff(phase), get_pinc(freq))
        else:
            self.wr_phase(channel, get_poff(phase), get_pinc(freq))
        self.dds_en

    @property
    def register_init(self):
        """
        Initialize ADC/DAC register.
        """
        self.wr_adc('42', 'f8')                 # delay data clock
        self.wr_dac(['01', '13'], ['01', 'c0']) # disable 2/4x interpolation

    @property
    def dac_temp(self):
        """
        Read the DAC temperature in degrees of Celsius.
        """
        return int(self.rd_dac('05').values()[0], 16)


def split_str(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def conv_int_list(str):
    return [int(x, 16) for x in split_str(str, 2)]

def get_poff(phase, width=32, flatten=True):
    """
    Get phase offset values.
    Specifyed phase is a degree (e.g., 45, 60, ...).
    """
    while phase < 0: phase += 360
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
    """
    Get phase increment values.
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
    return [hex(int(data[i:i+2], 16)) for i in range(0, len(data), 2)]
