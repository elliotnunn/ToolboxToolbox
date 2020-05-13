#!/usr/bin/env python3

# Patch the Apple C Compiler to output symbol-laden files unconditionally... without messing up the codegen!

from collections import Counter


def do_everything():
    # Essential Patches

    # Sets the "version" of the output file (to 3)
    force_value(2, 0x5048, 'OPENOBJECTFILE', 'move.b #gSymOn,d0')

    # Places Filename records
    force_value(1, 0x842, 'OPENNEWFILE', 'move.b #gSymOn,d0')

    # Apparently we crash without this
    force_value(26, 0x118, 'INITIALIZE', 'move.b #gSymOn,d0')

    # Inits something called the "file pos array"
    force_value(25, 0x63e6, 'INITPROC', 'move.b #gSymOn,d0')

    # Ooooh boy...
    # force_value(10, 0x4576, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    force_value(10, 0x47e6, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x4afe, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x4c62, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x4d8e, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x5116, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x51b8, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x52e6, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x5544, 'FUNCTIONDECL', 'move.b #gSymOn,d0')
    # force_value(10, 0x4e3c, 'FUNCTIONDECL', 'move.b #gSymVars,d0')
    # force_value(10, 0x4f56, 'FUNCTIONDECL', 'move.b #gSymVars,d0')
    # force_value(10, 0x5142, 'FUNCTIONDECL', 'move.b #gSymVars,d0')
    # force_value(10, 0x521a, 'FUNCTIONDECL', 'move.b #gSymVars,d0')
    # force_value(10, 0x538a, 'FUNCTIONDECL', 'move.b #gSymVars,d0')


    # One of these seems to annotate which files have been opened...
    # force_value(1, 0x48, 'SETSCANFILE', 'move.b #gSymOn,d0')

    # One of these is required for the first "ModuleBegin"... can safely skip, apparently!
    # force_value(1, 0x3fa2, 'PROG', 'move.b #gSymOn,d0')
    # force_value(1, 0x40fe, 'PROG', 'move.b #gSymOn,d0')
    # force_value(1, 0x4170, 'PROG', 'move.b #gSymVars,d0')
    # force_value(1, 0x4250, 'PROG', 'move.b #gSymVars,d0')
    # force_value(1, 0x486e, 'PROG', 'move.b #gSymOn,d0')


    # force_value(6, 0x258a, 'EXPANDMACRO', 'and.b #gSymOn,d0')
    # force_value(6, 0x441a, 'MACROLINE', 'move.b #gSymOn,d0')
    # force_value(6, 0x508a, 'LOADFILE', 'cmp.b #gSymOn,d0')
    # force_value(6, 0x5174, 'LOADFILE', 'move.b #gSymOn,d0')
    # force_value(6, 0x6416, 'DUMPFILE', 'move.b #gSymOn,-$2190(a6)')
    # force_value(6, 0x6720, 'DUMPFILE', 'move.b #gSymOn,d0')
    # force_value(7, 0x7d4, 'PROTOPARMLIST', 'move.b #gSymVars,d0')
    # force_value(7, 0x89a, 'PROTOPARMLIST', 'move.b #gSymOn,d0')
    # force_value(7, 0xa80, 'PROTOPARMLIST', 'move.b #gSymVars,d0')
    # force_value(7, 0xb16, 'PROTOPARMLIST', 'move.b #gSymOn,d0')


    # Not required...
    # force_value(7, 0x19f6, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x1d6e, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x1dec, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x2180, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x2296, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x2314, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x267a, 'DECLARATION', 'move.b #gSymOn,d0')
    # force_value(7, 0x27c8, 'DECLARATION', 'move.b #gSymOn,d0')

    #... skipped some because bored!


    # skipped some tedious "dumpfunction" symbols here!

    # force_value(25, 0x53d0, 'FORMATCODE', 'move.b #gSymOn,d0')
    # force_value(25, 0x53d8, 'FORMATCODE', 'move.b #gSymLines,d0')



def gappy_compare(actual_str, search_str):
    if len(actual_str) != len(search_str): return False

    for actual_el, search_el in zip(actual_str, search_str):
        if actual_el != search_el and search_el != 0x99: return False

    return True



