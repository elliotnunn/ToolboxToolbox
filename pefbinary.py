import struct

class PEF:
    MAGIC = b'Joy!'
    
    CONT_HEAD_FMT = '>4s4s4s5I2HI'
    CONT_HEAD_LEN = struct.calcsize(CONT_HEAD_FMT)
    
    SEC_HEAD_FMT = '>i5I4B'
    SEC_HED_LEN = struct.calcsize(SEC_HEAD_FMT)

    @classmethod
    def read_from(cls, path):
        with open(path, 'rb') as f:
            return cls(f.read())

    def __init__(self, data):
        (magic, fourcc, arch, ver,
        timestamp, old_def_ver, old_imp_ver, cur_ver,
        sec_count, inst_sec_count, reserv) = struct.unpack_from(self.CONT_HEAD_FMT, data)

        sec_earliest = len(data)
        sec_latest = 0

        self.sections = []
        self.sectypes = []
        self.headeroffsets = []

        self.code = None

        for i in range(sec_count):
            sh_offset = self.CONT_HEAD_LEN + self.SEC_HED_LEN*i

            (sectionName, sectionAddress, execSize,
            initSize, rawSize, containerOffset,
            regionKind, shareKind, alignment, reserved) = struct.unpack_from(self.SEC_HEAD_FMT, data, sh_offset)

            the_sec = data[containerOffset : containerOffset + rawSize]

            if regionKind == 0 and execSize == initSize == rawSize:
                the_sec = bytearray(the_sec)
                self.code = the_sec

            self.sections.append(the_sec)
            self.sectypes.append(regionKind)
            self.headeroffsets.append(sh_offset)

            sec_earliest = min(sec_earliest, containerOffset)
            sec_latest = max(sec_latest, containerOffset + rawSize)

        if any(data[sec_latest:]):
            print('nonzero trailing data from', hex(sec_latest), 'to', hex(len(data)), ' ... will cause incorrect output')

        self.padmult = 1
        while len(data) % (self.padmult * 2) == 0:
            self.padmult *= 2

        self.header = data[:sec_earliest]

    def __bytes__(self):
        accum = bytearray(self.header)

        for i in range(len(self.sections)):
            the_sec = self.sections[i]
            hoff = self.headeroffsets[i]

            while len(accum) % 16:
                accum.append(0)

            new_off = len(accum)
            new_len = len(the_sec)

            accum.extend(the_sec)

            struct.pack_into('>I', accum, hoff + 20, new_off)

            if the_sec is self.code:
                for i in range(8, 20, 4):
                    struct.pack_into('>I', accum, hoff + i, new_len)

        while len(accum) % self.padmult != 0:
            accum.extend(b'\x00')

        return bytes(accum)

    def write_to(self, path):
        with open(path, 'wb') as f:
            f.write(bytes(self))
