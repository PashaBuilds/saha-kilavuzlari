# capture_shot.ps1 — tek karelik tam yakalama boru hatti:
#   Claude penceresini kucult -> Vivado'yu one getir -> bekle ->
#   on plandaki pencereyi PNG'ye al -> makul cozunurluge indir.
# Kullanim:
#   powershell -ExecutionPolicy Bypass -File capture_shot.ps1 -Out shot-NN.png
#   -NoFocus : on plani degistirme (diyalog zaten ondeyken)
param(
    [Parameter(Mandatory=$true)][string]$Out,
    [string]$Title = "",
    [switch]$Ekran,
    [switch]$NoFocus
)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinUtil {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
"@

# Claude penceresi gorunuyorsa kucult (ekran yakalamayi kirletmesin)
foreach ($p in (Get-Process claude -ErrorAction SilentlyContinue)) {
    if ($p.MainWindowHandle -ne 0) {
        [WinUtil]::ShowWindow($p.MainWindowHandle, 6) | Out-Null   # SW_MINIMIZE
    }
}

if (-not $NoFocus) {
    $v = Get-Process vivado -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if ($v) { [WinUtil]::SetForegroundWindow($v.MainWindowHandle) | Out-Null }
}
Start-Sleep -Milliseconds 900

$kok = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
if (-not [System.IO.Path]::IsPathRooted($Out)) {
    $Out = Join-Path $kok "assets\screenshots\$Out"
}
$ek = @()
if ($Title -ne "") { $ek += @("-Title", $Title) }
if ($Ekran) { $ek += "-Ekran" }
& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "capture_window.ps1") -Out $Out @ek
& python (Join-Path $kok "build\kucult.py") $Out
