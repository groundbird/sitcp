#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import *
from contextlib import closing

def main():
#     host = socket.gethostname()
    host = 'ahiru.kek.jp'
    port = 14510
    buff = 1024
    user = 'Client'

    cs = socket(AF_INET, SOCK_STREAM)
    with closing(cs):
        cs.connect((host, port))
        while True:
            msg = raw_input('%s > ' % user)
            if not msg: break
            cs.send(msg)
            msg = cs.recv(buff)
            if not msg: break
            print msg

if __name__ == '__main__':
    main()
