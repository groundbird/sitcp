#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST            = '192.168.10.16' # IP address of SiTCP
PORT            = 24              # TCP
BUFF            = 512             # bytes
N_CHANNEL       = 1
SAMPLE_RATE     = 2e8
DOWNSAMPLE_RATE = 2e5

DATA_UNIT = N_CHANNEL*14+7  # IQ data + header/footer/timestamp [bytes]

from socket import socket, error, timeout
from contextlib import closing
from struct import unpack, calcsize
from time import sleep
from os import system
from os.path import getsize
from sys import argv
from errno import EWOULDBLOCK, ETIMEDOUT
from slowCtrl import RBCPError, RBCP
import numpy as np

class ReadoutError(Exception):
    def __init__(self, msg):
        self.msg = '%s' % str(msg)

    def __str__(self):
        return self.msg

class Readout(object):
    def __init__(self, host=HOST, port=PORT, buff=BUFF):
        self.host = host
        self.port = port
        self.buff = buff
        self.sock = socket()
#         self.sock.setblocking(1)
        self.sock.settimeout(0.1)

    def __del__(self):
        self.sock.close()

    def close(self):
        self.sock.close()

    def connect(self):
        self.sock.connect((self.host, self.port))

    def read(self, buf=BUFF):
        try:
            return self.sock.recv(buf)
        except timeout:
            return
        except error as e:
            raise e

    def clear(self):
#         while len(self.read()) != 0: pass
        while self.read() is not None: pass

    def write(self, fname, fsize=None):
        f = open(fname, 'w')
        while True:
            try:
                d = self.read()
                if not d:
                    print 'connection closed'
                    f.close()
                    break
                else:
                    f.write(d)
                    f.flush()

                if (fsize is not None) and getsize(fname) > fsize:
                    raise Exception

            except error, e:
                if e.args[0] == EWOULDBLOCK:
                    print 'EWOULBLOCK'
                    sleep(0.1)
                else:
                    print e
                    break

            except KeyboardInterrupt:
                print 'Stopped readout data'
                break

            except Exception:
                break
        return

def adc_read(fname, dsize=11*131072):
    s = RBCP()
    s.adc_snapshot()
    r = Readout()
    r.connect()
    r.write(fname, dsize)
    
    for i, x in enumerate(unpack_data(fname)):
        if i % 11 == 10:
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
    return

def iq_read(fname, d_len=None):
    dsize = None if d_len is None else DATA_UNIT*d_len
#     s = RBCP()
#     sleep(1)
    s.iq_rd() # begin read
#     r = Readout()
#     r.connect()
#     sleep(0.1)
#     s.iq_read() # begin read
    r.write(fname, dsize)
    s.iq_rd() # end read

    if dsize is not None: # cut surplus data on tail
        system('split -b %d %s %s.' % (dsize, fname, fname))
        system('mv %s.aa %s' % (fname, fname))
        system('rm %s.*' % fname)
#         print 'sleep'
#         sleep(3)

#     for i, x in enumerate(unpack_data(fname)):
#         if i % DATA_UNIT == DATA_UNIT-1:
#             print '%02X' % x
#         else:
#             print '%02X' % x,

#     print '-'*10
    fsize = getsize(fname)
    if dsize == fsize:
#         print 'Succeeded in readout data'
        pass
    else:
        if dsize is not None:
            raise ReadoutError('Failed in readout data\n%d bytes drop' % (dsize - fsize))
#             print 'Failed in readout data'
#             print '%d bytes drop' % (dsize - fsize)
#     print 'File size is %d bytes (%d KB)' % (fsize, fsize/1024)
    return

def hexdump(fname):
    f = open(fname, 'r')
    b = f.read()
    f.close()
    return np.array(unpack('B'*len(b), b))

def conv_256dec_to_signed(xxxList, width=False):
    if width:
        k = width
    else:
        k = 8*len(xxxList)
    p = "{0:0" + str(k) + "b}"
    b = p.format(conv_256dec_to_unsigned(xxxList))
    ret = 0
    for i, j in enumerate(b):
        if i == 0:
            ret += -2**(k-1-i) * int(j)
        else:
            ret +=  2**(k-1-i) * int(j)
    return ret

def conv_256dec_to_unsigned(xxxList):
    """
    convert 256-decimal to unsigned
    """
    k = len(xxxList)
    ret = 0
    for i, xxx in enumerate(xxxList):
        ret += 256**(k-i-1) * xxx
    return int(ret)

def format_data_adc_snapshot(ndarray, dsize=11):
    """
    ndarray <= hexdump output
    dsize is format data size.
    """
    data = ndarray.reshape(-1, dsize)
    ts = []
    da = []
    db = []
    for d in data:
        ts.append(conv_256dec_to_unsigned(d[1:6])) # timestamp is 5 bytes
        da.append(conv_256dec_to_signed(d[6:8]))
        db.append(conv_256dec_to_signed(d[8:10]))
    return ts, da, db

def conv_iq_data(ndarray, dsize=DATA_UNIT, ds=DOWNSAMPLE_RATE):
    """
    1 unit のデータを timestamp[4:0] と I_i[6:0], Q_i[6:0] (i: channel) に変換
    """
    data = ndarray.reshape(-1, dsize)
    ts = []
    i  = []
    q  = []
    for d in data:
        ts.append(conv_256dec_to_unsigned(d[1:6]))
        for ch in range(N_CHANNEL):
            i.append(conv_256dec_to_signed(d[14*ch+ 6:14*ch+13])/ds)
            q.append(conv_256dec_to_signed(d[14*ch+13:14*ch+20])/ds)
    return ts, i, q

def iq_data_read(ndarray, dsize=DATA_UNIT, ds=DOWNSAMPLE_RATE):
    data = ndarray.reshape(-1, dsize)
    ts = []
    i  = []
    q  = []
    for d in data:
        ts.append(conv_256dec_to_unsigned(d[1:6])) # timestamp is 5 bytes
        i.append(conv_256dec_to_signed(d[ 6:13])/ds)
        q.append(conv_256dec_to_signed(d[13:20])/ds)
    return ts, i, q

def unpack_data(fname):
    f = open(fname, 'r')
    b = f.read()
    return list(unpack('B'*len(b), b))

def unpack_data2(bin, buf=BUFF):
    return unpack('B'*buf, bin)
    
