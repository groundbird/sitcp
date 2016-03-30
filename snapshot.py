#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
import numpy as np
from os import system
from datetime import datetime
from lib.slowCtrl import *
from lib.readout import *

def adc_read(slowCtrl_obj, readout_obj, fname, dsize=11*131072):
    """Read ADC values
    dsize is header(1) + timestamp(5) + ch.A(2) + ch.B(2) + footer(1) = 11B.
    131072 is fifo depth.
    """

    readout_obj.clear()
    slowCtrl_obj.snapshot
    sleep(1)
    readout_obj.write(fname, dsize)
    
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
#         system('split -b %d %s %s.' (dsize, fname, fname))
#         system('mv %s.aa %s' % (fname, fname))
#         system('rm %s.*' % fname)
    print 'File size is %d bytes (%d KB)' % (fsize, fsize/1024)
    readout_obj.close()


if __name__ == '__main__':
    # Generate instance and connect
    s = RBCP()
    r = Readout()
    r.connect()
    date = datetime.utcnow()
    fname = 'data/snapshot_%s.bin' % date.strftime('%Y%m%d_%H%M%S')
    adc_read(s, r, fname)
