#!/usr/bin/env python
# -*- coding: utf-8 -*-

from slowCtrl import *
from readout import *
from sys import argv
from os import system
from os.path import getsize
from datetime import datetime
from struct import unpack
from time import sleep

N_CHANNEL = 1
DATA_UNIT = N_CHANNEL*14+7  # IQ data + header/footer/timestamp [bytes]

if __name__ == '__main__':
    date   = datetime.today()
    fname  = 'data/sweep_%s.bin' % date.strftime('%Y%m%d_%H%M%S')
    sample = 1
    fmin   = -1e8
    fmax   =  1e8
    fres   =  5e7

    fran = np.arange(fmin, fmax+fres, fres)
    dsize  = DATA_UNIT*sample

    # Generate objects
    s = RBCP()
    r = Readout()

    # Begin the readout sequence
    r.connect()
    r.clear()
    s.iq_rd() # on
#     f = open(fname, 'w')
#     for freq in fran:
    s.set_freq()
    data_freq = ''
#     while len(data_freq) < dsize:
    while True:
        try:
            if len(data_freq) > dsize:
                print 'try break'
#                 break
            d = r.read()
            data_freq += d
            print unpack('B'*len(d), d)
            print len(data_freq)
        except KeyboardInterrupt:
            print '\nStopped readout'
            break
        finally:
            print 'fin'
            s.iq_rd() # off
            r.close()

#     j = 0
#     for i in unpack('B'*len(data_freq), data_freq):
#         j += 1
#         if j % 21 == 0:
#             print i
#         else:
#             print i,
#         ts, i, q = iq_data_read(np.array(unpack('B'*dsize, data_freqp[:dsize])))
#         print ts
#         s.iq_rd()
#         r.close()
#         break
            
    # Cut unnecessary data
#     system('split -b %d %s %s.' % (dsize, fname, fname))
#     system('mv %s.aa %s' % (fname, fname))
#     system('rm %s.*' % fname)

    # Debug
#     fsize = getsize(fname)
#     if fsize == dsize:
#         print 'Succeeded in readout'
#     else:
#         print 'Failed in readout'
#         print 'Dropped %d bytes data' % (dsize - fsize)
