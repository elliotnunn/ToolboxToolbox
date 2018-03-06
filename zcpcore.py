#!/usr/bin/env python3

from subprocess import run, PIPE
from sys import argv
import tempfile

def read_rsrc_path(path):
    BADCHARS = b'\t$" '

    if '//' not in path:
        with open(path, 'rb') as f:
            return f.read()

    else:
        path, _, rest = path.partition('//')

        rtype, rid, *_ = rest.split('/')

        try:
            int(rid)
        except ValueError:
            rid = '"%s"' % rid

        type_expr = '\'%s\' (%s)' % (rtype, rid)

        rez_code = run(['DeRez', '-only', type_expr, path], stdout=PIPE, check=True).stdout

        if len(rez_code) < 2:
            raise FileNotFoundError

        accum = bytearray()

        for l in rez_code.split(b'\n'):
            if len(l) >= 6 and l[1:2] == b'$':
                hx = l[:43].lstrip(BADCHARS).rstrip(BADCHARS)
                accum.extend(bytes.fromhex(hx.decode('ascii')))

        return bytes(accum)

def write_rsrc_path(path, data):
    STEP = 32

    if '//' not in path:
        with open(path, 'wb') as f:
            f.write(data)

    else:
        path, _, rest = path.partition('//')

        rtype, rid, *args = rest.split('/')
        if args:
            rname = ', "%s"' % args[0]
            args = args[1:]
        else:
            rname = ""
        rid = int(rid)

        args = ''.join(', %s' % x for x in args)


        with tempfile.NamedTemporaryFile(mode='w') as f:
            print('data \'%s\' (%d%s%s) {\n' % (rtype, rid, rname, args), file=f)

            for o in range(0, len(data), STEP):
                chunk = data[o:o+STEP].hex()
                print('\t$"%s"' % chunk, file=f)

            print('};', file=f)

            f.flush()

            run(['Rez', '-a', '-o', path, f.name], check=True)
