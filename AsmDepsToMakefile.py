#!/usr/bin/env python3

import os
from os import path

LWID = 44
LWID2 = 84

def width(string):
    n = 0
    for c in string:
        if c == '\t':
            n += 1
            while n % 4: n += 1
        else: n += 1
    return n

def quote(string):
    return '"' + string + '"'

import argparse

args = argparse.ArgumentParser(description='''
    For an MPW Assembler file, print an MPW Make line that declares its
    dependencies. Defines can be specified so that MPW path variables
    are produced.
''')
args.add_argument('defines', metavar='VARIABLE=PATH', action='store', nargs='*', help='Variable definition')
args.add_argument('source', metavar='ASM', action='store', help='Assembly file')
args = args.parse_args()
args.defines = [tuple(equ.split('=')) for equ in args.defines]


f = open(args.source, 'rb').read()
f = bytes(c for c in f if c < 128)
f = f.decode('ascii').replace('\r', '\n').split('\n')

incfiles = []
for line in f:
    try:
        starter = line.split()[0].lower()
        if starter in ['load', 'include']:
            incfile = line.split()[1].strip("'")
            incfiles.append(incfile)
    except IndexError:
        pass

incfiles.append(path.basename(args.source))

for i in range(len(incfiles)):
    orig = incfiles[i]
    if orig == 'StandardEqu.d':
        incfiles[i] = '{ObjDir}' + orig
        continue
    doneflag = False
    for k, v in args.defines:
        if path.exists(path.join(v, orig)):
            incfiles[i] = '{%s}%s' % (k, orig)
            doneflag = True
    if doneflag: continue

isfirst = True
for l in incfiles:
    if isfirst:
        line = quote('{ObjDir}' + path.basename(args.source) + '.o') + '\t'
        while width(line) < LWID-4: line += '\t'
        line += '\u0192\t'
    else:
        line = ''
    isfirst = False

    while width(line) < LWID: line += '\t'

    line += quote(l)

    if l != incfiles[-1]:
        while width(line) < LWID2: line += '\t'
        line += '\u2202'

    print(line)

print('\tAsm {StdAOpts} -o {Targ} ' + quote(incfiles[-1]))
