#!/bin/sh
# Regenerate the Apocalypse config, recompile, and rebuild the Windows runtime.
# Usage: scripts/rebuild.sh
# Paths come from PS1RECOMP (upstream clone) and GAMEDATA (disc image + generated
# configs); by default ../PS1Recomp-ps1-recomp and ../../gamedata from this repo.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
UP=${PS1RECOMP:-$(cd "$HERE/.." && pwd)/PS1Recomp-ps1-recomp}
GAME=${GAMEDATA:-$(cd "$HERE/../.." && pwd)/gamedata}
OUT="$GAME/build"
EXE="$GAME/SLES_004.60"
CUE="$GAME/Apocalypse (Europe).cue"
mkdir -p "$OUT"
[ -f "$EXE" ] || python "$HERE/scripts/extract_exe.py" "$GAME/Apocalypse (Europe) (Track 1).bin" "$GAME"
"$UP/build/ps1Analyzer/Release/ps1Analyzer.exe" "$EXE" "$OUT/analyzer.toml" | tail -1
python "$HERE/scripts/merge_overrides.py" "$OUT/analyzer.toml" "$HERE/config/overrides.toml" \
    "$OUT/game_config.toml" --exe "$EXE" --cue "$CUE" --release "$OUT/game.toml"
"$UP/build/ps1Recomp/Release/ps1Recomp.exe" "$OUT/game_config.toml" \
    "$UP/ps1Runtime/src/recompiled_out.cpp" | grep -E "HLE functions|Success"
cmake --build "$UP/build" --config Release --target ps1Runtime --parallel | grep -E " error |ps1Runtime.vcxproj ->"
