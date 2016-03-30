#!/bin/bash

f=$1

python sweep.py -f $1e6 $1e6 -r && mv data/sweep_2015*.csv data/sweep_$1mhz.csv
