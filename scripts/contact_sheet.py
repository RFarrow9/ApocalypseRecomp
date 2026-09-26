#!/usr/bin/env python3
"""Tile the display area of several VRAM snapshots into one PNG (stdlib only).

Usage: contact_sheet.py <dir> <out.png> [--cols N] [--scale 2] [--rect x,y,w,h]

Reads the runtime's shot_*.ppm dumps (1024x512 VRAM), crops the rectangle
(default the top framebuffer, 0,0,512,256), downsamples by --scale, and tiles
them in frame order -- one image to judge motion across a scripted run.
"""
import argparse
import glob
import os
import struct
import zlib


def read_ppm(path):
    data = open(path, "rb").read()
    parts = data.split(b"\n", 3)
    w, h = map(int, parts[1].split())
    return w, h, parts[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--rect", default="0,0,512,256")
    a = ap.parse_args()
    rx, ry, rw, rh = map(int, a.rect.split(","))
    files = sorted(glob.glob(os.path.join(a.dir, "shot_*.ppm")))
    if not files:
        raise SystemExit("no shot_*.ppm in " + a.dir)
    tw, th = rw // a.scale, rh // a.scale
    cols = min(a.cols, len(files))
    rows = (len(files) + cols - 1) // cols
    W, H = cols * tw, rows * th
    canvas = bytearray(W * H * 3)
    for n, f in enumerate(files):
        w, _, px = read_ppm(f)
        ox, oy = (n % cols) * tw, (n // cols) * th
        for y in range(th):
            sy = ry + y * a.scale
            src = (sy * w + rx) * 3
            dst = ((oy + y) * W + ox) * 3
            row = px[src:src + rw * 3]
            canvas[dst:dst + tw * 3] = b"".join(
                row[x * a.scale * 3:x * a.scale * 3 + 3] for x in range(tw))
    raw = b"".join(b"\0" + bytes(canvas[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    with open(a.out, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)))
        fh.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        fh.write(chunk(b"IEND", b""))
    print("%d frames -> %s (%dx%d)" % (len(files), a.out, W, H))


if __name__ == "__main__":
    main()
