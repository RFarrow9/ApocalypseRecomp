#!/usr/bin/env python3
"""Summarise a PS1_AUDIO_DUMP WAV without listening to it (stdlib only).

Usage: audio_stats.py <dump.wav> [--window 1.0]

Prints, per window of seconds, the RMS and peak level of each channel and the
fraction of clipped samples -- enough to tell silence from music from noise
bursts, and where each starts.
"""
import argparse
import array
import math
import wave


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--window", type=float, default=1.0)
    a = ap.parse_args()
    w = wave.open(a.wav, "rb")
    rate, ch = w.getframerate(), w.getnchannels()
    data = array.array("h", w.readframes(w.getnframes()))
    per = int(rate * a.window) * ch
    print("%d Hz, %d ch, %.1f s" % (rate, ch, len(data) / ch / rate))
    for start in range(0, len(data), per):
        chunk = data[start:start + per]
        if not chunk:
            break
        out = []
        for c in range(ch):
            s = chunk[c::ch]
            rms = math.sqrt(sum(x * x for x in s) / len(s))
            peak = max(abs(x) for x in s)
            clip = sum(1 for x in s if abs(x) >= 32767) / len(s)
            out.append("rms %6.0f peak %5d clip %4.1f%%" % (rms, peak, clip * 100))
        print("%6.1fs  %s" % (start / ch / rate, "  |  ".join(out)))


if __name__ == "__main__":
    main()
