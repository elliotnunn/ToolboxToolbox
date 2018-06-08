#!/usr/bin/env python3

from sys import argv

# USAGE: KernelExtractor.py DESTDIR ROM1 [ROM2 ...]

kerns = {}

for fname in argv[2:]:
	print(fname)
	with open(fname, 'rb') as f:
		b = f.read()
	if len(b) != 0x400000: print('--- bad size')
	b = b[0x310000:]
	l = b.index(bytes(1024))
	l += 3
	l -= l % 4
	b = b[:l]
	if not b:
		print('--- no kernel')
		continue
	vers = '%02x%02x' % tuple(b[4:6])
	if not vers.startswith('02'): continue
	print('---', vers)
	if vers in kerns:
		if kerns[vers] != b:
			print('--- bad motivator')
			kerns[vers] = None
	else:
		kerns[vers] = b

for v, k in kerns.items():
	if k is None: continue
	with open(argv[1] + v, 'wb') as f:
		f.write(k)
