#!/usr/bin/env python3

import sys
import struct
from os import path
import re

biglist = []


def could_be_rom(lb):
    if not lb: return False
    if lb == 0x300000: return True # special supermario case!

    while not (lb & 1):
        lb >>= 1
    if lb != 1: return False

    return True


for rompath in sys.argv[1:]:
    try:
        if not could_be_rom(path.getsize(rompath)): continue
        rom = open(rompath, 'rb').read()
    except IsADirectoryError:
        continue

    info = []

    a, = struct.unpack_from('>H', rom, 8)
    b, = struct.unpack_from('>H', rom, 18)


    order = a << 64


    if a == 0x69:
        info.append('Original')
    elif a == 0x75:
        info.append('Plus')
    elif a == 0x178:
        info.append('II')
    elif a == 0x276:
        info.append('SE')
    elif a == 0x37a:
        info.append('Portable')
    elif a == 0x67c:
        info.append('IIci')
        if rom[18] == 0x15:
            order += 1 << 63
            info.append('TERROR')
        elif rom[18] == 0x17:
            order += 2 << 63
            info.append('Zydeco')
        elif rom[20] & 1:
            order += 3 << 63
            info.append('Horror')

    elif a == 0x77d:
        info.append('SuperMario')
    else:
        order = 0
        info.append('?-%X' % a)

    if a >= 0x300:
        info.append('Rel-%04x' % b)
        order += b << 32

    if a == 0x77d: # SuperMario
        info.append('SubVer-%x' % struct.unpack_from('>H', rom, 0x4c))
        order += struct.unpack_from('>H', rom, 0x4c)[0]


    if a == 0x67c:
        if b >= 0x12f1: info.append("EricksonSndMgr")
        if b == 0x12f1: info.append("EricksonMistake")

    if b'\x08.netBOOT' in rom:
        info.append('netBOOT')

    drvrs = re.finditer(rb'\x04\.MPP', rom)
    drvrs = [m.start() - 18 for m in drvrs] # the actual possible drvr starts
    for ofs in drvrs:
        if rom[ofs] == 0: continue
        if any(rom[ofs+1:ofs+8]): continue
        routine_offsets = struct.unpack_from('>HHHHH', rom, ofs+8)
        for ent in routine_offsets:
            if ent < 0x1a or ent % 2 != 0: break
        else:
            info.append('MPP=%d' % rom[ofs+24])

    biglist.append((order, ' '.join(info), rompath, rom))

biglist.sort()
wid = max(len(s) for _, s, *_ in biglist)

rom_paths = {}
for o, s, p, rom in biglist:
    rom_paths.setdefault(rom, [s]).append(p)

for rom, (s, *pp) in rom_paths.items():
    left = s.ljust(wid)
    for p in pp:
        print(left + '    ' + p)
        left = ' ' * wid
