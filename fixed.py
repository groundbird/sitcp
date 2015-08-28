#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.slowCtrl import *
from lib.readout import *
from sys import argv, exit, stdout
from os import system
from os.path import getsize
from datetime import datetime
from struct import unpack
from time import sleep
from argparse import ArgumentParser
import numpy as np

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

def fixed2file(readout_obj, fname, dsize):
#     if binary:
#         fname = '%s.bin' % fname
#     else:
#         fname = '%s.dat' % fname
    with open(fname, 'wb') as f:
        if dsize < BUFF:
            data = readout_obj.read(dsize)
            if len(data) != dsize:
                raise ReadoutError('Data length mismatch.')
                exit()
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
        nargs   = '?',
        default = 1e6, # Hz
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

    date   = datetime.today()
    fname  = 'data/fixed_%s.bin' % date.strftime('%Y%m%d_%H%M%S')
    freq   = args.freq
    sample = args.time * (SAMPLE_RATE/DOWNSAMPLE_RATE)
    dsize  = int(sample*DATA_UNIT)
    binary = args.binary

    # Generate instance and connect
    s = RBCP()
    r = Readout()
    r.connect()

    # Begin the readout sequence
    s.set_freq(freq)
    s.iq_rd() # on
    fixed2file(r, fname, dsize)

    # End the readout sequence
    s.iq_rd() # off
    r.close()

    # Cut unnecessary data
    if dsize > BUFF:
        system('split -b %d %s %s.' % (dsize, fname, fname))
        system('mv %s.aa %s' % (fname, fname))
        system('rm %s.*' % fname)

    # Convert binary to text
    if not binary:
        with open(fname, 'r') as f:
            bd = f.read()
            td = conv_iq_data(np.array(unpack('B'*len(bd), bd)))
            with open(fname[:-3]+'dat', 'w') as _f:
                for d in zip(*td):
                    print >> _f, '%d\t%+e\t%+e' % d

    # Debug
    fsize = getsize(fname)
    if fsize == dsize:
        print 'Succeeded in readout (%d bytes).' % fsize
        print 'Bye-Bye (^_^)/~'
        if not binary: system('rm %s' % fname) # Remove binary file
    else:
        print 'Failed in readout.'
        print 'Dropped %d bytes data.' % (dsize-fsize)
