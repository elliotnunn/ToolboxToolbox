#!/usr/bin/env python3

# MacOS apps, extensions etc often keep their PEF (Portable Executable
# Format) binaries (also called Code Fragments) in the data fork, with
# offsets in a 'cfrg' resource in the resource fork. This scheme allows
# the Code Fragment Manager to map that file directly into memory (when VM
# is on) instead of using the Resource Manager to load it into a Memory
# Manager heap. But when multiple PEFs are concatenated into the DF,
# patchpef (https://github.com/elliotnunn/patchpef) cannot be used to
# mangle them. This script moves the PEFs to 'ndrv' resources (type
# doesn't really matter) and updates the 'cfrg' accordingly. The original
# PEFs are zeroed out in the data fork, so if everything has gone
# correctly, the data fork should be all zeroes.

# USAGE: MovePEFsToResources.py SRCFILE DESTFILE

from sys import argv
from subprocess import run

oln, fn = argv[1:]

run(['rm', '-f', fn])
run(['cp', oln, fn])

with open(fn, 'rb') as f:
	df = bytearray(f.read())

run(['zcp', fn+'//cfrg/0', '/tmp/mycfrg'])

with open('/tmp/mycfrg', 'rb') as f:
	cfrg = bytearray(f.read())

pwpc_locs = []
start = 0
while True:
	found = cfrg.find(b'pwpc', start)
	if found == -1: break
	pwpc_locs.append(found)
	start = found + 4

for i, p in enumerate(pwpc_locs):
	where = cfrg[p+0x14+3]
	if where != 1: continue

	rsrcnum = i+13000
	
	start = int.from_bytes(cfrg[p+0x18:p+0x1c], 'big')
	size = int.from_bytes(cfrg[p+0x1c:p+0x20], 'big')
	nlen = cfrg[p+0x2a]
	name = cfrg[p+0x2b:p+0x2b+nlen].decode('ascii')

	pef = df[start:start+size]

	with open('/tmp/thispef', 'wb') as f:
		f.write(pef)

	run(['zcp', '/tmp/thispef', '%s//ndrv/%d/%s/sysheap/locked' % (fn, rsrcnum, name)])

	df[start:start+size] = bytes(size)

	cfrg[p+0x14+3] = 2
	cfrg[p+0x18:p+0x1c] = b'ndrv'
	cfrg[p+0x1c:p+0x20] = rsrcnum.to_bytes(4, 'big', signed=True)

with open(fn, 'wb') as f:
	f.write(df)

with open('/tmp/mycfrg', 'wb') as f:
	f.write(cfrg)

run(['zcp', '/tmp/mycfrg', fn+'//cfrg/0'])
