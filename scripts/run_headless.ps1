# Run the recompiled game for a fixed time, capturing logs and VRAM snapshots.
# Usage: scripts\run_headless.ps1 -Out <dir> [-Seconds 45] [-ShotEvery 300] [-Env @{PS1_HLE_TRACE='1'}]
# Snapshots land in <dir> as PPM and are converted to PNG afterwards.
param(
    [Parameter(Mandatory)] [string] $Out,
    [int] $Seconds = 45,
    [int] $ShotEvery = 300,
    [hashtable] $Env = @{},
    # Defaults: the upstream clone next to this repo, game data two levels up
    # (the same layout scripts/rebuild.sh uses).
    [string] $Runtime = (Join-Path $PSScriptRoot "..\..\PS1Recomp-ps1-recomp\build\ps1Runtime\Release\ps1Runtime.exe"),
    [string] $Config = (Join-Path $PSScriptRoot "..\..\..\gamedata\build\game_config.toml")
)
New-Item -ItemType Directory -Force $Out | Out-Null
Get-ChildItem $Out -Include *.ppm, *.png, *.log -Recurse | Remove-Item -Force
if ($ShotEvery -gt 0) {
    $env:PS1_SHOT_DIR = $Out
    $env:PS1_SHOT_EVERY = "$ShotEvery"
}
# Headless runs are for logs and VRAM, not listening: no audio device.
$env:SDL_AUDIODRIVER = "dummy"
foreach ($k in $Env.Keys) { Set-Item "env:$k" $Env[$k] }
$p = Start-Process -FilePath $Runtime -ArgumentList '--config', $Config -WorkingDirectory $Out `
    -RedirectStandardOutput "$Out\out.log" -RedirectStandardError "$Out\err.log" -PassThru
$null = $p.Handle  # keep a handle so ExitCode survives
if (-not $p.WaitForExit($Seconds * 1000)) {
    Stop-Process -Id $p.Id -Force
    "stopped after ${Seconds}s"
} else {
    "exited with code $($p.ExitCode)"
}
python (Join-Path $PSScriptRoot "ppm2png.py") $Out
