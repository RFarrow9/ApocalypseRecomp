#!/usr/bin/env python3
"""Find groups of analyzer "functions" that are really one piece of code.

Usage: find_tangles.py <exe> <analyzer.toml>

Hand-written assembly (renderers, decompressors) jumps freely between what
the analyzer splits into separate functions: `j`/`b*` into the middle of a
neighbour, conditional calls (`bltzal`/`bgezal`) into a neighbour's tail, and
continuation addresses built with lui/addiu and later reached through `jr`.
ps1Recomp can only turn a transfer into a local goto inside one function, so
each such group has to become one multi-entry region.

For every group of two or more functions this prints the region and every
address inside it that is entered from outside the function containing it --
the entry list for a [[regions]] override.
"""
import bisect
import struct
import sys
import tomllib

CONSTS = "--consts" in sys.argv


def main():
    exe_path, cfg_path = sys.argv[1], sys.argv[2]
    exe = open(exe_path, "rb").read()
    base, size = struct.unpack_from("<2I", exe, 0x18)
    text = exe[0x800:0x800 + size]
    cfg = tomllib.load(open(cfg_path, "rb"))
    funcs = sorted({(int(f["address"], 16), int(f["size"]))
                    for f in cfg["functions"]})
    starts = [a for a, _ in funcs]

    def owner(pc):
        i = bisect.bisect_right(starts, pc) - 1
        if i >= 0 and pc < funcs[i][0] + funcs[i][1]:
            return i
        return None

    parent = list(range(len(funcs)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    entries = {}  # target -> set of source pcs
    lui = {}
    for off in range(0, len(text) - 3, 4):
        pc = base + off
        w = struct.unpack_from("<I", text, off)[0]
        op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
        imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        tgt = None
        if op == 2:                                   # j
            tgt = (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        elif op in (4, 5, 6, 7) or (op == 1 and rt in (0, 1, 0x10, 0x11)):
            tgt = pc + 4 + simm * 4                   # b*, incl. bltzal/bgezal
        elif op == 0x0F:
            lui[rt] = (pc, imm << 16)
        elif op == 9 and rs in lui and pc - lui[rs][0] <= 64 and CONSTS:
            v = (lui[rs][1] + simm) & 0xFFFFFFFF      # code pointer constant
            j = owner(v)
            if j is not None and v != funcs[j][0]:
                tgt = v
        if tgt is None:
            continue
        src, dst = owner(pc), owner(tgt)
        if src is None or dst is None or src == dst:
            continue
        parent[find(src)] = find(dst)
        if tgt != funcs[dst][0]:
            entries.setdefault(tgt, set()).add(pc)

    groups = {}
    for i in range(len(funcs)):
        groups.setdefault(find(i), []).append(i)
    for g in sorted(groups.values(), key=lambda g: funcs[g[0]][0]):
        if len(g) < 2:
            continue
        lo = min(funcs[i][0] for i in g)
        hi = max(funcs[i][0] + funcs[i][1] for i in g)
        inner = sorted(e for e in entries if lo <= e < hi)
        print("region 0x%08X-0x%08X  %d functions, %d mid-function entries"
              % (lo, hi, len(g), len(inner)))
        print("  functions:", " ".join("%08X" % funcs[i][0] for i in sorted(g)))
        for e in inner:
            print("  entry %08X  from %s" % (e, " ".join("%08X" % s for s in sorted(entries[e]))))


if __name__ == "__main__":
    main()
