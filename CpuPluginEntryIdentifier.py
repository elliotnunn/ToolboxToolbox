#!/usr/bin/env python3

from pefbinary import PEF
from zcpcore import read_rsrc_path

# FIGURE OUT THE ENTRY POINTS IN A CPU PLUGIN!

# Paste in what the NanoKernel extruded under the influence of HackLogFirstSIGPs.

NK_OUTPUT = """
0 7c0802a6 90010008 9421ffc0 5463043e 480086d9 80410014 39820360 806c0748 38210040 
1 7c0802a6 bf41ffe8 90010008 9421ffb0 3bc20360 549f043e 57e7083c 7d07f214 547d043e 
2 7c0802a6 bfa1fff4 90010008 9421ffb0 3bc20360 549f043e 57e5083c 7cc5f214 5463043e 
3 7c0802a6 bf81fff0 90010008 9421ffb0 3b820360 549f043e 57e5083c 7cc5e214 547e043e 
4 7c0802a6 bf41ffe8 90010008 9421ffb0 3bc20360 549f043e 3b600001 57e5083c 3b400000 
5 7c0802a6 bfc1fff8 90010008 9421ffc0 3bc20360 549f043e 5463043e 480084bd 80410014 
6 7c0802a6 bfc1fff8 90010008 9421ffc0 83e2ffc4 549e043e 5463043e 48008239 80410014 
7 7c0802a6 bfc1fff8 90010008 9421ffc0 83e2ffc4 549e043e 5463043e 4800810d 80410014 
8 7c0802a6 bf41ffe8 90010008 9421ffb0 3bc20360 547c043e 837e074c 7f83e378 8bbe0f82 
9 7c0802a6 bf21ffe4 90010008 9421ffa0 3bc20360 547d043e 839e0b80 57bf083c 3b400000 
10 7c0802a6 bfc1fff8 90010008 9421ffc0 3bc20360 549f043e 5463043e 48007de1 80410014 
11 7c0802a6 90010008 9421ffc0 5463043e 48007d81 80410014 38210040 80010008 7c0803a6 
12 7c0802a6 bee1ffdc 90010008 9421ffa0 90a10080 90c10084 90e10088 9101008c 91210090 
13 7c0802a6 be61ffcc 90010008 9421ff90 83e2ffc4 547a043e 839f0b7c 3b000001 833f0b80 
14 456e7472 79000000 00000000 00000000 4e56ffe2 48e70718 266e0008 7005fe04 28484aae 
15 456e7472 79000000 00000000 00000000 4e56ffe2 48e70718 266e0008 7005fe04 28484aae 
16 7c0802a6 bf21ffe4 90010008 9421ffa0 90c10084 90e10088 9101008c 91210090 91410094 
17 7c0802a6 90010008 9421ffc0 5463043e 48006fd5 80410014 8062ffc4 38800007 48003409 
"""

# And this should be the PEF to search.
CPUP_PATH = '/Users/elliotnunn/Nosy/Victims/Extensions/Multiprocessing/Apple CPU Plugins//cpup/4/Core99Plugin/locked'

KNOWN_SELECTORS = {
	1: 'StartProcessor',
	3: 'StopProcessor',
	4: 'ResetProcessor',
	8: 'SynchClock',
}

whole_binary = read_rsrc_path(CPUP_PATH)
code_section = PEF(whole_binary).code

patchpef_args = []

for l in NK_OUTPUT.split('\n'):
	l = l.rstrip()
	if not l: continue
	n, _, hx = l.partition(' ')
	n = int(n)
	hx = bytes.fromhex(hx.replace(' ', ''))

	name = KNOWN_SELECTORS.get(n, 'UnknownSelector')
	name = '%s_%d' % (name, n)

	print('Selector %d:' % n, end='')

	loc = code_section.find(hx)
	if loc == -1:
		print(' not found')
		continue
	
	while loc != -1:
		patchpef_args.extend(['0x%X' % loc, ':'+name])
		print(' 0x%X' % loc, end='')
		loc = code_section.find(hx, loc+1)
	print()

if patchpef_args:
	print()
	print('Suggested patchpef arguments:')
	print(*patchpef_args)