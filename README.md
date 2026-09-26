# Apocalypse: Recompiled

> ### ⬇️ Just want to play? **[Download for Windows](https://github.com/RFarrow9/ApocalypseRecomp/releases/latest/download/Apocalypse-Recompiled-win64.zip)**
> Unzip, run `Apocalypse.exe`, pick your own disc image (`.cue`). Nothing else to install.
> Windows may say *"Windows protected your PC"* (the exe isn't code-signed): click
> **More info → Run anyway**. Press **F1** in game for the menu.
> · [Release notes](https://github.com/RFarrow9/ApocalypseRecomp/releases/latest)

A native PC version of **Apocalypse** (PlayStation, 1998, Neversoft/Activision), made by
statically recompiling the game's code to x86-64 with
[PS1Recomp](https://github.com/PS1Recomp/ps1-recomp). It is not an emulator: the game's
MIPS code becomes C++, compiled and linked against a PlayStation hardware runtime.

The whole game plays from start to finish -- all 11 levels, movies, saving and loading,
the ending -- with sharper graphics, twin-stick controller support, widescreen and an
in-game menu on top.

> **Unofficial fan project.** Not affiliated with or endorsed by Activision or Neversoft.
> **No game data is included:** you need your own copy of the PAL disc (SLES-00460) as a
> BIN/CUE image.

## What this repo is (and is not)

This repo contains **only original work**: configuration, patches, build scripts and notes.

It contains **no game data and no recompiled output**. The recompiled C++ is a derivative
work of the game binary; the disc image is obviously the game itself. Neither belongs here.
To use this you supply your own copy of the disc, and the build produces the output locally.

## Status

Target: **Apocalypse (Europe)**, SLES-00460, as a raw BIN/CUE dump of your own disc. Boot exe `SLES_004.60`,
entry `0x80086808`, 1 MB of code at `0x80010000`, 2116 functions.

| Stage | State |
|-------|-------|
| Toolchain (native MSVC) | ✅ analyzer, recompiler, runtime |
| Disc image | supplied by the player, kept outside this repo |
| Function analysis | ✅ 139 PsyQ matches + 21 hand-identified, 1 false match undone (`config/overrides.toml`) |
| Recompilation | ✅ compiles and links on Windows |
| Boots | ✅ warning screen → Neversoft logo → title ("PRESS START") |
| Input | ✅ libpad raw buffers refreshed each VBlank; Start works |
| **Main menu** | ✅ **renders** (NEW GAME / LOAD GAME / OPTIONS), times out into attract mode |
| Attract mode | ✅ intro movie → title → recorded demo (graveyard level) → title, looping |
| **FMV** | ✅ **Activision/intro/attract movies and the NEW GAME cutscene play in 24-bit colour**, checked frame-for-frame against ffmpeg's decode of the same `.STR` |
| Pause menu | ✅ PAUSED / CONTINUE / QUIT, cursor moves |
| **In-game** | ✅ **all 11 levels** (Prison → The Beast) load and play under scripted input, no crashes |
| **Progression + saving** | ✅ level complete → "Save game?" → memory card save → next level's cutscene → next level; **LOAD GAME** lists the save ("SEWERS 1") and resumes there |
| Controls | ✅ keyboard; controllers with the game's own twin-stick DualShock mode (left stick moves, right stick aims and fires) |
| Gameplay input / timing | ✅ scripted pad input drives the player; field rate follows the game's PAL/NTSC mode |
| Audio | ✅ SPU effects/sequenced music; ✅ XA-ADPCM (speech/streamed audio) decoded -- verified against the disc; not yet listened to by a human |

## What this recomp adds

The game runs as native x86-64 code, not under an emulator. On top of that:

- **Just run it**: double-click the exe. The first run asks for your own disc image
  (`.cue`), checks it is Apocalypse (SLES-00460), extracts what it needs and remembers it.
  Dropping a `.cue` onto the exe works too.
- **In-game menu** (**F1**, **Esc**, or **Back+Start** on a controller): pauses the game.
  - Display: fullscreen, aspect **4:3 / 16:9 / 21:9 / 32:9**, smooth or crisp pixels.
  - Audio: volume.
  - Extras: **unlock all levels** (the game's own debug level select and autotest),
    **infinite health**, **infinite ammo**, **all weapons**.
  - "Original settings" puts everything back to how the PlayStation showed it.
  - Settings are saved to `settings.ini` next to the exe.
- **Controllers, twin-stick**: any pad SDL knows (Xbox, PlayStation, Switch Pro, most
  generic pads), hot-pluggable, laid out by position (A/south = ✕, B = ○, X = □, Y = △),
  triggers as L2/R2. The game's own DualShock mode is on by default: **left stick moves,
  right stick aims and fires** (verified: stick-only input moves the player and shoots). The
  left stick also drives the D-pad, which is what the menus read.
- **Sharper graphics**: the displayed frame is drawn again on your GPU at 2x-8x the
  native resolution (**Auto** by default: fills the window). The PS1's own texture lookup,
  palettes, colour modulation and four blend modes are reproduced in a shader, so polygons,
  sprites and text come out clean instead of blocky. Movies stay native. "Original"
  shows the untouched software picture.
- **Big window, fullscreen**: opens at 4:3, sized to about 80% of the desktop height.
  **F11** or **Alt+Enter** toggles borderless fullscreen.
- **Widescreen**: the wider aspects widen the 3D view through the GTE instead of
  stretching it. Movies stay 4:3; the HUD is widened; objects past the original screen edge
  can pop in (the game culls them itself).
- Keyboard: arrows = D-pad, Z/X/A/S = ✕/○/□/△, Q/W/E/R = L1/R1/L2/R2, Enter = Start.

### Cheats are data

The cheat list lives in `config/overrides.toml` (`[[cheats]]`) and ships in `game.toml`.
Each entry is a list of actions:

| Action | Meaning |
|---|---|
| `800FF9B8=1` | write the word 1 to 0x800FF9B8, every frame while on |
| `800FFC28>DA=64:h` | follow the pointer at 0x800FFC28, add 0xDA, write 0x64 as 16 bits (`:b` = 8) |
| `call 8005E62C 800FFC28>0 3 unless 800FFC28>270` | call game function 0x8005E62C(player, 3) at the next end of frame, unless that weapon slot is already filled |
| `... if 800FFC28>44=800A3920` | only while the object's class pointer matches (between levels the player pointer holds other objects) |

The addresses were found with `PS1_RAM_DUMP` snapshots correlated against the HUD, and
by reading the pickup handler; the comments in `overrides.toml` record how.

## Building from source (Windows)

    # once: upstream clone at the tested commit + Windows patches
    git clone --recurse-submodules https://github.com/PS1Recomp/ps1-recomp.git ../PS1Recomp-ps1-recomp
    cd ../PS1Recomp-ps1-recomp && git checkout ab4f0e0
    for p in 002 003 004 005 006; do git apply ../ApocalypseRecomp/patches/$p-*.patch; done
    # MultiThreaded = static C runtime, so the exe runs without the VC++ redistributable
    cmake -B build -DPS1RECOMP_BUILD_TESTS=OFF -DSDL2_DIR=<path to SDL2-2.32.10>/cmake \
        -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded
    cmake --build build --config Release --target ps1Analyzer ps1Recomp

    # every change: analyze -> merge overrides -> recompile -> build
    sh scripts/rebuild.sh
    ../PS1Recomp-ps1-recomp/build/ps1Runtime/Release/ps1Runtime.exe \
        --config <game data folder>/build/game_config.toml

You need Visual Studio 2022 (MSVC), CMake 3.20+, Python 3 with Pillow, Git Bash, and the
official `SDL2-devel-2.32.10-VC.zip`. By default the scripts expect the upstream clone next
to this repo (`../PS1Recomp-ps1-recomp`) and your disc image in `../../gamedata`; set
`PS1RECOMP` and `GAMEDATA` to use other locations. The disc image must stay outside this
repo.

## Patches to upstream

| Patch | What |
|-------|------|
| `001-ps1runtime-pthread-link` | Linux/gcc 10: link pthread (Linux build) |
| `002-windows-msvc-port` | Runtime builds with MSVC: backtrace shims, GL 3.3 entry points loaded through SDL, `<SDL2/...>` include shim, 64 MB stack (Linux gives 8 MB and recompiled calls nest deeply), unbuffered stdout, PDB, and a Windows stall sampler (`PS1_STALL_SAMPLE=<ms>`) |
| `003-div-hardware-semantics` | DIV/DIVU emit `DO_DIV`/`DO_DIVU` with R3000A results for /0 and INT_MIN/-1. Before: /0 skipped the write, INT_MIN/-1 faulted the host, and a constant /0 (data decoded as code) failed to compile under MSVC |
| `004-runtime-fixes-and-diagnostics` | Runtime bugs, all general (not Apocalypse-specific): VBlank events/callbacks were only delivered from inside `VSync()`, so polling loops froze; the "usable guest stack" check rejected the 2 MB RAM mirrors (8 MB dev-kit stacks), silently deferring *every* callback; `DMACallback` handlers were stored but never run; libpad direct buffers were never refreshed and `PadGetState` ignored libpad port ids; **`ClearOTag`/`ClearOTagR` linked in the wrong directions** (reverse-OT games drew nothing); **GTE register access had no hardware semantics** (LZCR, IR/VZ sign expansion, SXYP, ORGB, control sign expansion, FLAG bit 31); `skip_<name>` HLE names. Diagnostics: `PS1_PEEK`, `PS1_CALL_PROFILE` and the `PS1RECOMP_ABI_CHECK` build (reports callees that clobber `$s0-$s7/$sp/$fp`) |
| `005-recompiler-control-flow-and-gte` | `BLTZAL`/`BGEZAL` are conditional *calls*, not gotos; **a function that ends without a jump now falls through to the next address** (it returned, leaving `$sp` unbalanced when the analyzer split a function); **`mfc2/mtc2/cfc2/ctc2/lwc2/swc2` go through the GTE accessors** instead of raw arrays; `jr $rX` to the entry `$ra` is a return (hand-written code parking `$ra`); `[[functions]] entry = ` for multi-entry regions; null calls reported with registers |
| (004, continued) | **FMV and presentation**: native libcd streaming (`psyq_st.cpp`: St ring, `CdRead2`, `StGetNext`/`StFreeRing`, sectors assembled at data-ready time); **MDEC** decode per psx-spx (inverse zigzag, zigzag-ordered quant tables, DC scale, FE00 padding, orthonormal IDCT, output depth from bits 28-27 -- 24bpp was decoded as 15bpp -- and the scale-table command no longer overwrites the quant tables); **24bpp display** and PAL heights in the renderer, which now composes the displayed picture on the CPU (`GPU::composeDisplay`) and letterboxes to 4:3; GP1(08h) bit 6 no longer lands in the display-disable bit; **GPU vertices are signed 11-bit and oversized polygons/lines are dropped** as on hardware (games rely on it for polygons behind the camera). `PS1_SHOT_DISPLAY=1` snapshots the displayed picture; `PS1_MDEC_DEBUG` / `PS1_MDEC_DUMP` |
| (004, continued) | **Memory cards**: A0:ABh/ACh are `_card_info`/`_card_load` (answered with the card IOE event only), B0:42h/43h/45h are `firstfile`/`nextfile`/`erase`, and a BIOS **memory card filesystem** (`card_fs.cpp`: `bu00:` create/read/write/seek on the card image, psx-spx directory format). CD interrupts now go to the CD-ROM event class 0xF0000003 -- they were delivered to the memory card classes, which made saves report "insert a memory card". **Overlay menu** (Dear ImGui, fetched by CMake), settings.ini, data-driven cheats with pointer chains and guest calls (run at VSync/DrawSync), **first-run disc setup** (`disc_setup.cpp`), controller mapping, analog pad reporting, fullscreen/aspect/filtering, GTE widescreen hack, GTE projection from IR1/IR2. Test hooks: `PS1_POKE`, `PS1_RAM_DUMP`, `PS1_GUEST_CALL`, `PS1_ANALOG`, `PS1_TURBO`, `PS1_OVERLAY_OPEN` |
| `006-windows-test-portability` | Unit tests build and run on MSVC (stack reserve, wide `std::filesystem::path`) |

## Tools

- `scripts/extract_exe.py` — boot exe via ISO9660 + SYSTEM.CNF; handles raw 2352-byte sectors.
- `scripts/find_refs.py` — which function references a string, or calls an address. This is
  how the missed PsyQ entry points were pinned.
- `scripts/merge_overrides.py` — folds `config/overrides.toml` into the analyzer output.
- `scripts/find_tangles.py` — groups of analyzer "functions" that jump into each other
  (hand-written asm); prints the region and entry list for a `[[regions]]` override.
- `scripts/rebuild.sh` — the whole pipeline, analyzer to runtime.
- `scripts/make_patches.sh` — regenerate patches 004-006 from the upstream working tree and
  verify the series reproduces it.
- `scripts/run_headless.ps1` — timed run with logs + VRAM snapshots (PNG), silent audio.
  E.g. `-Env @{PS1_AUTO_START='750'}` presses Start at the title; add `PS1_SHOT_DISPLAY='1'`
  to capture what the screen shows (24-bit FMV included) instead of all of VRAM.
- FMV reference: cut a movie's raw 2352-byte sectors out of the `.bin` (the file table is
  in the ISO9660 root, `/CINEMAS/*.STR`) and `ffmpeg -i X.str` decodes it (demuxer
  `psxstr`) -- ground truth to compare runtime frames against.

## Tests (upstream suite, Windows)

Recompiler 107/107. Runtime 480 pass (MDEC regression tests included); 4 fail on Windows file semantics in the tests
themselves (deleting a still-open temp file, a `/tmp` path). Analyzer tests fail creating
their fixture files on Windows -- untouched code, not investigated yet.

## Pipeline

    disc image  ->  PS1-EXE  ->  ps1Analyzer  ->  analyzer.toml + overrides.toml = game_config.toml
                                                      |
                                                      v
                                 ps1Recomp  ->  recompiled_out.cpp  (~150k lines)
                                                      |
                                                      v
                                 ps1Runtime  ->  native executable (SDL2 + OpenGL)

## Licence

GPL-3.0-or-later (see `LICENSE`). The patches in `patches/` modify
[PS1Recomp](https://github.com/PS1Recomp/ps1-recomp) (GPL-3.0-or-later, Italo Dell Areti).
Release builds also contain Dear ImGui, toml11, {fmt} (MIT) and SDL2 (zlib); their notices
ship in the release zip. The part of a release build that is recompiled from the game's
own code is not published as source -- it is regenerated from your own disc by this
repository's tools.
