#!/usr/bin/env python3

# this is a monstrous program!

import macresources
import shlex
import tempfile

returns = []

import sys

for f in sys.argv[1:]:
    try:
        a, _, b = f.partition('//')

        rtype, _, rid = b.partition('/')
        rtype = rtype.encode('mac_roman')
        rid = int(rid)

        rsrc = open(a, 'rb').read()
        rsrc = macresources.parse_rez_code(rsrc)
        rsrc = next(r for r in rsrc if r.type == rtype and r.id == rid)

        name = '-%s-%s-%d' % (a.split('/')[-1], rtype.decode('mac_roman'), rid)
        handle, name = tempfile.mkstemp(dir='/tmp', suffix=name)

        open(name, 'wb').write(rsrc.data)
        returns.append(name)

    except:
        returns.append(f)

if returns:
    print(' '.join(shlex.quote(x) for x in returns))
