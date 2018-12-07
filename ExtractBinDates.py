#!/usr/bin/env python3

from datetime import datetime, timedelta
import argparse

def macdatestr(srcint):
	dt = datetime(1904, 1, 1) + timedelta(seconds=srcint)
	st = dt.isoformat()
	st = st.replace('T', ' ')
	return st

args = argparse.ArgumentParser()

args.add_argument('src',  nargs='+', help='Binary to extract build dates from')
args.add_argument('--all', action='store_true', help='Show every date, not just the latest one')

args = args.parse_args()

for binpath in args.src:
	thebin = open(binpath, 'rb').read()

	if args.all: print(binpath)

	maxdat = -1

	while b'Joy!peffpwpc' in thebin:
		thebin = thebin[thebin.index(b'Joy!peffpwpc') + 16:]
		dt = int.from_bytes(thebin[:4], byteorder='big')
		maxdat = max(maxdat, dt)

		if args.all: print(macdatestr(dt))

	if not args.all:
		suffix = ' [%s]' % binpath
		if maxdat == -1:
			print('???????????????????' + suffix)
		else:
			print(macdatestr(maxdat) + suffix)
