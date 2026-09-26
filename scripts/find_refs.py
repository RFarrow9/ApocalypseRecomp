#!/usr/bin/env python3
"""Locate functions in a PS-X EXE by the strings they reference and the calls they make.

Usage:
  find_refs.py <exe> <game_config.toml> str  <substring> [...]
  find_refs.py <exe> <game_config.toml> call <0xADDR> [...]

`str`  finds every LUI/ADDIU (or LUI/ORI) pair that builds the address of a
       string containing <substring>, and reports the containing function.
`call` finds every JAL to <ADDR> and reports the calling function.

Function boundaries come from the analyzer's [[functions]] list, so results
are "which known function does this" -- the tool for pinning PsyQ entry points
the signature matcher missed, via their debug strings or the internal helpers
it did find.
"""
import bisect
import struct
import sys
import tomllib


def load(exe_path, cfg_path):
    exe = open(exe_path, "rb").read()
    load_addr, size = struct.unpack_from("<2I", exe, 0x18)
    text = exe[0x800:0x800 + size]
    cfg = tomllib.load(open(cfg_path, "rb"))
    funcs = sorted((int(f["address"], 16), f["name"]) for f in cfg["functions"])
    names = {int(h["address"], 16): h["name"] for h in cfg.get("hle_functions", [])}
    return load_addr, text, funcs, names


def owner(funcs, names, addr):
    i = bisect.bisect_right([a for a, _ in funcs], addr) - 1
    if i < 0:
        return "?"
    a, n = funcs[i]
    return "%s @0x%08X%s" % (n, a, " (%s)" % names[a] if a in names else "")


def words(text, load_addr):
    for off in range(0, len(text) - 3, 4):
        yield load_addr + off, struct.unpack_from("<I", text, off)[0]


def find_strings(text, load_addr, needle):
    hits, start = [], 0
    nb = needle.encode()
    while (i := text.find(nb, start)) >= 0:
        s = i
        while s > 0 and 0x20 <= text[s - 1] < 0x7F:
            s -= 1
        e = text.find(b"\0", i)
        hits.append((load_addr + s, text[s:e].decode("ascii", "replace")))
        start = i + 1
    return hits


def refs_to(text, load_addr, target):
    """Addresses of LUI/ADDIU|ORI pairs (within 16 instrs) that build `target`."""
    out = []
    lui = {}
    for pc, w in words(text, load_addr):
        op = w >> 26
        rt, rs, imm = (w >> 16) & 31, (w >> 21) & 31, w & 0xFFFF
        if op == 0x0F:
            lui[rt] = (pc, imm << 16)
        elif op in (0x09, 0x0D) and rs in lui and pc - lui[rs][0] <= 64:
            hi = lui[rs][1]
            val = (hi + (imm - 0x10000 if imm & 0x8000 and op == 0x09 else imm)) & 0xFFFFFFFF
            if op == 0x0D:
                val = hi | imm
            if val == target:
                out.append(pc)
    return out


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    exe, cfg, mode, args = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    load_addr, text, funcs, names = load(exe, cfg)
    for a in args:
        if mode == "str":
            for saddr, s in find_strings(text, load_addr, a):
                print("0x%08X %r" % (saddr, s[:70]))
                for pc in refs_to(text, load_addr, saddr):
                    print("    ref at 0x%08X in %s" % (pc, owner(funcs, names, pc)))
        elif mode == "call":
            t = int(a, 16)
            jal = 0x0C000000 | ((t >> 2) & 0x03FFFFFF)
            print("callers of 0x%08X:" % t)
            seen = set()
            for pc, w in words(text, load_addr):
                if w == jal:
                    o = owner(funcs, names, pc)
                    if o not in seen:
                        seen.add(o)
                        print("    %s" % o)
        else:
            sys.exit("mode must be str or call")


if __name__ == "__main__":
    main()
