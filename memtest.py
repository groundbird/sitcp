#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.slowCtrl import *
from random import randint
from sys import argv, exit

FPGA_REGISTER = 8   # bytes
N_TRIAL       = 1e6
BEGIN         = 0

def get_random_hex(bytes=FPGA_REGISTER):
    return [format(randint(0, 255), 'x').zfill(2) for x in range(bytes)]

def flatten(dataList):
    ret = ''
    for d in dataList:
        ret += d
    return ret

def get_random_data(length):
    length = int(length) if not isinstance(length, int) else length
    ret = []
    for i in xrange(length):
        ret.append(flatten(get_random_hex()))
    return ret

def get_increment_data(ini, fin):
    ini = long(ini)
    fin = long(fin)
    return [format(x, 'x').zfill(2*FPGA_REGISTER) for x in xrange_(ini, fin)]

def xrange_(ini, fin):
    """
    xrange in python 2.7x fails on numbers larger than C longs.
    """
    i = ini
    while i < fin:
        yield i
        i += 1

def memtest(RBCP, wrData, quiet=False):
    errList = []
    for wd in wrData:
        RBCP.wr('a0000000', wd) # write
        rdData, i, j = [], 0, 0
        for d in range(FPGA_REGISTER):
            rd = format(int(RBCP.rd('a100000'+str(i))[1][0], 16), 'x').zfill(2)
            rdData.append(rd) # read
            i += 1
        rd = ''.join(rdData)
        if not quiet:
            print wd, rd, len(errList)

        if wd != rd:
            print 'error'
            print 'write: %s, read: %s' % (wd, rd)
            errList.append([j, wd, rd])
        j += 1

#     if len(errList) != 0:
#         print '-'*20
#         print 'error:'
#         print errList
#     else:
#         print '-'*20
#         print 'No problem!'

    return len(errList)

def usage():
    print """
Usage:
\tpython memtest.py [-rand] [-inc or -num]

Options:
\t-r, --rand [int]   Write a random value N_TRIAL times. e.g., --rand 1000
\t-i, --inc [hex]    Write a increment value. e.g., -i 0xff
"""
    return exit()

s = RBCP()

if len(argv) == 1:
    mode = 'random'
elif len(argv) == 2:
    if argv[1] == '-r' or argv[1] == '--rand':
        mode = 'random'
    elif argv[1] == '-i' or  argv[1] == '--inc':
        mode = 'increment'
    else:
        usage()
elif len(argv) == 3:
    if argv[1] == '-r' or argv[1] == '--rand':
        mode = 'random'
        N_TRIAL = float(argv[2])
    elif argv[1] == '-i' or argv[1] == '--inc':
        mode = 'increment'
        BEGIN = int(argv[2], 16)
#         BEGIN = long(argv[2], 16)
    else:
        usage()
else:
    usage()


if mode == 'random':
    div, block, errNum = 1, 2**16, 0
    while N_TRIAL/div > block: div *= 2
    for i in xrange(div):
        memtest(s, get_random_data(N_TRIAL/div))
    else:
        print '\n--------------------'
        print 'trial: %s' % long(N_TRIAL)
        print 'error: %s' % errNum

elif mode == 'increment':
    lastValue = 2**(FPGA_REGISTER*8)
    div, block, errNum, j = 1, 2**16, 0, 0
    while lastValue/div > block: div *= 2
    for i in xrange(div):
        i += BEGIN/block
        if (i+1)*block > lastValue: break
        errNum += memtest(s, get_increment_data(i*block, (i+1)*block))
        j += 1
    else:
        print '\n--------------------'
        print 'trial: %s' % int(j*block)
        print 'error: %s' % errNum
    
else:
    usage()


