# capture_window.ps1 — pencereyi PNG'ye yakalar.
# Varsayilan: PrintWindow (pencerenin kendi yuzeyi — ustune binenler goremez).
# DIKKAT: PrintWindow, sahipli diyaloglari ve gecici popup'lari ICERMEZ;
# onlar icin -Title ile diyalog penceresini hedefle ya da -Ekran ile
# pencere dikdortgenini ekrandan kopyala.
# Kullanim:
#   capture_window.ps1 -Out shot.png                     # on plandaki pencere
#   capture_window.ps1 -Out shot.png -Title "Re-customize IP"  # basliga gore pencere
#   capture_window.ps1 -Out shot.png -Ekran              # on plan pencere rect'ini ekrandan
#   capture_window.ps1 -Out shot.png -Full               # tum ekran
param(
    [Parameter(Mandatory=$true)][string]$Out,
    [string]$Title = "",
    [switch]$Ekran,
    [switch]$Full
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class Cap {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h, int attr, out RECT r, int size);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    public delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    public static IntPtr FindByTitle(string sub) {
        IntPtr bulunan = IntPtr.Zero;
        EnumWindows((h, l) => {
            if (!IsWindowVisible(h)) return true;
            var sb = new StringBuilder(512);
            GetWindowText(h, sb, 512);
            if (sb.ToString().IndexOf(sub, StringComparison.OrdinalIgnoreCase) >= 0) {
                bulunan = h; return false;
            }
            return true;
        }, IntPtr.Zero);
        return bulunan;
    }
}
"@
[Cap]::SetProcessDPIAware() | Out-Null

if ($Full) {
    $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
    $g.Dispose()
} elseif ($Ekran) {
    # pencere dikdortgenini EKRANDAN kopyala (gecici popup'lar dahil olur)
    $hwnd = if ($Title -ne "") { [Cap]::FindByTitle($Title) } else { [Cap]::GetForegroundWindow() }
    if ($hwnd -eq [IntPtr]::Zero) { Write-Error "Pencere bulunamadi: $Title"; exit 1 }
    $r = New-Object Cap+RECT
    $ok = [Cap]::DwmGetWindowAttribute($hwnd, 9, [ref]$r, [System.Runtime.InteropServices.Marshal]::SizeOf($r))
    if ($ok -ne 0) { [Cap]::GetWindowRect($hwnd, [ref]$r) | Out-Null }
    $w = $r.R - $r.L; $h = $r.B - $r.T
    if ($w -le 0 -or $h -le 0) { Write-Error "Pencere boyutu gecersiz"; exit 1 }
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
    $g.Dispose()
} else {
    $hwnd = if ($Title -ne "") { [Cap]::FindByTitle($Title) } else { [Cap]::GetForegroundWindow() }
    if ($hwnd -eq [IntPtr]::Zero) { Write-Error "Pencere bulunamadi: $Title"; exit 1 }
    $r = New-Object Cap+RECT
    # pencere cercevesi (golge haric): DWMWA_EXTENDED_FRAME_BOUNDS = 9
    $ok = [Cap]::DwmGetWindowAttribute($hwnd, 9, [ref]$r, [System.Runtime.InteropServices.Marshal]::SizeOf($r))
    $rw = New-Object Cap+RECT
    [Cap]::GetWindowRect($hwnd, [ref]$rw) | Out-Null
    $w = $rw.R - $rw.L; $h = $rw.B - $rw.T
    if ($w -le 0 -or $h -le 0) { Write-Error "Pencere boyutu gecersiz"; exit 1 }

    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $dc = $g.GetHdc()
    # PW_RENDERFULLCONTENT = 2 (donanim hizlandirmali yuzeyler dahil)
    $okPrint = [Cap]::PrintWindow($hwnd, $dc, 2)
    $g.ReleaseHdc($dc)
    $g.Dispose()
    if (-not $okPrint) { Write-Error "PrintWindow basarisiz"; exit 1 }

    # DWM cercevesi GetWindowRect'ten kucukse kirp (golge kenari at)
    if ($ok -eq 0) {
        $cx = $r.L - $rw.L; $cy = $r.T - $rw.T
        $cw = $r.R - $r.L;  $ch = $r.B - $r.T
        if ($cx -ge 0 -and $cy -ge 0 -and $cw -gt 0 -and $ch -gt 0 -and ($cx+$cw) -le $w -and ($cy+$ch) -le $h) {
            $kirp = $bmp.Clone((New-Object System.Drawing.Rectangle($cx, $cy, $cw, $ch)), $bmp.PixelFormat)
            $bmp.Dispose(); $bmp = $kirp
        }
    }
}

$dir = Split-Path -Parent $Out
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output "yakalandi: $Out ($($bmp.Width) x $($bmp.Height))"
$bmp.Dispose()
