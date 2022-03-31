#!/usr/bin/env python3

import argparse
import macresources
import sys
import struct
import string


OKCHARS = string.ascii_letters + string.digits + "_%"


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

jump_table = {}  # a5_ofs: (segnum, seg_ofs)
(jt_size, a5_offset_of_jt) = struct.unpack_from(">LL", jt_resource, 8)

thirtytwo = False

for jt_ofs in range(16, 16 + jt_size, 8):
    if jt_resource[jt_ofs : jt_ofs + 8] == b"\x00\x00\xff\xff\x00\x00\x00\x00":
        thirtytwo = True
        continue

    if thirtytwo:
        segnum, be_a9f0, ofs = struct.unpack_from(">HHL", jt_resource, jt_ofs)

        if be_a9f0 != 0xA9F0:
            raise ValueError("32-bit jt")

        jump_table[jt_ofs - 16 + a5_offset_of_jt + 2] = (segnum, ofs)

    else:
        ofs, be_3f3c, segnum, be_a9f0 = struct.unpack_from(">HHHH", jt_resource, jt_ofs)

        if be_3f3c != 0x3F3C or be_a9f0 != 0xA9F0:
            raise ValueError("16-bit jt")

        jump_table[jt_ofs - 16 + a5_offset_of_jt + 2] = (segnum, ofs)


# From https://github.com/elliotnunn/mps/blob/master/stacktrace.go
def macsbug_syms(blob):
    bigmv = memoryview(blob)

    for i in range(0, len(blob) - 2, 2):
        try:
            mv = bigmv[i:]
            # RTS or JMP(A0)
            if mv[:2] == b"\x4e\x75" or mv[:2] == b"\x4e\xd0":
                j = i + 2

            # RTD #<word>
            elif mv[:3] == b"\x4e\x74\x00":
                j = i + 4

            # Not the end of a procedure
            else:
                continue

            mv = bigmv[j:]
            # "Old style" MacsBug symbol format
            # Haven't done the MacApp format
            if 0x20 <= mv[0] & 0x7F <= 0x7F and 0x20 <= mv[1] <= 0x7F:
                k = j + 1
                ln = 8

            # Apple Compiler symbol
            elif mv[0] == 0x80 and mv[1] != 0:
                k = j + 2
                ln = mv[1]

            # Apple Compiler symbol
            elif 0x81 <= mv[0] <= 0x9F:
                k = j + 1
                ln = mv[0] & 0x7F

            # No MacsBug string
            else:
                continue

            s = bytes(bigmv[k : k + ln])
            # Sanitise the string
            if is_mxbg_str(s):
                yield i, k, s.decode("ascii")

        except IndexError:
            pass


def is_mxbg_str(s):
    for c in s:
        if not ((ord("a") <= c <= ord("z")) or (ord("A") <= c <= ord("Z")) or (ord("0") <= c <= ord("9")) or c in (ord(" "), ord("%"), ord("_"))):
            return False
    return True


def unpack_relocs(blob):
    # blob = memoryview(blob)
    while True:
        if blob[:2] == b"\x00\x00":
            break

        elif blob[0] == 0 and blob[1] & 0x80:
            yield ((blob[1] << 25) + (blob[2] << 17) + (blob[3] << 9) + (blob[4] << 1)) & 0xFFFFFFFF
            blob = blob[5:]

        elif blob[0] & 0x80:
            yield ((blob[0] << 9) + (blob[1] << 1)) & 0xFFFF
            blob = blob[2:]

        else:
            yield blob[0] << 1
            blob = blob[1:]


with open(args.dest + ".py", "w") as idascript:
    # Find MacsBug symbols
    namedict = {}
    for r in other_resources:
        targets = set(ofs for seg, ofs in jump_table.values() if seg == r.id)

        for rtsoffset, stringoffset, name in macsbug_syms(r):
            print(f"idaapi.make_ascii_string({addr(r.id)+stringoffset:#X}, {(len(name)+2)&~1}, ASCSTR_C)", file=idascript)
            print(f"set_cmt({addr(r.id)+stringoffset:#X}, 'MacsBug symbol', 0)", file=idascript)

            for funcoffset in reversed(range(0, rtsoffset, 2)):
                inst = bytes(r[funcoffset : funcoffset + 2])
                if inst in (b"\x4E\x75", b"\x4E\x74", b"\x4E\xD0"):
                    break  # encountered a func-end

                if funcoffset in targets or inst == b"NV":
                    namedict[addr(r.id) + funcoffset] = name
                    break

    interseg_calls = {}
    for r in other_resources:
        # 32-bit segment
        if r[:2] == b"\xFF\xFF":
            a5relocs, pcrelocs = struct.unpack_from(">LxxxxL", r, 0x14)

            ofs = 0
            for reloc in unpack_relocs(r[a5relocs:]):
                ofs = (ofs + reloc) & 0xFFFFFFFF  # reloc can be negative!
                (a5offset,) = struct.unpack_from(">L", r, ofs)

                # Instead of hacking IDA to treat xxxx(A5) as a function address,
                # just stuff the actual function address in the JMP target
                if a5offset in jump_table:
                    target_seg, target_seg_offset = jump_table[a5offset]
                    target_addr = addr(target_seg) + target_seg_offset
                    struct.pack_into(">L", r, ofs, target_addr)

            ofs = 0
            for reloc in unpack_relocs(r[pcrelocs:]):
                ofs = (ofs + reloc) & 0xFFFFFFFF  # reloc can be negative!

                (target_addr,) = struct.unpack_from(">L", r, ofs)
                target_addr += addr(r.id)
                struct.pack_into(">L", r, ofs, target_addr)

        # 16-bit segment
        else:
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

    for a5_ofs, (segnum, ofs) in jump_table.items():
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

bigboy = bytearray()
for r in other_resources:
    bigboy.extend(bytes(addr(r.id) - len(bigboy)))
    bigboy.extend(r)

with open(args.dest, "wb") as f:
    f.write(bigboy)
