#!/usr/bin/env python3

import unicodedata

col_widths = [7, 54, 20]
rows = [['MacRom', 'UTF-8 NFC', 'UTF-8 NFD']]
for i in range(256):
    rows.append(['[%02X]' % i])
    for form in ('NFC', 'NFD'):
        unistr = bytes([i]).decode('mac_roman')
        unistr = unicodedata.normalize(form, unistr)
        codepoints = []
        for cp in unistr:
            utf8hex = cp.encode('utf-8').hex().upper()
            name = unicodedata.name(cp, 'U+%04X' % ord(cp))
            codepoints.append(f'[{utf8hex}] {name}')
        rows[-1].append(' + '.join(codepoints))

for row in rows:
    accum = ''
    for wid, col in zip(col_widths, row):
        accum += (col + ' ').ljust(wid)
    accum = accum.rstrip()
    print(accum)
