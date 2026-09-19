#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures.py — hesaplanmış şekil üreticisi (yalnızca stdlib)

Spektrum/eğri içeren bazı SVG'lerin çizim verisi elle uydurulmaz; burada
scenario.json'dan beslenen bir hesapla üretilir ve tam SVG dosyası yazılır.
Üretilen dosyalar repoda commit'li durur (build her makinede deterministik).

  python build/gen_figures.py          # tüm üretilmiş şekilleri yeniden yaz
  python build/gen_figures.py g-142    # yalnızca birini

dsp-core.js'teki modellerin Python eşdeğerleri (nco, fft, pencere) buradadır;
tests/test_bilinen_cevap.py aynı formülleri sınar.
"""
import cmath
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "svg"
S = json.loads((ROOT / "data" / "scenario.json").read_text(encoding="utf-8"))
TAU = 2 * math.pi


# ------------------------------------------------------------------ DSP eşdeğerleri
def fft(x):
    n = len(x)
    if n == 1:
        return x
    if n & (n - 1):
        raise ValueError("N 2'nin kuvveti olmalı")
    e, o = fft(x[0::2]), fft(x[1::2])
    out = [0] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * o[k]
        out[k] = e[k] + t
        out[k + n // 2] = e[k] - t
    return out


def pencere(tip, N):
    if tip == "hann":
        return [0.5 - 0.5 * math.cos(TAU * k / N) for k in range(N)]
    if tip == "blackman-harris":
        a = (0.35875, 0.48829, 0.14128, 0.01168)
        return [a[0] - a[1] * math.cos(TAU * k / N) + a[2] * math.cos(2 * TAU * k / N) - a[3] * math.cos(3 * TAU * k / N) for k in range(N)]
    return [1.0] * N


def spektrum_dbfs(x, tip="blackman-harris"):
    """Kompleks dizi → dBFS (tam ölçek sinüs 0 dBFS), fftshift'li."""
    N = len(x)
    w = pencere(tip, N)
    s1 = sum(w)
    X = fft([x[k] * w[k] for k in range(N)])
    out = [20 * math.log10(max(abs(X[k]) / s1, 1e-15)) for k in range(N)]
    return out[N // 2:] + out[:N // 2]


def nco(n, N, P, A, ftw, dither=False, seed=7):
    """dsp-core DSP.nco eşdeğeri (Mulberry32 yerine basit LCG dither; yalnızca şekil için)."""
    acc, mod, lut, q = 0, 2 ** N, 2 ** P, 2 ** (A - 1)
    rnd = seed
    out = []
    for _ in range(n):
        faz_acc = acc
        if dither:
            rnd = (rnd * 1103515245 + 12345) % 2 ** 31
            faz_acc = (faz_acc + (rnd % 2 ** (N - P))) % mod
        adres = faz_acc * lut // mod
        faz = adres / lut * TAU
        out.append(complex(round(math.cos(faz) * (q - 1)) / q, round(math.sin(faz) * (q - 1)) / q))
        acc = (acc + ftw) % mod
    return out


def ftw_hesapla(f, fs, N):
    return round(f / fs * 2 ** N) % 2 ** N


# ------------------------------------------------------------------ SVG yardımcıları
def seyrelt(xs, ys, x0, x1, xmin, xmax):
    """Piksel sütunu başına tepe tutma (max) ile seyreltir — dosya boyutu için."""
    kova = {}
    for x, y in zip(xs, ys):
        px = int(x0 + (x - xmin) / (xmax - xmin) * (x1 - x0))
        if px not in kova or y > kova[px][1]:
            kova[px] = (x, y)
    ks = sorted(kova)
    return [kova[k][0] for k in ks], [kova[k][1] for k in ks]


def path_from(xs, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax):
    # x aralığı dışındaki noktalar atılır (panel dışına taşma olmasın)
    cift = [(x, y) for x, y in zip(xs, ys) if xmin <= x <= xmax]
    xs, ys = [c[0] for c in cift], [c[1] for c in cift]
    xs, ys = seyrelt(xs, ys, x0, x1, xmin, xmax)
    d = []
    for k, (x, y) in enumerate(zip(xs, ys)):
        px = x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)
        py = y0 - (max(ymin, min(ymax, y)) - ymin) / (ymax - ymin) * (y0 - y1)
        d.append(("M" if k == 0 else "L") + f"{px:.1f} {py:.1f}")
    return "".join(d)


