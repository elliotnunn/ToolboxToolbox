#!/usr/bin/env python3

import argparse
import macresources
import sys
import struct
import string


OKCHARS = string.ascii_letters + string.digits + "_"


def addr(seg):
    return 0x100000 * seg


parser = argparse.ArgumentParser()
parser.add_argument("src", help="rdump file")
parser.add_argument("dest", help="binary dest (may also create .txt file)")
args = parser.parse_args()

with open(args.src, "rb") as f:
    d = f.read()
    if f.name.endswith(".rdump"):
        resources = list(macresources.parse_rez_code(d, original_file=f.name))
    else:
        resources = list(macresources.parse_file(d))

resources = [r for r in resources if r.type == b"CODE" and r.id >= 0]
resources.sort(key=lambda r: r.id)

if not resources or resources[0].id != 0:
    sys.exit("CODE 0 not found in %s" % args.src)

jt_resource, *other_resources = resources

bigboy = bytearray()
for r in other_resources:
    bigboy.extend(bytes(addr(r.id) - len(bigboy)))
    bigboy.extend(r)

with open(args.dest, "wb") as f:
    f.write(bigboy)

jump_table = []  # (a5_ofs, segnum, seg_ofs)
(jt_size, a5_offset_of_jt) = struct.unpack_from(">LL", jt_resource, 8)
for jt_ofs in range(16, 16 + jt_size, 8):
    ofs, be_3f3c, segnum, be_a9f0 = struct.unpack_from(">HHHH", jt_resource, jt_ofs)
    if be_3f3c != 0x3F3C or be_a9f0 != 0xA9F0:
        break
    jump_table.append((jt_ofs - 16 + a5_offset_of_jt + 2, segnum, ofs + 4))


with open(args.dest + ".py", "w") as idascript:
    # Find MacsBug symbols
    namedict = {}
    for r in other_resources:
        targets = set(ofs for _, seg, ofs in jump_table if seg == r.id)

        bugnames = []
        lastfound = 0
        for i in range(0, len(r) - 2, 2):
            namelen = r[i + 2]
            if r[i : i + 2] not in (b"\x4e\x75", b"\x4e\xd0"):
                continue
            if not (0x81 <= namelen < 0xB0):
                continue
            namelen &= 0x3F
            if i + 3 + namelen > len(r):
                continue
            name = r[i + 3 : i + 3 + namelen].decode("latin-1")
            if not all(c in OKCHARS for c in name):
                continue

            possibles = []
            for j in reversed(range(lastfound, i, 2)):
                if r[j : j + 2] == b"Nu":
                    break  # stop looking after an RTS
                if r[j : j + 2] == b"NV" or j in targets:
                    possibles.append(j)

            lastfound = i

            if len(possibles) > 3:
                continue  # don't bother with this name, too ambiguous

            for j, p in enumerate(possibles, 1):
                namedict[addr(r.id) + p] = name if len(possibles) == 1 else f"{name}?{j}"

    interseg_calls = {}
    for r in other_resources:
        for i in range(0, len(r) - 3, 2):
            if r[i : i + 2] in (b"\x4e\xad", b"\x48\x6d") or (r[i] == 0x41 and r[i + 1] & 0xF8 == 0xE8):
                (targ,) = struct.unpack_from(">h", r, i + 2)
                if targ > 0:
                    interseg_calls.setdefault(targ, []).append(addr(r.id) + i)

    # Make some neat names for the segments...
    segnames = {}
    for r in other_resources:
        if r.name:
            segnames[r.id] = "".join(c for c in r.name if c in (string.ascii_letters + string.digits))
        else:
            segnames[r.id] = f"seg_{r.id:X}"

    for a5_ofs, segnum, ofs in jump_table:
        bigboy_ofs = addr(segnum) + ofs

        cool_name = f"{segnames[segnum]}$"
        if bigboy_ofs in namedict:
            cool_name += namedict[bigboy_ofs]
            del namedict[bigboy_ofs]
        else:
            cool_name += f"{bigboy_ofs:X}"

        print(f'MakeFunction(0x{bigboy_ofs:X}); MakeName(0x{bigboy_ofs:X}, "{cool_name}")', file=idascript)

        for caller in interseg_calls.get(a5_ofs, []):
            print(f'MakeCode(0x{caller:X}); op_man(0x{caller:X}, 0, "{cool_name}")', file=idascript)

    for bigboy_ofs, name in sorted(namedict.items()):
        cool_name = f"{segnames[bigboy_ofs >> 20]}${name}"
        print(f'MakeFunction(0x{bigboy_ofs:X}); MakeName(0x{bigboy_ofs:X}, "{cool_name}")', file=idascript)
