#!/usr/bin/env python3


import os
import struct
import sys


COMBO_FIELDS = {
    0x40: 'AppleTalk1',
    0x20: 'AppleTalk2',
    0x30: 'AppleTalk2_NetBoot_FPU',
    0x08: 'AppleTalk2_NetBoot_NoFPU',
    0x10: 'NetBoot',
    0x78: 'AllCombos',
}


def pad_offset(offset, align):
    (offset + align - 1) & ~(align - 1)


class Rsrc:
    def __init__(self, rom_bin, struct_offset):
        self.struct_offset = struct_offset

        rsrc_s_fmt = '> B 7x L L 4s h c 256p' # Struct actually padded to 16b to fit pstring
        rsrc_s_len = struct.calcsize(rsrc_s_fmt)
        rsrc_s = rom_bin[self.struct_offset : self.struct_offset + rsrc_s_len]
        rsrc_s_tuple = struct.unpack(rsrc_s_fmt, rsrc_s)

        (self.combo_field,
        self.next_offset, self.data_offset,
        self.type, self.id,
        attrs, self.name)        = rsrc_s_tuple

        self.combo_field = COMBO_FIELDS.get(self.combo_field, 'UnknownComboField0x%X'%self.combo_field)

        rsrc_s_len_actual = pad_offset(rsrc_s_len - 256 + len(self.name), 16)

        mm_header_fmt = '> L L L'
        mm_header_len = struct.calcsize(mm_header_fmt)
        mm_header = rom_bin[self.data_offset - mm_header_len : self.data_offset]
        mm_header_tuple = struct.unpack(mm_header_fmt, mm_header)

        (mm_attrs, block_len, mm_bogus_ptr_ptr) = mm_header_tuple

        self.data = rom_bin[self.data_offset : self.data_offset + block_len - mm_header_len]


if __name__ == '__main__':
    try:
        _, src, dest = sys.argv
    except ValueError:
        print('USAGE: %s SRC.ROM DEST-DIR' % (sys.argv[0]))
        exit(1)

    with open(src, 'rb') as f:
        rom_bin = f.read()

    os.makedirs(dest)

    (map_offset,) = struct.unpack('>L', rom_bin[0x1A : 0x1A + 4])

    map_s_fmt = '>Lbbhh'
    map_s_len = struct.calcsize(map_s_fmt)
    map_s = rom_bin[map_offset:map_offset + map_s_len]
    (offsetToFirst, maxValidIndex, comboFieldSize, comboVersion, headerSize) = struct.unpack(map_s_fmt, map_s)

    next_offset = offsetToFirst
    idx = 0
    while next_offset != 0:
        r = Rsrc(rom_bin, next_offset)

        fname = '%03d %s %d' % (idx, r.type.decode('ascii'), r.id)
        if r.name:
            fname += ' "%s"' % r.name.decode('ascii')
        if r.combo_field != 'AllCombos':
            fname += ' (%s)' % r.combo_field
        fname = fname.replace('/', '-')

        with open(os.path.join(dest, fname), 'wb') as f:
            f.write(r.data)

        next_offset = r.next_offset
        idx += 1
