#!/usr/bin/env python3

import sys
from collections import defaultdict
from os.path import split, join

klist = []
for x in sys.argv[1:]:
    try:
        y = open(x, 'rb').read()
        if len(y) != 0x400000: raise ValueError
    except:
        continue

    y = y[0x310000:]
    y = y[:y.index(bytes(256))]
    while len(y) % 4: y += bytes(1)

    klist.append((x, y))

kseries = defaultdict(list)
for x, y in klist:
    kseries[y].append(x)

flg = False
for kerndata, owners in kseries.items():
    if flg: print()
    flg = True
    for o in owners: print(o)

    a, b = split(owners[0])
    dest = join(a, 'NK-'+b)
    open(dest, 'wb').write(kerndata)
