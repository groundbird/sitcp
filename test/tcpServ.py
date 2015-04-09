#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import *
from time import ctime
from contextlib import closing

def main():
    # host = gethostname()
    host = 'ahiru.kek.jp'
    port = 14510
    buff = 1024
    user = 'Server'

    ss = socket(AF_INET, SOCK_STREAM)
    with closing(ss):
        ss.bind((host, port))
        ss.listen(5)
        print '(hostname, port) = (%s, %s)' % (host, port)
        while True:
            print 'Waiting for connection...'
            cs, adrr = ss.accept()
            with closing(cs):
                print 'Connected from', adrr
                while True:
                    msg = cs.recv(buff)
                    if not msg: break
                    print '%s [%s] > %s' % (adrr[0], ctime(), msg)
                    cs.send('echo back: %s [%s] > %s' % (user, ctime(), msg))

if __name__ == '__main__':
    main()
