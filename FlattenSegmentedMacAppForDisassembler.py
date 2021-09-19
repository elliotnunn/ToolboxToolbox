#!/usr/bin/env python3

import argparse
import macresources
import sys
import struct
import string


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
for i, r in enumerate(resources):
    while len(bigboy) < i * 0x10000:
        bigboy.append(0)
    bigboy.extend(r)

with open(args.dest, "wb") as f:
    f.write(bigboy)

with open(args.dest + ".py", "w") as idascript:
    # Find MacsBug symbols
    namedict = {}
    for b in range(0, len(bigboy), 2):
        if bigboy[b : b + 2] == b"NV":  # link a6, starting a compiled function
            for c in range(b + 2, len(bigboy), 2):
                if bigboy[c : c + 2] == b"NV":
                    break
                if 0x81 <= bigboy[c] < 0xB0:
                    strlen = bigboy[c] & 0x0F
                    if strlen < 2:
                        break
                    namestr = bigboy[c + 1 : c + 1 + strlen]
                    if len(namestr) < strlen:
                        break
                    namestr = namestr.decode("latin-1")
                    if not all(c in (string.ascii_letters + string.digits + "_") for c in namestr):
                        break
                    if strlen % 2 == 0 and bigboy[c + 1 + strlen : c + 1 + strlen + 1] not in b"\0":
                        break

                    namedict[b] = namestr
                    break

    # Make some neat names for the segments...
    segnames = {}
    for r in other_resources:
        if r.name:
            segnames[r.id] = "".join(c for c in r.name if c in (string.ascii_letters + string.digits))
        else:
            segnames[r.id] = f"seg_{r.id:X}"

    jt_size, a5_offset_of_jt = struct.unpack_from(">LL", jt_resource, 8)

    for jt_ofs in range(16, 16 + jt_size, 8):
        ofs, be_3f3c, segnum, be_a9f0 = struct.unpack_from(">HHHH", jt_resource, jt_ofs)
        if be_3f3c != 0x3F3C or be_a9f0 != 0xA9F0:
            break
        ofs += 4  # not sure what the leading stuff is?

        bigboy_ofs = ((segnum) * 0x10000) + ofs
        a5_ofs = jt_ofs - 16 + a5_offset_of_jt + 2

        cool_name = f"{segnames[segnum]}_"
        if bigboy_ofs in namedict:
            cool_name += namedict[bigboy_ofs]
            del namedict[bigboy_ofs]
        else:
            cool_name += f"{bigboy_ofs:X}"

        print(f'MakeFunction(0x{bigboy_ofs:X}); MakeName(0x{bigboy_ofs:X}, "{cool_name}")', file=idascript)

        call_to_me = struct.pack(">H", a5_ofs)
        bb_i = -1
        while 1:
            bb_i = bigboy.find(call_to_me, bb_i + 1)
            if bb_i == -1:
                break
            if bb_i % 2:
                continue
            if bigboy[bb_i - 2 : bb_i] not in (b"\x4e\xad", b"\x48\x6d"):
                continue  # jsr/pea

            # Okay, found one
            print(f'MakeCode(0x{bb_i-2:X}); op_man(0x{bb_i-2:X}, 0, "{cool_name}")', file=idascript)

    for bigboy_ofs, name in sorted(namedict.items()):
        cool_name = f"{segnames[bigboy_ofs >> 16]}_{name}"
        print(f'MakeFunction(0x{bigboy_ofs:X}); MakeName(0x{bigboy_ofs:X}, "{cool_name}")', file=idascript)
