#!/usr/bin/env python3
"""Convert the runtime's VRAM PPM dumps in a directory to PNG (stdlib only).

Usage: ppm2png.py <dir>
Prints each file with the fraction of non-black samples, a quick signal for
"did anything get drawn".
"""
import glob
import os
import struct
import sys
import zlib


def convert(src, dst):
    data = open(src, "rb").read()
    parts = data.split(b"\n", 3)
    w, h = map(int, parts[1].split())
    px = parts[3]
    raw = b"".join(b"\0" + px[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    with open(dst, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))
    sample = px[::101]
    return sum(1 for b in sample if b) / max(len(sample), 1)


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    for src in sorted(glob.glob(os.path.join(d, "*.ppm"))):
        frac = convert(src, src[:-4] + ".png")
        print("%s  non-black %.3f" % (os.path.basename(src), frac))


if __name__ == "__main__":
    main()
