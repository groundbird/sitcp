#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.slowCtrl import *
from random import randint

N = 1e6

s = RBCP()

# data = [randint(0, 255) for x in range(int(1e6))]
# for d in data:
#     wd = s.wr('a0000000', format(d, 'x').zfill(2))[1][0]
#     rd = s.rd('a1000000')[1][0]
#     if wd != rd:
#         print 'error'
#         print 'write: %s, read: %s' % (wd, rd)


# data = [format(randint(0, 255), 'x').zfill(2) for x in range(8)]
# data_8 = ''
# for d in data:
#     data_8 += d

def foo():
    gen_data = lambda: [format(randint(0, 255), 'x').zfill(2) for x in range(8)]
    ret = ''
    for d in gen_data():
        ret += d
    return ret

def bar(num):
    ret = []
    for i in xrange(num):
        ret.append(foo())
    return ret


for wd in bar(int(N)):
    try:
        s.wr('a0000000', wd) # write
        rd = []
        i = 0
        j = 0
        for d in range(8):
            rd.append(format(int(s.rd('a100000'+str(i))[1][0], 16), 'x').zfill(2))
            i += 1
        rd_ = ''
        for d in rd:
            rd_ += d

        print wd, rd_
        errList = []
        if wd != rd_:
            print 'error'
            print 'write: %s, read: %s' % (wd, rd_)
            errList.append([j, wd, rd_])

        j += 1
        
    except KeyboardInterrupt:
        break


if len(errList) != 0:
    print errList
else:
    print 'no problem!'
