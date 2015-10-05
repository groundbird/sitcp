#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.slowCtrl import *
from lib.readout import *
from sys import argv, exit
from os import system
from os.path import getsize
from datetime import datetime
from struct import unpack
from time import sleep
from argparse import ArgumentParser
from fixed import *

__version__ = '0.0.1'

# Command-line options
p = ArgumentParser(
    description = 'Take the frequency sweep readout data.')
g = p.add_argument_group()
g.add_argument(
    # Set frequency reange [Hz]
    '-f',
    '--freq',
    action  = 'store',
    nargs   = 2,
    default = [-1e8, 1e8], # Hz
    type    = float,
    dest    = 'fran',
    help    = 'The frequency range. The default values are -100e6/+100e6 (-100 MHz to 100 MHz).',
    metavar = ('[fmin]', '[fmax]'))
g.add_argument(
    # Set frequency step [Hz]
    '-s',
    '--step',
    action  = 'store',
    nargs   = '?',
    default = 1e6, # sec
    type    = float,
    dest    = 'step',
    help    = 'The frequency step. The default value is 1e6 (1 MHz).',
    metavar = 'step')
g.add_argument(
    # Set observation time [s]
    '-t',
    '--time',
    action  = 'store',
    nargs   = '?',
    default = 0.1, # sec
    type    = float,
    dest    = 'time',
    help    = 'The observation time per frequency. The default value is 0.1 (0.1 sec).',
    metavar = 's')
args = p.parse_args()

date   = datetime.utcnow()
fname  = 'data/sweep_%s.csv' % date.strftime('%Y%m%d_%H%M%S')
fran   = np.arange(args.fran[0], args.fran[1]+args.step, args.step)
sample = args.time * (SAMPLE_RATE/DOWNSAMPLE_RATE)
dsize  = int(sample*DATA_UNIT) # KB

# Generate object and connection
s = RBCP()
r = Readout()
r.connect()

# Begin the readout sequence
s.wr_adc()      # Reset ADC register
s.wr_dac()      # Reset DAC register
s.register_init # Initialize ADC/DAC register

print """
Start frequency sweep readout.
--------------------------------------------------
Date             : %s UTC
Frequency range  : %.2e to %.2e Hz
Frequency steps  : %.2e Hz
Observation time : %s sec
# of samples     : %d 
--------------------------------------------------
Frequency [Hz]\tI\t\tQ
""" % (date.strftime('%Y-%m-%d %H:%M:%S'),
       args.fran[0], args.fran[1], args.step, args.time, sample)

with open(fname, 'w') as f:
    # CSV file header
    print >> f, """# Frequency sweep data (Ver. %s)
# Date                    : %s UTC
# Sampling rate           : %d Hz
# Frequency range         : %d to %d Hz
# Frequency steps         : %d Hz
# # of sample / frequency : %d

freq,i,q""" % (__version__,
               date.strftime('%Y-%m-%d %H:%M:%S'),
               SAMPLE_RATE/DOWNSAMPLE_RATE,
               args.fran[0], args.fran[1],
               args.step,
               sample)
    for freq in fran:
        try:
            s.set_freq(freq); #print 'set freq'
            r.clear()
            s.iq_tgl; #print 'on'
            sleep(0.1*dsize/1000) # depend on dsize
            ts, i, q = fixed(r, dsize)
            i_mean = np.mean(i)
            q_mean = np.mean(q)
            print >> f, '%d,%f,%f' % (freq, i_mean, q_mean)
            f.flush()
            print '%+e\t%+e\t%+e' % (freq, i_mean, q_mean) # debug
            s.iq_tgl; #print 'off'
        except RBCPError as e:
            if e.msg == 'RBCP Error: Write failed':
                print 'Retry'
                s.sitcp_reset
                sleep(10)
            else:
                print e.msg
                s.sitcp_reset
                exit()
            if s.chk_stat[1][0] == '0x1':
                s.iq_tgl;
            continue

        except KeyboardInterrupt:
            if s.chk_stat[1][0] == '0x1':
                s.iq_tgl; print '\nInterrupt off'
            exit()

print """
Finish frequency sweep readout.
Bye-Bye (^_^)/~
"""
