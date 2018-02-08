#!/usr/bin/env python3

from sys import argv, stderr
import struct

CR = '\r'

ROMSIZE = 0x400000
EMBASE = 0x360000

try:
    rom_path, = argv[1:]

    with open(rom_path, 'rb') as f:
        rom = f.read(ROMSIZE)

    if len(rom) != ROMSIZE:
        raise ValueError

except:
    print('USAGE: %s ROM > ASM.s' % argv[0], file=stderr)
    print('       empw PPCAsm -o Emulator.x ASM.s', file=stderr)
    exit(1)

# read special offsets into emulator, from ConfigInfo struct
em_entry, em_kernel_trap_table = struct.unpack_from('>LL', rom, 0x30d080)

labels = {
    EMBASE: ['EmTop'],
    0x380000: ['EmBtm', 'OpcodeTblTop'],
    ROMSIZE: ['OpcodeTblBtm'],
    EMBASE + em_entry: ['EmEntry'],
    EMBASE + em_kernel_trap_table: ['EmKernelTrapTable'],
}

for k, vs in sorted(labels.items()):
    for v in vs:
        print('\texport\t%s\t; %x' % (v, k), end=CR)
print(end=CR)

for o in range(EMBASE, ROMSIZE+4, 4):
    try:
        lbls = labels[o]
    except KeyError:
        pass
    else:
        for lbl in lbls:
            print(lbl + ':', end=CR)

    if o == ROMSIZE:
        break

    print('\tdc.l\t$%02x%02x%02x%02x\t; %x' % (rom[o], rom[o+1], rom[o+2], rom[o+3], o), end=CR)
