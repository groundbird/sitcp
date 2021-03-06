#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sys import argv, exit, stdout
from os import system
from os.path import getsize
from datetime import datetime
from struct import unpack
from time import sleep
from argparse import ArgumentParser
import numpy as np
import pytz
from compiler.ast import flatten

from lib.slowCtrl import *
from lib.readout import *

__version__ = '0.0.2'

def fixed(readout_obj, dsize, ds=DOWNSAMPLE_RATE):
    dsize = int(dsize)
    data  = readout_obj.read(dsize)
    if data[0] != '\xff':
        raise ReadoutError('Header is broken.')
    if data[-1] != '\xee':
        raise ReadoutError('Footer is broken.')
    if len(data) != dsize:
        raise ReadoutError('Data length mismatch.')
    ts, i, q = conv_iq_data(np.array(unpack('B'*dsize, data)))
    return ts, i, q

def fixed2file(readout_obj, fname, dsize, ds=DOWNSAMPLE_RATE):
    with open(fname, 'wb') as f:
        if dsize < BUFF:
            data = readout_obj.read(dsize)
            if len(data) != dsize:
                raise ReadoutError('Data length mismatch.')
                exit()
#             ts, i, q = conv_iq_data(np.array(unpack('B'*dsize, data)))
#             data = ts, i/ds, q/ds
            f.write(data)
            f.flush()
        else:
            while getsize(fname) < dsize:
                try:
                    data = readout_obj.read()
                    f.write(data)
                    f.flush()
                except KeyboardInterrupt:
                    print '\nStopped readout (%d bytes).' % getsize(fname)
                    break
                except error as e:
                    print e
                    break


if __name__ == '__main__':
    # Command-line options
    p = ArgumentParser(
        description = 'Take the fixed frequency readout data.')
    g = p.add_argument_group()
    g.add_argument(
        # Set frequency [Hz]
        '-f',
        '--freq',
        action  = 'store',
#         nargs   = '?',
        nargs   = N_CHANNEL,
#         default = 1e6, # Hz
        default = [1e6 for i in range(N_CHANNEL)],
        type    = float,
        dest    = 'freq',
        help    = 'The observation frequency. The default value is 1e6 (1 MHz).',
        metavar = 'Hz')
    g.add_argument(
        # Set observation time [s]
        '-t',
        '--time',
        action  = 'store',
        nargs   = '?',
        default = 1, # sec
        type    = float,
        dest    = 'time',
        help    = 'The observation time. The default value is 1 (1 sec).',
        metavar = 's')
    g.add_argument(
        # Save file option
        '-b',
        '--binary',
        action = 'store_true',
        dest   = 'binary',
        help   = 'Output file type. The deault type is text.')
    args = p.parse_args()

    date   = datetime.utcnow()
    fname  = 'data/fixed_%s.bin' % date.strftime('%Y%m%d_%H%M%S')
    freq   = args.freq
    sample = args.time * (SAMPLE_RATE/DOWNSAMPLE_RATE)+1
    dsize  = int(sample*DATA_UNIT)
    binary = args.binary

    # Generate instance and connect
    s = RBCP()
    r = Readout()
    r.connect()

    # Initialize
    s.wr_adc()      # Reset ADC register
    s.wr_dac()      # Reset DAC register
    s.register_init # Initialize ADC/DAC register

    # Begin the readout sequence
#     s.set_freq(freq)
#     s.set_freq(freq, 0, 0)
    for i in range(N_CHANNEL):
        if i % 2:
            s.set_freq(freq[i],  45, i)
        else:
            s.set_freq(freq[i], 225, i)
#     s.set_freq(freq[0],  45, 0)
#     s.set_freq(freq[1], 225, 1)
    s.iq_toggle('start')
    fixed2file(r, fname, dsize)

    # End the readout sequence
    s.iq_toggle('stop')
    r.close()

    # Cut unnecessary data
    if dsize > BUFF:
        system('split -b %d %s %s.' % (dsize, fname, fname))
        system('mv %s.aa %s' % (fname, fname))
        system('rm %s.*' % fname)

    # Convert binary to csv
    if not binary:
        with open(fname, 'r') as f:
            bin = f.read()
            csv = conv_iq_data(np.array(unpack('B'*len(bin), bin)))
            with open(fname[:-3]+'csv', 'w') as _f:
                # CSV file header
#                 print >> _f, """# Fixed point observation (Ver. %s)
# # Date                  : %s UTC
# # Sampling rate         : %d Hz
# # Number of channels    : %d
# # Observation frequency : %d Hz

# timestamp,i,q""" % (__version__,
#                     date.strftime('%Y-%m-%d %H:%M:%S'),
#                     SAMPLE_RATE/DOWNSAMPLE_RATE,
#                     (len(csv)-1)/2,
#                     freq)
                form_head = """# Fixed point observation (Ver. {})
# Date                  : {} UTC
# Sampling rate         : {:.0f} Hz
# Number of channels    : {}
"""
                form_head += '# Observation frequency :'+' {:.0f}'*N_CHANNEL
                form_head += '\ntimestamp,i[j],q[j]'
                lst = flatten([__version__,
                               date.strftime('%Y-%m-%d %H:%M:%S'),
                               SAMPLE_RATE/DOWNSAMPLE_RATE,
                               N_CHANNEL, freq])
                print form_head.format(*lst)
                print >>_f, form_head.format(*lst)
#                 for d in zip(*csv):
#                     print >> _f, '%d,%f,%f' % d
                form_data = '{}'+',{:f}'*(2*N_CHANNEL)
#                 print form_data
#                 for d in zip(*csv):
#                     print d
#                     print >>_f, form_data.format(*d)
                ts, i, q = csv
                i = zip(*[iter(i)]*N_CHANNEL)
                q = zip(*[iter(q)]*N_CHANNEL)
#                 i = i.reshape(-1, N_CHANNEL)
#                 q = q.reshape(-1, N_CHANNEL)
                for ts, i, q in zip(ts, i, q):
                    lst = flatten([ts, i, q])
                    print form_data.format(*lst)
                    print >>_f, form_data.format(*lst)
    # Debug
    fsize = getsize(fname)
    if fsize == dsize:
        print '\nSucceeded in readout (%d bytes).' % fsize
        print 'Bye-Bye (^_^)/~\n'
        if not binary: system('rm %s' % fname)  # Remove binary file
    else:
        print 'Failed in readout.'
        print 'Dropped %d bytes data.' % (dsize-fsize)