def scan_back(cursor, binary, *search_strs):
    if cursor is None: cursor = len(binary)

    while cursor > 0:
        cursor -= 1

        for which, ss in enumerate(search_strs):
            if gappy_compare(binary[cursor:cursor+len(ss)], ss):
                return cursor, which

    return cursor, None



def bool_global_a5_offset_from_SETSYMDEBUGOPTION(code):
    # Count all the below opcodes, and the most common is accessing our desired global
    most_common = Counter()
    i = None
    while True:
        i, which = scan_back(i, code, b'\x1B\x7C\x00\x01\x99\x99') # MOVE.B #1,????(A5)
        if which != 0: break

        a5 = bytes(code[i+4:i+6])
        most_common[a5] += 1

    if most_common:
        most_common, freq = most_common.most_common(1)[0]
        return most_common


def patch_global_access_by_function(code, my_global):
    global_access = b'\x10\x2d' + my_global # MOVE.B my_global(A5),D0

    num_patches = 0
    i = None
    while True:
        if b'FUNCTIONDECL\0' in code:
            i, which = scan_back(i, code, b'\x3f\x3c\x00\x04\x2f\x2d\x99\x99\x4e\x99\x99\x99') # MOVE.W #4,-(SP); MOVE.L ????(A5),-(SP); JSR ??????)
            if which != 0: break

        i, which = scan_back(i, code, global_access) 
        if which != 0: break

        code[i:i+4] = b'\x10\x3c\x00\x01' # MOVE.B #1,D0
        num_patches += 1

    return num_patches


def find_functions(segment):
    offset = 0
    biglist = []
    while offset < len(segment):
        next_offset = segment.find(b'NV', offset + 1)
        if next_offset == -1: next_offset = len(segment)
        biglist.append((offset, segment[offset:next_offset]))
        offset = next_offset
    return biglist


def do_better(all_resources):
    segments = [r for r in all_resources if r.type == b'CODE' and r.id > 0]

    print('Patching C compiler to force some SADE symbols (selectively, without changing codegen)')

    a5glob = None
    for segment in segments:
        for offset, function in find_functions(segment):
            if b'SETSYMDEBUGOPTION\0' in function:
                a5glob = bool_global_a5_offset_from_SETSYMDEBUGOPTION(function)

    if a5glob is None:
        print('    Could not find the -sym global. Stopping.')
        return

    print(f'    Found the -sym global: {hex(struct.unpack(">h", a5glob)[0])}(A5)')

    for segment in segments:
        for offset, function in find_functions(segment):
            for fname in ['OPENOBJECTFILE', 'OPENNEWFILE', 'INITIALIZE', 'INITPROC', 'FUNCTIONDECL']:
                if fname.encode('ascii') + b'\0' in function:
                    num_patches = patch_global_access_by_function(function, a5glob)
                    if num_patches:
                        print(f'    Hardcoded to true: {fname} (seg {segment.id} {repr(segment.name)} + {hex(offset)}) x{num_patches}')
                    segment[offset:offset+len(function)] = function







import macresources
import re
import struct

target = '/Users/elliotnunn/Documents/mac/supermario/worktree/cube-e/Tools/C.rdump'

resources = list(macresources.parse_rez_code(open(target, 'rb').read()))

def force_value(in_segment, at_offset, in_func_name, code):
    known_globals = {'gSymLines': -0x1082, 'gSymTypes': -0x1081, 'gSymVars': -0x1080, 'gSymOn': -0x107f}

    for r in resources:
        if r.id == in_segment and r.type == b'CODE': break
    else:
        raise ValueError('bad segment %r' % in_segment)

    m = re.match(r'move.b #(\w+),d0', code)
    if not m:
        print('Could not match %r' % code)
        return

    if struct.unpack_from('>h', r, at_offset + 2)[0] != known_globals[m.group(1)]:
        print('Bad code %r %r %r %r' % (in_segment, at_offset, in_func_name, code))
        return

    struct.pack_into('>HH', r, at_offset, 0x103C, 1) # WE ARE FORCING THINGS ON!

# do_everything()

# find_a5_offset_of_boolean_global(resources)
do_better(resources)

open(target, 'wb').write(macresources.make_rez_code(resources, ascii_clean=True))
