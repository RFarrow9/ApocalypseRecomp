#!/bin/sh
# Regenerate patches/004-006 from the working tree of the upstream clone and
# prove the series (002..006) reproduces it on a pristine checkout.
#
# 002 and 003 are kept as they are (they are the base the later patches stack
# on); every file below is copied whole from the working tree, so a change to
# any of them lands in the patch that owns it.  Add new files to a list here.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
UP=${PS1RECOMP:-$(cd "$HERE/.." && pwd)/PS1Recomp-ps1-recomp}
P="$HERE/patches"
W="${TMPDIR:-/tmp}/ps1recomp-series"

RUNTIME="ps1Runtime/CMakeLists.txt
ps1Runtime/include/runtime/bios/bios.h
ps1Runtime/include/runtime/bios/card_fs.h
ps1Runtime/include/runtime/bios/file_io.h
ps1Runtime/include/runtime/cdrom/cdrom_controller.h
ps1Runtime/include/runtime/cdrom/xa_decoder.h
ps1Runtime/include/runtime/disc_setup.h
ps1Runtime/include/runtime/dma/dma.h
ps1Runtime/include/runtime/gpu/gpu.h
ps1Runtime/include/runtime/gte.h
ps1Runtime/include/runtime/input/input.h
ps1Runtime/include/runtime/gpu/renderer_opengl.h
ps1Runtime/include/runtime/mdec/mdec.h
ps1Runtime/include/runtime/memory.h
ps1Runtime/include/runtime/overlay.h
ps1Runtime/include/runtime/ps1_runtime_macros.h
ps1Runtime/include/runtime/psyq/psyq_hle.h
ps1Runtime/include/runtime/psyq/psyq_st.h
ps1Runtime/include/runtime/spu/spu.h
ps1Runtime/src/abi_check.cpp
ps1Runtime/src/bios/bios.cpp
ps1Runtime/src/bios/card_fs.cpp
ps1Runtime/src/bios/file_io.cpp
ps1Runtime/src/bios/syscall_a.cpp
ps1Runtime/src/bios/syscall_b.cpp
ps1Runtime/src/cdrom/cdrom_controller.cpp
ps1Runtime/src/cdrom/xa_decoder.cpp
ps1Runtime/src/disc_setup.cpp
ps1Runtime/src/dma/dma.cpp
ps1Runtime/src/gpu/gpu.cpp
ps1Runtime/src/gpu/renderer_opengl.cpp
ps1Runtime/src/gpu/renderer_hires.cpp
ps1Runtime/src/gte.cpp
ps1Runtime/src/input/input.cpp
ps1Runtime/src/main_host.cpp
ps1Runtime/src/mdec/mdec.cpp
ps1Runtime/src/overlay.cpp
ps1Runtime/src/psyq/psyq_hle.cpp
ps1Runtime/src/psyq/psyq_libcd.cpp
ps1Runtime/src/psyq/psyq_pad.cpp
ps1Runtime/src/psyq/psyq_registry.cpp
ps1Runtime/src/psyq/psyq_st.cpp
ps1Runtime/src/spu/spu.cpp
ps1Test/runtime/test_gpu_display.cpp
ps1Test/runtime/test_gpu_rasterizer.cpp
ps1Test/runtime/test_gpu_textures.cpp
ps1Test/runtime/test_mdec.cpp
ps1Test/runtime/test_card_fs.cpp
ps1Test/runtime/test_psyq_hle.cpp
ps1Test/runtime/test_psyq_pad.cpp
ps1Test/runtime/test_runtime_macros.cpp"

RECOMP="ps1Recomp/include/ps1recomp/instruction_emitter.h
ps1Recomp/src/dispatch_emitter.cpp
ps1Recomp/src/instruction_emitter.cpp
ps1Recomp/src/main.cpp
ps1Test/recompiler/test_forward_branch.cpp
ps1Test/recompiler/test_instruction_emitter.cpp"

TESTS="ps1Test/CMakeLists.txt
ps1Test/runtime/test_config.cpp"

cd "$UP"
rm -rf "$W"; git worktree prune
git worktree add -q --detach "$W" HEAD
cd "$W"
git apply "$P/002-windows-msvc-port.patch" "$P/003-div-hardware-semantics.patch"
git add -A; git -c user.name=x -c user.email=x commit -qm base

step() {
  name=$1; files=$2
  for f in $files; do mkdir -p "$(dirname "$W/$f")"; cp "$UP/$f" "$W/$f"; done
  git -C "$W" add -A
  git -C "$W" diff --cached > "$P/$name.patch"
  git -C "$W" -c user.name=x -c user.email=x commit -qm "$name"
  echo "$name: $(grep -c '^diff --git' "$P/$name.patch") files"
}
rm -f "$P"/004-*.patch "$P"/005-*.patch "$P"/006-*.patch
step 004-runtime-fixes-and-diagnostics "$RUNTIME"
step 005-recompiler-control-flow-and-gte "$RECOMP"
step 006-windows-test-portability "$TESTS"

# Every modified or added upstream file must now match the series result.
cd "$UP"
bad=0
for f in $(git diff --name-only HEAD; git ls-files --others --exclude-standard ps1Runtime ps1Recomp ps1Test | grep -v recompiled_out); do
  diff -q --strip-trailing-cr "$f" "$W/$f" >/dev/null 2>&1 || { echo "NOT IN SERIES: $f"; bad=1; }
done
git worktree remove --force "$W"
[ $bad = 0 ] && echo "series reproduces the working tree"
exit $bad
