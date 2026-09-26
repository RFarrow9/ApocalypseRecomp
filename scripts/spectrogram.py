#!/usr/bin/env python3
"""Render a spectrogram PNG of a PS1_AUDIO_DUMP WAV (numpy + Pillow).

Usage: spectrogram.py <dump.wav> <out.png> [--start S] [--seconds N]

Music shows as horizontal harmonic lines with a rhythm; noise as a uniform
smear; silence as black.  A way to judge audio without listening.
"""
import argparse
import wave

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("out")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--seconds", type=float, default=20.0)
    a = ap.parse_args()
    w = wave.open(a.wav, "rb")
    rate, ch = w.getframerate(), w.getnchannels()
    w.setpos(int(a.start * rate))
    raw = np.frombuffer(w.readframes(int(a.seconds * rate)), dtype=np.int16)
    mono = raw.reshape(-1, ch).mean(axis=1) / 32768.0
    n, hop = 2048, 512
    frames = [mono[i:i + n] * np.hanning(n)
              for i in range(0, len(mono) - n, hop)]
    spec = np.abs(np.fft.rfft(np.array(frames), axis=1))[:, : n // 4]  # to ~11 kHz
    db = 20 * np.log10(spec + 1e-9)
    db -= db.max()                                  # relative to the peak
    img = np.clip((db + 60) / 60, 0, 1)             # top 60 dB -> 0..1
    img = (img.T[::-1] * 255).astype(np.uint8)      # low frequencies at bottom
    Image.fromarray(img).resize((min(1600, img.shape[1]), 400)).save(a.out)
    print("%.1fs from %.1fs -> %s" % (len(mono) / rate, a.start, a.out))


if __name__ == "__main__":
    main()
