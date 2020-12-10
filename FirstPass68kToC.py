#!/usr/bin/env python3


# Pipe the output of MPW DumpObj into this script (never mind line endings).
# The output will be a good template for decompiling MPW C code by hand.


# Copyright (c) 2020 Elliot Nunn

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
import re
lines = sys.stdin.read().replace('\r', '\n').split('\n')

def match(*args, **kwargs):
    global m
    m = re.match(*args, **kwargs)
    return m

def search(*args, **kwargs):
    global m
    m = re.search(*args, **kwargs)
    return m


def gethex(s):
    try:
        return int(s.replace('$', '').replace('#', '').replace('0x', ''), 16)
    except:
        raise ValueError('%r not hexable' % s)


name = 'NONAME'
firstline = -1

procedures = []
for i, l in enumerate(lines):
    if search(r'Module="(\w+)"', l): name = m.group(1)

    if search(r'LINK.W +A6', l):
        firstline = i
        leading_chars = m.start()

    if firstline != -1 and match(r'^(\w+):', l) and not match(r'^[0-9A-Fa-f]+$', m.group(1)):
        name = 'NONAME'
        firstline = -1
        continue

    if search(r'\b(RTS|RTD|JMP +\(A0\))\b', l):
        lastline = i
        if name != 'NONAME' and firstline != -1:
            procedures.append((name, firstline, lastline))
        name = 'NONAME'
        firstline = -1

for name, firstline, lastline in procedures:
    data = b''
    for l in lines[lastline+1:]:
        if search(r'LINK.W +A6', l): break
        if not search(r':((?: [0-9A-Fa-f]{4})+) ', l): break
        data += bytes.fromhex(m.group(1))


    proc_offset = int(lines[firstline][:8], 16)
    data_offset = int(lines[lastline][:8], 16) + 2
    if 'RTD' in lines[lastline]: data_offset += 2 # ugly way to figure out where data goes


    for i in range(firstline, lastline+1):
        lines[i] = lines[i][:leading_chars] + lines[i][leading_chars:].partition(';')[0].rstrip()
        lines[i]

    statements = ''
    for i in range(firstline, lastline+1):
        if lines[i][8:9] != ':': continue
        offset = int(lines[i][:8], 16)
        opcode = lines[i][leading_chars:]
        opcode, _, rest = opcode.partition(' ')
        if rest:
            rest = rest.strip()

        rest = re.sub(r'\*[\-\+]\$[0-9A-Fa-f]+', lambda m: 'label_%X' % (int(m.group()[1:].replace('$', ''), 16) + offset), rest)

        statements += 'label_%X:' % offset

        if rest:
            statements += opcode + ' ' + rest + ';'
        else:
            statements += opcode + ';'


    # Now we have a clean statement list that we can do transformations on.


    # Transformation: A7 to SP
    statements = re.sub(r'(?<!\$)\bA7\b', 'SP', statements)



    # Transformation: get rid of unused labels
    def label_if_nonunique(m):
        if len(re.findall(r'\b' + m.group()[:-1] + r'\b', statements)) > 1:
            return m.group()
        else:
            return ''

    statements = re.sub(r'\blabel_[0-9A-Fa-f]+:', label_if_nonunique, statements)



    # Transformation: split the A6 stack frame into variables
    a6_size = -gethex(re.search(r'LINK.W A6,#(-?\$\w\w\w\w)', statements).group(1))
    a6_splits = {0, a6_size}

    def a6_sub(m):
        this_split = int(m.group(1), 16)
        if this_split <= a6_size:
            a6_splits.add(this_split)
            return 'var_%X' % this_split
        else:
            return m.group()

    statements = re.sub(r'-\$(\w\w\w\w)\(A6\)', a6_sub, statements)
    a6_splits = sorted(a6_splits)

    a6_decs = ''
    for a, b in zip(a6_splits, a6_splits[1:]):
        varsize = b-a
        if varsize == 1:
            a6_decs += 'char var_%X;' % b
        elif varsize == 2:
            a6_decs += 'short var_%X;' % b
        elif varsize == 4:
            a6_decs += 'long var_%X;' % b
        else:
            a6_decs += 'char var_%X[0x%x];' % (b, varsize)



    # Transformation: change #$70777063 to #'pwpc'
    def longliteral(m):
        chars = bytes.fromhex(m.group(1)).decode('ascii', 'replace')
        if all(c.isalnum() or c in ' #' for c in chars):
            return repr(chars)
        else:
            return m.group()

    statements = re.sub(r'\$([0-9A-Fa-f]{8})\b', longliteral, statements)



    # Transformation: change $ to 0x
    statements = statements.replace('$', '0x')



    # Transformation: split the trailing data into string literals
    data_splits = {data_offset}
    for m in re.finditer(r'\blabel_([0-9A-Fa-f]+)\b', statements):
        offset = int(m.group(1), 16)
        if data_offset <= offset < data_offset + len(data):
            data_splits.add(offset)
    data_splits = sorted(data_splits)

    def data_sub(m):
        this_offset = int(m.group(1), 16)
        if not (data_offset <= this_offset < data_offset + len(data)): return m.group()

        chars = b''
        for i in range(len(data)):
            if i > 0 and data_offset+i in data_splits: break
            chars += data[i:i+1]

        chars = chars.rstrip(b'\x00')

        quotedstring = ''
        if chars and chars[0] == len(chars) - 1:
            quotedstring += '\\p'
            chars = chars[1:]

        for c in chars:
            if c == 10:
                quotedstring += '\\r' # deliberately reversed CR and LF
            elif c == 13:
                quotedstring += '\\n'
            elif c == ord('"'):
                quotedstring += '\\"'
            elif 32 <= c < 127:
                quotedstring += chr(c)
            else:
                quotedstring += '\\x%02X' % c
        return '"%s"' % quotedstring

    statements = re.sub(r'\blabel_([0-9A-Fa-f]+)\b', data_sub, statements)



    # Does it use the self-argument-cleaning Pascal convention
    prototype = 'void %s(void)' % name
    if statements.split(';')[-2].startswith(('JMP (A0)', 'RTD ')): prototype = 'pascal ' + prototype



    def splitstatements(longstring):
        return re.findall(r'[^;:]+.', longstring)


    print(prototype)
    print('{')

    for x in splitstatements(a6_decs):
        print('    ' + x)

    if a6_decs: print()

    for x in splitstatements(statements):
        if x.endswith(';'):
            a, b, c = x.partition(' ')
            if c:
                b = ' ' * (8 - len(a))
            x = a + b + c
            x = '// ' + x
        print('    ' + x)

    print('}')
    print()
    print()
