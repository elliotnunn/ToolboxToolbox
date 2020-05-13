# The only clever thing that we do, is strip out "pad" and "last" records
# To make editing less tedious


def split(mpwobj):
    """Split the binary object into a list of "chunks"
    """

    biglist = []

    ofs = 0
    while ofs < len(mpwobj):
        rectype = mpwobj[ofs]

        if not (rectype <= 20 or rectype == 25):
            raise ValueError(f'bad record type {rectype} at {hex(offset)}')

        if rectype == 1: # First
            reclen = 4
        elif rectype == 2: # Last
            reclen = 2
        elif rectype == 5: # Module
            reclen = 6
        elif rectype == 6: # EntryPoint
            reclen = 8
        elif rectype == 7: # Size
            reclen = 6
        elif rectype == 11: # Filename
            reclen = 8
        elif rectype == 14: # ModuleEnd
            reclen = 8
        elif rectype == 16: # BlockEnd
            reclen = 12
        elif rectype == 25: # XData
            reclen = 8
        else:
            reclen = 256 * mpwobj[ofs+2] + mpwobj[ofs+3]

        biglist.append(mpwobj[ofs:ofs+reclen])
        ofs += reclen

    return biglist


def join(chunks):
    newlist = []
    for c in chunks:
        newlist.append(c)
        if len(c) & 1:
            newlist.append(b'\0')
    return newlist
