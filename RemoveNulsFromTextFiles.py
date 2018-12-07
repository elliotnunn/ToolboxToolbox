#!/usr/bin/env python3

import sys
import os
from os import path

the_dir = sys.argv[1]

def get_textfiles_from_dir(the_dir):
    textfiles = []
    for parent, dirs, files in os.walk(the_dir):
        for flnam in files:
            flnam = path.join(parent, flnam)
            try:
                if open(flnam + '.idump', 'rb').read(4) != b'TEXT':
                    continue
            except:
                continue
            textfiles.append(flnam)
    return textfiles

BADCHAR = b'\x00'

for f in get_textfiles_from_dir(the_dir):
    dat = open(f, 'rb').read()
    if BADCHAR in dat:
        print('Writing', f)
        open(f, 'wb').write(dat.replace(BADCHAR, b''))
