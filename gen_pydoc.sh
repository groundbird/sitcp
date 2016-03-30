#!/bin/bash

DOCPATH='doc/'

# generate pydoc
pyfiles=('lib/slowCtrl.py' 'lib/readout.py')
for py in ${pyfiles[@]}; do
    py_tmp=${py%.*}
    pydoc -w $py && mv ${py_tmp##*/}.html $DOCPATH
done

# rsync ahiru
rsync -auv $DOCPATH ahiru:public_html/doc
