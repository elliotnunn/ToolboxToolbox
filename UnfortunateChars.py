#!/usr/bin/env/python3

for i in range(128, 256):
	print('%02x' % i, bytes([i]).decode('mac_roman').encode('utf-8').decode('mac_roman'))
