#!/usr/bin/env python3
"""Pull the boot PS-X EXE out of a PS1 disc image via its ISO9660 filesystem.

Usage: extract_exe.py <track1.bin|image.iso> [outdir] [--list]

Handles raw 2352-byte-sector images (MODE2/2352, the usual raw dump format) and plain
2048-byte-sector .iso files. Reads SYSTEM.CNF to find the real boot executable
rather than scanning for the "PS-X EXE" magic, which breaks on raw images because
every sector carries its own header and the file is not contiguous in the .bin.
"""
import os
import re
import struct
import sys


class Disc:
    def __init__(self, path):
        self.f = open(path, "rb")
        size = os.path.getsize(path)
        # A raw sector starts with the 12-byte sync pattern 00 FF*10 00.
        head = self.f.read(12)
        if head == b"\x00" + b"\xff" * 10 + b"\x00":
            self.sector_size, self.data_off = 2352, 24  # MODE2 form 1: sync+hdr+subhdr
        elif size % 2048 == 0:
            self.sector_size, self.data_off = 2048, 0
        else:
            sys.exit("unrecognised image layout (size %d)" % size)

    def read_sector(self, lba):
        self.f.seek(lba * self.sector_size + self.data_off)
        return self.f.read(2048)

    def read_extent(self, lba, length):
        out = bytearray()
        while len(out) < length:
            out += self.read_sector(lba)
            lba += 1
        return bytes(out[:length])

    def walk(self, lba=None, length=None, prefix=""):
        """Yield (path, lba, size, is_dir) for every entry under a directory."""
        if lba is None:
            pvd = self.read_sector(16)
            if pvd[1:6] != b"CD001":
                sys.exit("no ISO9660 primary volume descriptor at sector 16")
            root = pvd[156:156 + 34]
            lba, length = struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0]
        data = self.read_extent(lba, length)
        i = 0
        while i < len(data):
            n = data[i]
            if n == 0:  # records never straddle a sector; skip to the next one
                i = (i // 2048 + 1) * 2048
                continue
            rec = data[i:i + n]
            e_lba, e_size = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
            is_dir = bool(rec[25] & 2)
            name = rec[33:33 + rec[32]]
            i += n
            if name in (b"\x00", b"\x01"):
                continue
            path = prefix + "/" + name.decode("ascii", "replace")
            yield path, e_lba, e_size, is_dir
            if is_dir:
                yield from self.walk(e_lba, e_size, path)

    def find(self, want):
        want = want.upper().lstrip("\\/").replace("\\", "/")
        for path, lba, size, is_dir in self.walk():
            p = path.lstrip("/").upper()
            if not is_dir and (p == want or p.split(";")[0] == want.split(";")[0]):
                return path, lba, size
        return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    img = args[0]
    out = args[1] if len(args) > 1 else os.path.dirname(os.path.abspath(img))
    disc = Disc(img)
    print("image: %s (%d-byte sectors)" % (img, disc.sector_size))

    if "--list" in sys.argv:
        for path, lba, size, is_dir in disc.walk():
            print("  %s %8d  lba %6d  %s" % ("d" if is_dir else "-", size, lba, path))

    hit = disc.find("SYSTEM.CNF")
    if not hit:
        sys.exit("no SYSTEM.CNF on disc")
    cnf = disc.read_extent(hit[1], hit[2]).decode("ascii", "replace")
    print("SYSTEM.CNF:\n  " + "\n  ".join(l.strip() for l in cnf.splitlines() if l.strip()))
    m = re.search(r"BOOT\s*=\s*cdrom:\\?([^\s;]+(?:;\d+)?)", cnf, re.I)
    if not m:
        sys.exit("no BOOT line in SYSTEM.CNF")
    hit = disc.find(m.group(1))
    if not hit:
        sys.exit("boot file %s not found on disc" % m.group(1))
    path, lba, size = hit
    exe = disc.read_extent(lba, size)
    if exe[:8] != b"PS-X EXE":
        sys.exit("%s is not a PS-X EXE" % path)
    pc, gp, taddr, tsize = struct.unpack_from("<4I", exe, 0x10)
    sp_base, sp_off = struct.unpack_from("<2I", exe, 0x30)
    name = os.path.join(out, path.lstrip("/").split(";")[0])
    os.makedirs(out, exist_ok=True)
    with open(name, "wb") as fh:
        fh.write(exe)
    print("boot exe: %s (%d bytes) -> %s" % (path, size, name))
    print("  entry PC   0x%08X" % pc)
    print("  GP         0x%08X" % gp)
    print("  load addr  0x%08X  text size %d (0x%X)" % (taddr, tsize, tsize))
    print("  stack      0x%08X + 0x%X" % (sp_base, sp_off))
    print("  region     %s" % exe[0x4C:0x80].split(b"\0")[0].decode("ascii", "replace"))


if __name__ == "__main__":
    main()
