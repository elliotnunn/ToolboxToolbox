#!/usr/bin/env python3

import sys

files = sys.argv[1:]

for i in range(len(files)):
    files[i] = open(files[i], 'rb').read()

b = files[0]
for f in files[1:]:
    m = 0
    maxlen = max(len(b), len(f))
    minlen = min(len(b), len(f))
    for i in range(minlen):
        if b[i] == f[i]: m += 1
    try:
        print(100 * m // maxlen)
    except ZeroDivisionError:
        print('-')
