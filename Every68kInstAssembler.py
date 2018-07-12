#!/usr/bin/env python3

import struct
from sys import argv

class MPWObject:
    def __init__(self):
        self._list = []
        self._dict = []
        self._backdict = {}
        self._dict_idx = 200

    def __bytes__(self):
        dest = bytearray()

        for chunk in self._list:
            dest.extend(chunk)
            if len(dest) & 1: dest.append(0)

        return bytes(dest)

    def _ensurename(self, name):
        # get the ID of this name from the dict
        # If nonexistent, then add it
        # i.e. idempotent

        try:
            return self._backdict[name]
        except KeyError:
            self.putdict([name])
            return self._backdict[name]

    def _quickappend(self, *bytelist):
        self._list.append(bytes(bytelist))

    def putfirst(self):
        self._quickappend(1, 1, 0, 2)

    def putlast(self):
        self._quickappend(2, 0)

    def putdict(self, items):
        dest = bytearray()

        dest.extend([4, 0, 99, 99])
        dest.extend(struct.pack('>H', self._dict_idx))

        flag = False

        for item in items:
            flag = True
            dest.append(len(item))
            dest.extend(item.encode('ascii'))

            self._backdict[item] = self._dict_idx

            self._dict_idx += 1 # ID of the *next* thing

        if not flag: return

        struct.pack_into('>H', dest, 2, len(dest))
        
        self._list.append(dest)

    def putmod(self, name='#0001', segname='Main', flags=(1<<7)+(1<<3)):
        modid = self._ensurename(name)
        segid = self._ensurename(segname)
        self._last_mod_id = modid

        self._list.append(struct.pack('>BBHH', 5, flags, modid, segid))

    def putentry(self, offset, name):
        entid = self._ensurename(name)

        self._list.append(struct.pack('>BBHL', 6, 1<<3, entid, offset))

    def putsize(self, size):
        self._list.append(struct.pack('>BBL', 7, 0, size))

    def putcontents(self, data): # in multiple chunks please!
        done = 0

        while done < len(data):
            this_time = data[done:done+30000]

            header = struct.pack('>BBHL', 8, 1<<3, 8 + len(this_time), done)

            self._list.append(header + this_time)

            done += len(this_time)

    def putcomment(self, cmt):
        cmt = cmt.replace('\n','\r').encode('mac_roman')
        if len(cmt) & 1: cmt += b' '

        dest = bytearray()
        dest.extend([3, 0])
        dest.extend(struct.pack('>H', len(cmt) + 4))
        dest.extend(cmt)

        self._list.append(dest)

    def putsimpleref(self, targname, width, *offsets):
        offsets = list(offsets)

        if width == 2: # of the operand field, in bytes
            flags = 1 << 4
        elif width == 4:
            flags = 0

        flags |= 1<<3 # longwords in the offset list!

        targid = self._ensurename(targname)

        dest = struct.pack('>BBHH', 9, flags, 6 + 4 * len(offsets), targid)
        dest += b''.join(struct.pack('>L', o) for o in offsets)

        self._list.append(dest)

    def putweirdref(self, targname, width, *offsets):
        # Assumes that you've already put -offset at offset
        offsets = list(offsets)

        if width == 1:
            flags = 2 << 4
        elif width == 2: # of the operand field, in bytes
            flags = 1 << 4
        elif width == 4:
            flags = 0 << 4

        flags |= 1<<7 # difference calculation
        # flags |= 1<<3 # longwords in the offset list!

        targid = self._ensurename(targname)

        dest = struct.pack('>BBHHH', 10, flags, 8 + 2 * len(offsets), targid, self._last_mod_id)
        dest += b''.join(struct.pack('>H', o) for o in offsets)

        self._list.append(dest)




# included my own copy of mpwobj!

o = MPWObject()

o.putfirst()

for i in range(65536):
    b = struct.pack('>H16b', i, *range(16))

    o.putmod(name='#xxxx')
    o.putcontents(b)

    b = struct.pack('>H16b', i, *range(1, 17))

    o.putmod(name='#xxxx')
    o.putcontents(b)

o.putlast()

if argv[1:]:
    with open(argv[1], 'wb') as f:
        f.write(bytes(o))

