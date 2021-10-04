#!/usr/bin/env python3

import sys
from datetime import datetime, timedelta


# Copied from machfs MakeHFS
def hfsdat(x):
    if x.lower() == "now":
        x = datetime.now().isoformat()

    if len(x) == 8 and all(c in "0123456789ABCDEF" for c in x.upper()):
        try:
            return int(x, base=16)
        except ValueError:
            pass

    epoch = "19040101000000"  # ISO8601 with the non-numerics stripped

    # strip non-numerics and pad out using the epoch (cheeky)
    stripped = "".join(c for c in x if c in "0123456789")
    stripped = stripped[: len(epoch)] + epoch[len(stripped) :]

    tformat = "%Y%m%d%H%M%S"

    delta = datetime.strptime(stripped, tformat) - datetime.strptime(epoch, tformat)
    delta = int(delta.total_seconds())

    if not 0 <= delta <= 0xFFFFFFFF:
        print("Warning: moving %r into the legacy MacOS date range (1904-2040)" % x)

    delta = min(delta, 0xFFFFFFFF)
    delta = max(delta, 0)

    return delta


# Copied from ExtractBinDates.py
def macdatestr(srcint):
    dt = datetime(1904, 1, 1) + timedelta(seconds=srcint)
    st = dt.isoformat()
    st = st.replace("T", " ")
    return st


def secs2date(secs):
    print(f"${secs:08x} = {macdatestr(secs)}")


def date2secs(date):
    secs = hfsdat(date)
    print(f"{macdatestr(secs)} = ${secs:08x}")


for a in sys.argv[1:]:
    if a.startswith("$"):
        secs = int(a[1:], 16)
        secs2date(secs)
    elif a.startswith("0x"):
        secs = int(a[2:], 16)
        secs2date(secs)
    else:
        date2secs(a)
