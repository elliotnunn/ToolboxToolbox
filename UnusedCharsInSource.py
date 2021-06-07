#!/usr/bin/env python3

import os
from os import path

textfiles = []
for base, dirlist, filelist in os.walk('/Users/elliotnunn/Documents/mac/supermario/base/SuperMarioProj.1994-02-09'):
    dirlist = [d for d in dirlist if not d.startswith('.')]
    filelist = [f for f in filelist if not f.startswith('.')]

    for f in filelist:
        try:
            if open(path.join(base, f) + '.idump', 'rb').read(4) == b'TEXT':
                textfiles.append(path.join(base, f))
        except:
            pass

bigstring = b''
for tf in textfiles:
    bigstring += open(tf).read().encode('mac_roman')

for i in range(256):
    if i not in bigstring:
        print(f'{i:02x} {repr(bytes([i]).decode("mac_roman"))}')
