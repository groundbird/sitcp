#!/bin/bash

DOCPATH='doc/'
pyfiles=('lib/slowCtrl.py' 'lib/readout.py')

for py in ${pyfiles[@]}; do
    py_tmp=${py%.*}
    pydoc -w $py && mv ${py_tmp##*/}.html $DOCPATH
done
