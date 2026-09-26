#!/usr/bin/env python3
"""Decode one XA-ADPCM channel of a file on the disc to WAV (numpy).

Usage: xa_extract.py <track1.bin> <FILE.XA> <channel> <out.wav> [--seconds N]
       xa_extract.py <track1.bin> <FILE.XA> --list

A reference for the runtime's XA decoder: decodes straight from the disc
with the same psx-spx algorithm, independent of the game, so a clean result
here and noise in-game points at delivery, not decoding.  --list shows which
file/channel/coding combinations the file interleaves.
"""
import argparse
import collections
import struct
import wave

import numpy as np

import extract_exe  # same directory: ISO9660 walker

POS = (0, 60, 115, 98)
NEG = (0, 0, -52, -55)


def decode_sector(raw, hist):
    coding = raw[19]
    stereo = (coding & 3) == 1
    rate = 18900 if ((coding >> 2) & 3) == 1 else 37800
    eight = ((coding >> 4) & 3) == 1
    chans = ([], [])
    data = raw[24:24 + 18 * 128]
    for g in range(18):
        grp = data[g * 128:(g + 1) * 128]
        for u in range(4 if eight else 8):
            p = grp[4 + u]
            shift, flt = p & 15, (p >> 4) & 3
            if shift > 12:
                shift = 9
            ch = (u & 1) if stereo else 0
            for j in range(28):
                if eight:
                    s = struct.unpack("b", bytes([grp[16 + j * 4 + u]]))[0] << 8
                else:
                    b = grp[16 + j * 4 + (u >> 1)]
                    n = (b >> 4) if (u & 1) else (b & 15)
                    s = ((n << 12) & 0xFFFF)
                    s = s - 0x10000 if s & 0x8000 else s
                s >>= shift
                old, older = hist[ch]
                s += (old * POS[flt] + older * NEG[flt] + 32) >> 6
                s = max(-32768, min(32767, s))
                hist[ch] = (s, old)
                chans[ch].append(s)
    if not stereo:
        chans = (chans[0], chans[0])
    return rate, chans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bin")
    ap.add_argument("file")
    ap.add_argument("channel", nargs="?", type=int, default=0)
    ap.add_argument("out", nargs="?")
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    disc = extract_exe.Disc(a.bin)
    hit = disc.find(a.file)
    if not hit:
        raise SystemExit("no " + a.file)
    _, lba, size = hit
    nsec = (size + 2047) // 2048
    if a.list:
        seen = collections.Counter()
        for i in range(min(nsec, 4000)):
            disc.f.seek((lba + i) * disc.sector_size)
            raw = disc.f.read(2352)
            if raw[18] & 0x04:
                seen[(raw[16], raw[17], raw[19])] += 1
        for (f, c, cod), n in sorted(seen.items()):
            print("file %d channel %d coding 0x%02X: %d sectors" % (f, c, cod, n))
        return
    hist = [(0, 0), (0, 0)]
    L, R, rate = [], [], 37800
    for i in range(nsec):
        disc.f.seek((lba + i) * disc.sector_size)
        raw = disc.f.read(2352)
        if not (raw[18] & 0x04) or raw[17] != a.channel:
            continue
        rate, (l, r) = decode_sector(raw, hist)
        L += l
        R += r
        if len(L) > a.seconds * rate:
            break
    pcm = np.column_stack([np.array(L, np.int16), np.array(R, np.int16)])
    w = wave.open(a.out, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(pcm.tobytes())
    print("%d frames at %d Hz -> %s" % (len(L), rate, a.out))


if __name__ == "__main__":
    main()
