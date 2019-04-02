#!/usr/bin/env python3

# unsigned longint;        /* checkSum */
# unsigned longint LOC = 1071985200;  /* location identifier */
# integer version = 4;     /* ckid version number */
# integer readOnly = 0;    /* Check out state, if = 0 it is modifiable */
# Byte noBranch = 0;       /* if modifiable & Byte != 0 then branch was made
#                            on check out */
# Byte clean = 0,
#     MODIFIED = 1;       /* did user execute "ModifyReadOnly" on this file? */
# unsigned longint UNUSED; /* not used */
# unsigned longint;        /* date and time of checkout */
# unsigned longint;        /* mod date of file */

# unsigned longint;        /* PID.a */
# unsigned longint;        /* PID.b */

# integer;                 /* user ID */
# integer;                 /* file ID */
# integer;                 /* rev ID */

# pstring;                 /* Project path */
# Byte = 0;
# pstring;                 /* User name */
# Byte = 0;
# pstring;                 /* Revision number */
# Byte = 0;
# pstring;                 /* File name */
# Byte = 0;
# pstring;                 /* task */
# Byte = 0;
# wstring;                 /* comment */
# Byte = 0;

import argparse
from macresources.do_what_i_mean import read
import os
from os import path
import struct
import datetime

def up_date(mac_date):
    base = datetime.datetime(1904, 1, 1, 0, 0, 0)
    base += datetime.timedelta(seconds=mac_date)
    return base.strftime('%Y-%m-%d %H:%M:%S')

parser = argparse.ArgumentParser(description='''
    Print the dates in every ckid (Projector) resource.
''')

parser.add_argument('src', action='store', help='Source file')

grp = parser.add_mutually_exclusive_group()
grp.add_argument('-c', action='store_const', dest='what', const='ckout', help='Show checkout date')
grp.add_argument('-m', action='store_const', dest='what', const='mod', help='Show mod date')
grp.add_argument('-p', action='store_const', dest='what', const='proj', help='Show project creation date')

args = parser.parse_args()

for base, dirs, files in os.walk(args.src):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    files[:] = [f for f in files if f.endswith('.rdump')]

    for f in files:
        resources = read(path.join(base, f))

        for r in resources:
            if r.type == b'ckid':
                cksm, loc, ver, ro, nobr, mod, _, t_ckout, t_mod, t_proj, tc_proj, uid, fid, rid = struct.unpack_from('>IIHHBBIIIIIHHH', r.data)

                if args.what == 'ckout':
                    print(up_date(t_ckout), end='  ')
                elif args.what == 'mod':
                    print(up_date(t_mod), end='  ')
                elif args.what == 'proj':
                    print(up_date(t_proj), end='  ')

                print(path.join(base, f[:-6])) # cut rdump off end