def eksen(x0, x1, y0, y1, xt, yt, xmin, xmax, ymin, ymax, xfmt=str, yfmt=str):
    parts = []
    for v in xt:
        px = x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)
        parts.append(f'<line x1="{px:.1f}" y1="{y1}" x2="{px:.1f}" y2="{y0}" class="izgara"/>'
                     f'<text x="{px:.1f}" y="{y0 + 14}" text-anchor="middle" class="s-mono2">{xfmt(v)}</text>')
    for v in yt:
        py = y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
        parts.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" class="izgara"/>'
                     f'<text x="{x0 - 6}" y="{py + 4:.1f}" text-anchor="end" class="s-mono2">{yfmt(v)}</text>')
    parts.append(f'<rect x="{x0}" y="{y1}" width="{x1 - x0}" height="{y0 - y1}" class="eksen"/>')
    return "".join(parts)


# ------------------------------------------------------------------ şekiller
def g_142():
    """NCO faz kırpma spur'ları: P = 8 (dither yok) vs P = 8 + dither vs P = 14 — aynı 601 MHz tonu."""
    fs, N, A = S["adc"]["fs_hz"], S["ddc"]["akumulator_bit"], 16
    f = S["ddc"]["nco_hz"] + 1e6
    n = 2048
    paneller = [("P = 8 bit, dither yok", 8, False), ("P = 8 bit, dither açık", 8, True), ("P = 14 bit, dither açık", 14, True)]
    W, H = 900, 640
    px0, px1 = 60, W - 20
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-g142">',
           '<title id="t-g142">NCO çıkış spektrumu üç ayarda (hesaplanmış): P = 8 bit dither kapalı — periyodik faz kırpma spur\'ları ≈ −48 dBc; P = 8 bit dither açık — spur\'lar gürültüye dağılır; P = 14 bit dither açık — spur\'lar −84 dBc altında. Ton 601 MHz, fs 2400 MHz, A = 16 bit.</title>']
    ftw = ftw_hesapla(f, fs, N)
    for i, (ad, P, dit) in enumerate(paneller):
        y1 = 30 + i * 205
        y0 = y1 + 160
        sp = spektrum_dbfs(nco(n, N, P, A, ftw, dit))
        xs = [(k - n / 2) * fs / n / 1e6 for k in range(n)]
        xmin, xmax, ymin, ymax = -1200, 1200, -130, 5
        out.append(f'<text x="{px0}" y="{y1 - 8}" class="s-baslik">{ad}</text>')
        out.append(eksen(px0, px1, y0, y1, [-1200, -800, -400, 0, 400, 800, 1200], [0, -40, -80, -120], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        # gürültü/spur dolgusu ve çizgi
        d = path_from(xs, sp, px0, px1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}L{px1} {y0}L{px0} {y0}Z" class="spk-sinyal" opacity=".18"/>')
        out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.2"/>')
        # kestirim çizgisi
        kest = -6.02 * P
        py = y0 - (kest - ymin) / (ymax - ymin) * (y0 - y1)
        out.append(f'<line x1="{px0}" y1="{py:.1f}" x2="{px1}" y2="{py:.1f}" class="yol-gurultu"/>'
                   f'<text x="{px1 - 4}" y="{py - 5:.1f}" text-anchor="end" class="s-kucuk s-kirmizi">−6.02·P = {kest:.0f} dBc</text>')
        # ölçülen en büyük spur
        pk = max(range(n), key=lambda k: sp[k])
        spur = max((sp[k], k) for k in range(n) if abs(k - pk) > 6)
        sx = px0 + (xs[spur[1]] - xmin) / (xmax - xmin) * (px1 - px0)
        sy = y0 - (spur[0] - ymin) / (ymax - ymin) * (y0 - y1)
        sag = sx > (px0 + px1) / 2
        # etiket: spur kestirim çizgisine yakınsa altına, değilse (gürültü tabanı üstünde) üstüne; arka plan kutusuyla
        ust = (spur[0] - kest) < -6
        ty = (sy - 9) if ust else (sy + 14)
        met = f"en büyük spur {spur[0]:.0f} dBc"
        tw = len(met) * 5.8 + 6
        tx = (sx - 8) if sag else (sx + 8)
        rx = (tx - tw + 2) if sag else (tx - 3)
        out.append(f'<rect x="{rx:.1f}" y="{ty - 11:.1f}" width="{tw:.0f}" height="14" rx="2" fill="var(--dia-panel)" opacity=".9"/>')
        out.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="4" fill="var(--gold)"/>'
                   f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{"end" if sag else "start"}" class="s-kucuk s-altin">{met}</text>')
        out.append(f'<text x="{px1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">frekans (MHz) · dBFS</text>')
    out.append("</svg>")
    (SVG / "g-142-faz-kirpma-spektrum.svg").write_text("\n".join(out), encoding="utf-8")
    print("  ✓ g-142-faz-kirpma-spektrum.svg")


URETICILER = {"g-142": g_142}


def main():
    secim = sys.argv[1:] or list(URETICILER)
    for ad in secim:
        if ad not in URETICILER:
            print(f"  ? bilinmeyen: {ad}")
            continue
        URETICILER[ad]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
