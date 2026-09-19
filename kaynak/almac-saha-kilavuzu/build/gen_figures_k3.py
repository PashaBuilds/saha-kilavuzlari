#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k3.py — Kısım III (Bölüm 8–11) şekil üreticisi (yalnızca stdlib)

Hesaplanmış eğri içeren şekiller (g-81, g-90, g-91, g-92, g-93) ve blok/harita
şemaları (g-80, g-100 … g-112) buradan yazılır. Sayılar data/scenario.json'dan
ve dsp-core.js'in Python eşdeğerlerinden gelir (gen_figures.py yardımcıları).

  python build/gen_figures_k3.py           # hepsini yaz
  python build/gen_figures_k3.py g-91 g-93 # yalnızca seçilenleri
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_figures import S, SVG, fft, pencere, path_from, eksen, TAU  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FS = S["adc"]["fs_hz"]
IF = S["on_uc"]["if_hz"]
BIT = S["adc"]["bit"]
JIT = S["adc"]["jitter_s"]
RF = S["sinyal"]["rf_hz"]


# ------------------------------------------------------------------ yardımcılar
def katla(f, fs):
    """dsp-core DSP.katla eşdeğeri → (bölge, alias, evrik)"""
    nyq = fs / 2
    bolge = int(f // nyq) + 1
    r = math.fmod(f, fs)
    return bolge, (fs - r if r > nyq else r), bolge % 2 == 0


def snr_jitter(f, sigma):
    return -20 * math.log10(TAU * f * sigma)


def yaz(ad, parcalar):
    (SVG / ad).write_text("\n".join(parcalar), encoding="utf-8")
    print("  ✓", ad)


def bas(gid, W, H, title):
    return [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-{gid}">',
            f'<title id="t-{gid}">{title}</title>']


def poly(pts, kls, extra=""):
    return f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" class="{kls}" fill="none" {extra}/>'


def blok(x, y, w, h, etiket, kls="blok", alt=None, tkls="s-metin2", r=4):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" class="{kls}"/>']
    if alt:
        out.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 - 3:.1f}" text-anchor="middle" class="{tkls}">{etiket}</text>')
        out.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 11:.1f}" text-anchor="middle" class="s-kucuk">{alt}</text>')
    else:
        out.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 4:.1f}" text-anchor="middle" class="{tkls}">{etiket}</text>')
    return "".join(out)


def sym(ad, x, y, etiket=None, w=60, h=40, tkls="s-kucuk"):
    out = [f'<use href="#sym-{ad}" x="{x}" y="{y}" width="{w}" height="{h}"/>']
    if etiket:
        out.append(f'<text x="{x + w / 2:.1f}" y="{y + h + 13}" text-anchor="middle" class="{tkls}">{etiket}</text>')
    return "".join(out)


def ok(x1, y1, x2, y2, kls="yol-analog", marker="ok-analog"):
    return f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" class="{kls}" marker-end="url(#{marker})"/>'


# ------------------------------------------------------------------ g-80
def g_80():
    """Nyquist bölgeleri: düz eksen (üst) ve akordeon gibi katlanmış hali (alt)."""
    W, H = 900, 430
    fs = FS / 1e6
    out = bas("g80", W, H,
              "Nyquist bölgeleri ve katlanma, akordeon görünümü: üstte gerçek frekans ekseni 0–3·fs, altı bölgeye bölünmüş; "
              "her bölgede aynı asimetrik bant (alçak kenar A, yüksek kenar B). Altta eksen fs/2 katlarında akordeon gibi "
              "katlanır: tek bölgeler düz, çift bölgeler aynalı (A ile B yer değiştirir) olarak 0–fs/2 üzerine iner; en altta "
              "ADC çıkışında hepsinin üst üste bindiği tek bant. Referans senaryo: fs = 2400 MHz, IF 1800 MHz 2. bölgede, evrik.")
    x0, x1 = 70, 860
    zon = (x1 - x0) / 6
    # --- üst eksen
    yT = 110
    out.append(f'<text x="{x0}" y="24" class="s-baslik">Gerçek frekans ekseni — bölgeler (n−1)·fs/2 … n·fs/2</text>')
    for z in range(6):
        xa = x0 + z * zon
        kls = "blok-aktif" if z == 1 else "blok"
        out.append(f'<rect x="{xa:.1f}" y="{yT - 62}" width="{zon:.1f}" height="62" class="{kls}" opacity=".6"/>')
        out.append(f'<text x="{xa + zon / 2:.1f}" y="{yT - 48}" text-anchor="middle" class="s-kucuk">{z + 1}. bölge{" · evrik" if z % 2 else ""}</text>')
        # asimetrik bant: A alçak (kısa), B yüksek (uzun)
        a, b = xa + zon * 0.30, xa + zon * 0.70
        out.append(f'<polygon points="{a:.1f},{yT} {a:.1f},{yT - 12} {b:.1f},{yT - 36} {b:.1f},{yT}" class="spk-sinyal"/>')
        out.append(f'<text x="{a - 2:.1f}" y="{yT - 3}" text-anchor="end" class="s-kucuk s-vurgu">A</text>')
        out.append(f'<text x="{b + 2:.1f}" y="{yT - 3}" class="s-kucuk s-vurgu">B</text>')
    out.append(f'<path d="M{x0} {yT} H{x1}" class="eksen"/>')
    for z in range(7):
        xa = x0 + z * zon
        lab = ["0", "fs/2", "fs", "3fs/2", "2fs", "5fs/2", "3fs"][z]
        out.append(f'<path d="M{xa:.1f} {yT} v5" class="eksen"/><text x="{xa:.1f}" y="{yT + 17}" text-anchor="middle" class="s-kucuk">{lab}</text>')
        out.append(f'<text x="{xa:.1f}" y="{yT + 30}" text-anchor="middle" class="s-mono2">{int(z * fs / 2)}</text>')
    out.append(f'<text x="{x1}" y="{yT + 44}" text-anchor="end" class="s-kucuk">MHz (fs = {int(fs)})</text>')
    # IF işareti
    xif = x0 + IF / 1e6 / (fs / 2) * zon
    out.append(f'<path d="M{xif:.1f} {yT - 70} V{yT}" class="yol-analog"/>'
               f'<text x="{xif + 4:.1f}" y="{yT - 66}" class="s-kucuk s-altin">IF {int(IF / 1e6)}</text>')
    # --- akordeon
    ax0, ax1 = 70, 470
    sw = ax1 - ax0
    yA = 175
    dy = 30
    out.append(f'<text x="{ax0}" y="{yA - 12}" class="s-baslik">Akordeon: eksen fs/2 katlarında katlanır</text>')
    for z in range(6):
        y = yA + z * dy
        ters = z % 2 == 1
        out.append(f'<rect x="{ax0}" y="{y}" width="{sw}" height="{dy - 6}" class="{"blok-aktif" if z == 1 else "blok"}" opacity=".5"/>')
        a, b = 0.30, 0.70
        if ters:
            a, b = 1 - b, 1 - a  # aynalı: B solda, A sağda
            pts = f"{ax0 + a * sw:.1f},{y + dy - 6} {ax0 + a * sw:.1f},{y + 2} {ax0 + b * sw:.1f},{y + dy - 14} {ax0 + b * sw:.1f},{y + dy - 6}"
        else:
            pts = f"{ax0 + a * sw:.1f},{y + dy - 6} {ax0 + a * sw:.1f},{y + dy - 14} {ax0 + b * sw:.1f},{y + 2} {ax0 + b * sw:.1f},{y + dy - 6}"
        out.append(f'<polygon points="{pts}" class="spk-sinyal"/>')
        la, lb = ("B", "A") if ters else ("A", "B")
        out.append(f'<text x="{ax0 + a * sw - 3:.1f}" y="{y + dy - 8}" text-anchor="end" class="s-kucuk s-vurgu">{la}</text>')
        out.append(f'<text x="{ax0 + b * sw + 3:.1f}" y="{y + dy - 8}" class="s-kucuk s-vurgu">{lb}</text>')
        out.append(f'<text x="{ax1 + 8}" y="{y + dy / 2 + 1}" class="s-kucuk">{z + 1}. bölge → {"evrik" if ters else "düz"}</text>')
        # kıvrım
        if z < 5:
            if z % 2 == 0:
                out.append(f'<path d="M{ax1} {y + dy - 6} A 6 6 0 0 1 {ax1} {y + dy + 2}" class="yol-saat"/>')
            else:
                out.append(f'<path d="M{ax0} {y + dy - 6} A 6 6 0 0 0 {ax0} {y + dy + 2}" class="yol-saat"/>')
    # frekans yönü okları
    out.append(f'<text x="{ax0}" y="{yA + 6 * dy + 8}" class="s-kucuk">0</text><text x="{ax1}" y="{yA + 6 * dy + 8}" text-anchor="end" class="s-kucuk">fs/2</text>')
    # --- çıkış: hepsi üst üste
    ox0, ox1 = 590, 860
    ow = ox1 - ox0
    yO = 250
    out.append(f'<text x="{ox0}" y="{yA - 12}" class="s-baslik">ADC çıkışı (0 – fs/2)</text>')
    out.append(f'<text x="{ox0}" y="{yA + 4}" class="s-kucuk">tek bölge kalır; tek/çift kaynaklar</text>')
    out.append(f'<text x="{ox0}" y="{yA + 17}" class="s-kucuk">ayırt edilemez — AAF yalnızca birini bırakmalı</text>')
    a, b = 0.30, 0.70
    out.append(f'<polygon points="{ox0 + a * ow:.1f},{yO + 60} {ox0 + a * ow:.1f},{yO + 40} {ox0 + b * ow:.1f},{yO} {ox0 + b * ow:.1f},{yO + 60}" class="spk-sinyal"/>')
    out.append(f'<polygon points="{ox0 + a * ow:.1f},{yO + 60} {ox0 + a * ow:.1f},{yO} {ox0 + b * ow:.1f},{yO + 40} {ox0 + b * ow:.1f},{yO + 60}" class="spk-image"/>')
    out.append(f'<path d="M{ox0} {yO + 60} H{ox1}" class="eksen"/>')
    out.append(f'<text x="{ox0}" y="{yO + 76}" class="s-kucuk">0</text><text x="{ox1}" y="{yO + 76}" text-anchor="end" class="s-kucuk">fs/2</text>')
    out.append(f'<text x="{ox0}" y="{yO + 96}" class="s-kucuk s-vurgu">mavi: 1, 3, 5. bölge (düz)</text>')
    out.append(f'<text x="{ox0}" y="{yO + 110}" class="s-kucuk s-kirmizi">kırmızı: 2, 4, 6. bölge (aynalı)</text>')
    out.append(f'<text x="{ox0}" y="{yO + 132}" class="s-metin2">Senaryo: IF {int(IF / 1e6)} → {int(katla(IF, FS)[1] / 1e6)} MHz, evrik</text>')
    out.append(f'<text x="{ox0}" y="{yO + 148}" class="s-kucuk">(2. bölge; alt kenar 1650 → 750, üst kenar 1950 → 450)</text>')
    out.append("</svg>")
    yaz("g-80-nyquist-akordeon.svg", out)


# ------------------------------------------------------------------ g-81
def g_81():
    """Referans senaryonun katlanma haritası: IF bandı, HD2, HD3, image → 1. bölge."""
    W, H = 900, 400
    x0, x1 = 60, 870
    fmax = 6000.0
    px = lambda f: x0 + f / fmax * (x1 - x0)
    yT = 120
    out = bas("g81", W, H,
              "Referans senaryonun katlanma haritası: üstte gerçek frekans ekseni (0–6 GHz) üzerinde Nyquist bölgeleri, IF bandı "
              "1650–1950 MHz, HD2 bandı 3300–3900 MHz, HD3 bandı 4950–5850 MHz ve image 5.8 GHz; altta ADC çıkışında 1. bölgeye "
              "(0–1200 MHz) katlanmış halleri: sinyal 450–750 MHz evrik, HD2 900–1200 MHz, HD3 150–1050 MHz sinyalin üstüne biner, "
              "image AAF ile bastırılmazsa 1000 MHz")
    out.append(f'<text x="{x0}" y="22" class="s-baslik">Gerçek frekans (AAF girişi)</text>')
    for z in range(1, 6):
        a, b = (z - 1) * 600, z * 600
        kls = "blok-aktif" if z == 2 else "blok"
        out.append(f'<rect x="{px(a):.1f}" y="{yT - 70}" width="{px(b) - px(a):.1f}" height="70" class="{kls}" opacity=".55"/>')
        out.append(f'<text x="{(px(a) + px(b)) / 2:.1f}" y="{yT - 52}" text-anchor="middle" class="s-kucuk">{z}. bölge{" (evrik)" if z % 2 == 0 else ""}</text>')
    out.append(f'<path d="M{x0} {yT} H{x1}" class="eksen"/>')
    for f in range(0, 6001, 600):
        out.append(f'<path d="M{px(f):.1f} {yT} v5" class="eksen"/><text x="{px(f):.1f}" y="{yT + 17}" text-anchor="middle" class="s-kucuk">{f}</text>')
    out.append(f'<text x="{x1}" y="{yT + 32}" text-anchor="end" class="s-kucuk">MHz · fs/2 = 1200, fs = 2400</text>')

    def bant(a, b, y, h, kls, etiket, kls2="s-kucuk"):
        out.append(f'<rect x="{px(a):.1f}" y="{y}" width="{max(3, px(b) - px(a)):.1f}" height="{h}" class="{kls}"/>')
        out.append(f'<text x="{(px(a) + px(b)) / 2:.1f}" y="{y - 4}" text-anchor="middle" class="{kls2}">{etiket}</text>')
    bant(1650, 1950, yT - 40, 40, "spk-sinyal", "IF bandı 1650–1950", "s-kucuk s-vurgu")
    bant(3300, 3900, yT - 26, 26, "spk-image", "HD2 3300–3900", "s-kucuk s-kirmizi")
    bant(4950, 5850, yT - 18, 18, "spk-image", "HD3 4950–5850", "s-kucuk s-kirmizi")
    out.append(f'<path d="M{px(5800):.1f} {yT - 64} V{yT}" class="yol-gurultu"/><text x="{px(5800) + 4:.1f}" y="{yT - 56}" class="s-kucuk s-kirmizi">image 5800 (mixer)</text>')
    # AAF eğrisi (öğretici: bant içinde 0, dışında 0.25 dB/MHz, 60 dB'de doyar)
    pts = []
    for k in range(401):
        f = k * 15.0
        att = 0 if 1650 <= f <= 1950 else min(60, 0.25 * (abs(f - 1800) - 150))
        pts.append((px(f), yT - 66 + att))
    out.append(poly(pts, "spk-filtre"))
    out.append(f'<text x="{px(2300):.1f}" y="{yT - 70}" class="s-kucuk s-altin">AAF (bant geçiren) yanıtı</text>')
    yB = 330
    for f in (1800, 3600, 5400, 5800):
        _, al, _ = katla(f * 1e6, FS)
        kls, mk = ("yol-sayisal", "ok-sayisal") if f == 1800 else ("yol-gurultu", "ok-gurultu")
        out.append(f'<path d="M{px(f):.1f} {yT + 22} C {px(f):.1f} {yT + 120}, {px(al / 1e6):.1f} {yB - 140}, {px(al / 1e6):.1f} {yB - 72}" class="{kls}" marker-end="url(#{mk})"/>')
    pxb = lambda f: x0 + f / 1200 * (x1 - x0)
    out.append(f'<text x="{x0}" y="{yB - 78}" class="s-baslik">ADC çıkışı — 1. bölgeye katlanmış (0–fs/2)</text>')
    out.append(f'<rect x="{x0}" y="{yB - 60}" width="{x1 - x0}" height="60" class="blok" opacity=".4"/>')
    out.append(f'<path d="M{x0} {yB} H{x1}" class="eksen"/>')
    for f in range(0, 1201, 150):
        out.append(f'<path d="M{pxb(f):.1f} {yB} v5" class="eksen"/><text x="{pxb(f):.1f}" y="{yB + 17}" text-anchor="middle" class="s-kucuk">{f}</text>')
    out.append(f'<text x="{x1}" y="{yB + 32}" text-anchor="end" class="s-kucuk">MHz</text>')

    def bantb(a, b, y, h, kls, etiket, kls2="s-kucuk"):
        out.append(f'<rect x="{pxb(a):.1f}" y="{y}" width="{max(3, pxb(b) - pxb(a)):.1f}" height="{h}" class="{kls}"/>')
        out.append(f'<text x="{(pxb(a) + pxb(b)) / 2:.1f}" y="{y - 4}" text-anchor="middle" class="{kls2}">{etiket}</text>')
    bantb(150, 1050, yB - 14, 14, "spk-image", "HD3 → 150–1050 (3× genişler, bandın üstüne biner)", "s-kucuk s-kirmizi")
    bantb(900, 1200, yB - 30, 16, "spk-image", "HD2 → 900–1200", "s-kucuk s-kirmizi")
    bantb(450, 750, yB - 58, 44, "spk-sinyal", "sinyal → 450–750, EVRİK (alt kenar 1950 → 450)", "s-kucuk s-vurgu")
    out.append(f'<path d="M{pxb(1000):.1f} {yB - 60} V{yB}" class="yol-gurultu"/><text x="{pxb(1000) + 3:.1f}" y="{yB - 40}" class="s-kucuk s-kirmizi">image → 1000 (AAF ~−60 dB)</text>')
    out.append(f'<text x="{pxb(600):.1f}" y="{yB + 50}" text-anchor="middle" class="s-metin2">fs/4 = 600 MHz: NCO buraya kurulur; HD3 ve 2-yollu interleaving image tam buraya katlanır</text>')
    out.append("</svg>")
    yaz("g-81-katlanma-haritasi.svg", out)


# ------------------------------------------------------------------ g-90
def g_90():
    """3 bitlik kuantizör merdiveni, hata sinyali ve tekdüze hata modeli."""
    W, H = 900, 330
    bits = 3
    q = 2 ** (bits - 1)
    n = 64
    x = [0.92 * math.sin(TAU * 1.37 * k / n + 0.4) for k in range(n)]
    y = [max(-q, min(q - 1, round(v * q))) / q for v in x]
    e = [b - a for a, b in zip(x, y)]
    L = dict(x0=50, x1=560, y0=170, y1=30)
    px = lambda k: L["x0"] + k / (n - 1) * (L["x1"] - L["x0"])
    py = lambda v: L["y0"] - (v + 1) / 2 * (L["y0"] - L["y1"])
    out = bas("g90", W, H,
              "Kuantizasyon merdiveni ve hata sinyali: solda 3 bitlik kuantizörün 8 basamağı üzerinde sürekli sinüs (altın) ve "
              "kuantalanmış örnekler (mavi merdiven); altta hata sinyali e[n] = y − x, ±LSB/2 arasında; sağda hatanın olasılık "
              "yoğunluğu (tekdüze) ve varyansı LSB²/12, buradan SNR = 6.02·N + 1.76 dB")
    out.append(f'<text x="{L["x0"]}" y="18" class="s-baslik">3 bitlik kuantizör: 2³ = 8 seviye, LSB = FS/8</text>')
    for lev in range(-q, q):
        yy = py(lev / q)
        out.append(f'<path d="M{L["x0"]} {yy:.1f} H{L["x1"]}" class="izgara"/>')
        out.append(f'<text x="{L["x0"] - 6}" y="{yy + 4:.1f}" text-anchor="end" class="s-mono2">{lev & 7:03b}</text>')
    out.append(f'<rect x="{L["x0"]}" y="{L["y1"]}" width="{L["x1"] - L["x0"]}" height="{L["y0"] - L["y1"]}" class="eksen"/>')
    pts = [(px(k * (n - 1) / 399), py(0.92 * math.sin(TAU * 1.37 * (k * (n - 1) / 399) / n + 0.4))) for k in range(400)]
    out.append(poly(pts, "yol-analog"))
    d = ""
    for k in range(n):
        d += ("M" if k == 0 else "L") + f"{px(k - 0.5):.1f} {py(y[k]):.1f}L{px(k + 0.5):.1f} {py(y[k]):.1f}"
    out.append(f'<path d="{d}" class="yol-sayisal"/>')
    ya, yb = py(1 / q), py(2 / q)
    out.append(f'<path d="M{L["x1"] + 10} {ya:.1f} V{yb:.1f}" class="yol-kontrol" marker-end="url(#ok-kontrol)" marker-start="url(#ok-kontrol)"/>'
               f'<text x="{L["x1"] + 16}" y="{(ya + yb) / 2 + 4:.1f}" class="s-kucuk s-yesil">1 LSB</text>')
    out.append(f'<text x="{L["x0"]}" y="{L["y0"] + 16}" class="s-kucuk">x(t) sürekli (altın) · y[n] kuantalanmış (mavi merdiven) · örnek n →</text>')
    E = dict(x0=50, x1=560, y0=300, y1=215)
    pye = lambda v: E["y0"] - (v + 0.5 / q) / (1 / q) * (E["y0"] - E["y1"])
    out.append(f'<rect x="{E["x0"]}" y="{E["y1"]}" width="{E["x1"] - E["x0"]}" height="{E["y0"] - E["y1"]}" class="eksen"/>')
    out.append(f'<path d="M{E["x0"]} {pye(0):.1f} H{E["x1"]}" class="izgara"/>')
    out.append(f'<text x="{E["x0"] - 6}" y="{E["y1"] + 4}" text-anchor="end" class="s-kucuk">+½ LSB</text><text x="{E["x0"] - 6}" y="{E["y0"] + 4}" text-anchor="end" class="s-kucuk">−½ LSB</text>')
    out.append(poly([(px(k), pye(e[k])) for k in range(n)], "yol-gurultu"))
    for k in range(n):
        out.append(f'<circle cx="{px(k):.1f}" cy="{pye(e[k]):.1f}" r="1.8" class="spk-image"/>')
    out.append(f'<text x="{E["x0"]}" y="{E["y1"] - 6}" class="s-metin2">hata e[n] = y[n] − x[n]: sinyale bağlı ama "gürültü gibi" davranır (küçük bit sayısında örüntü görünür)</text>')
    R = dict(x0=640, x1=860, y0=170, y1=60)
    out.append(f'<text x="{R["x0"]}" y="{R["y1"] - 30}" class="s-baslik">Hata dağılımı (model)</text>')
    out.append(f'<rect x="{R["x0"]}" y="{R["y1"]}" width="{R["x1"] - R["x0"]}" height="{R["y0"] - R["y1"]}" class="eksen"/>')
    out.append(f'<rect x="{R["x0"] + 40}" y="{R["y1"] + 20}" width="{R["x1"] - R["x0"] - 80}" height="{R["y0"] - R["y1"] - 20}" class="spk-gurultu"/>')
    out.append(f'<text x="{R["x0"] + 40}" y="{R["y0"] + 14}" text-anchor="middle" class="s-kucuk">−½ LSB</text><text x="{R["x1"] - 40}" y="{R["y0"] + 14}" text-anchor="middle" class="s-kucuk">+½ LSB</text>')
    out.append(f'<text x="{(R["x0"] + R["x1"]) / 2}" y="{R["y1"] + 14}" text-anchor="middle" class="s-kucuk">p(e) = 1/LSB (tekdüze)</text>')
    out.append(f'<text x="{R["x0"]}" y="{R["y0"] + 40}" class="s-metin2">σ² = LSB²/12</text>')
    out.append(f'<text x="{R["x0"]}" y="{R["y0"] + 60}" class="s-metin2">tam ölçek sinüs: P = FS²/8</text>')
    out.append(f'<text x="{R["x0"]}" y="{R["y0"] + 80}" class="s-metin2">oran → 1.5 · 2^(2N)</text>')
    out.append(f'<text x="{R["x0"]}" y="{R["y0"] + 102}" class="s-metin s-vurgu" style="font-weight:700">SNR = 6.02·N + 1.76 dB</text>')
    out.append(f'<text x="{R["x0"]}" y="{R["y0"] + 122}" class="s-kucuk">N = 3 → 19.8 dB · N = {BIT} → {6.02 * BIT + 1.76:.1f} dB</text>')
    out.append("</svg>")
    yaz("g-90-kuantizasyon-merdiveni.svg", out)


# ------------------------------------------------------------------ g-91
def g_91():
    """Açıklamalı ADC FFT grafiği (kurgusal 14-bit cihaz, tek ton testi)."""
    N = 4096
    fs = FS
    rnd = random.Random(7)
    fb = 1178
    f1 = fb * fs / N
    A = 10 ** (-1 / 20)
    snr_hedef = 57.0
    sigma = A / math.sqrt(2) / 10 ** (snr_hedef / 20)
    q = 2 ** (BIT - 1)
    x = []
    for k in range(N):
        t = k / fs
        v = A * math.cos(TAU * f1 * t)
        v += A * 10 ** (-80 / 20) * math.cos(TAU * 2 * f1 * t + 0.7)
        v += A * 10 ** (-72 / 20) * math.cos(TAU * 3 * f1 * t + 1.1)
        v += A * 10 ** (-76 / 20) * math.cos(TAU * (fs / 2 - f1) * t)
        v += 10 ** (-84 / 20) * math.cos(TAU * (fs / 2 - 1.5 * fs / N) * t)
        v += rnd.gauss(0, sigma)
        x.append(max(-q, min(q - 1, round(v * q))) / q)
    w = pencere("blackman-harris", N)
    s1 = sum(w)
    X = fft([complex(x[k] * w[k], 0) for k in range(N)])
    sp = [20 * math.log10(max(abs(X[k]) * 2 / s1, 1e-12)) for k in range(N // 2 + 1)]
    M = len(sp)
    f = [k * fs / N / 1e6 for k in range(M)]
    pk = max(range(M), key=lambda k: sp[k])
    yb = lambda fr: int(round(fr / fs * N))
    hd2b, hd3b, ilb = yb(katla(2 * f1, fs)[1]), yb(katla(3 * f1, fs)[1]), yb(fs / 2 - f1)
    P = [10 ** (v / 10) for v in sp]
    mask = [True] * M
    for k in range(max(0, pk - 8), pk + 9):
        mask[k] = False
    for k in range(4):
        mask[k] = False
    for b in (hd2b, hd3b, ilb):
        for k in range(max(0, b - 3), min(M, b + 4)):
            mask[k] = False
    nm = sum(mask)
    Pn = sum(P[k] for k in range(M) if mask[k]) * M / nm
    Ps = sum(P[pk - 8:pk + 9])
    snr = 10 * math.log10(Ps / Pn)
    en_kotu = max(max(sp[b - 3:b + 4]) for b in (hd2b, hd3b, ilb))
    sfdr = sp[pk] - en_kotu
    gur = sorted(P[k] for k in range(M) if mask[k])
    taban = 10 * math.log10(gur[len(gur) // 2])
    pg = 10 * math.log10(N / 2)
    nsd = -(snr + 10 * math.log10(fs / 2)) + sp[pk]
    print(f"    g-91: f1={f1 / 1e6:.1f} MHz tepe={sp[pk]:.2f} dBFS SNR={snr:.1f} SFDR={sfdr:.1f} taban={taban:.1f} PG={pg:.1f} NSD={nsd:.1f}")
    W, H = 900, 400
    G = dict(x0=62, x1=880, y0=330, y1=40)
    px = lambda fm: G["x0"] + fm / 1200 * (G["x1"] - G["x0"])
    py = lambda db: G["y0"] - (db + 130) / 140 * (G["y0"] - G["y1"])
    out = bas("g91", W, H,
              f"Açıklamalı ADC FFT grafiği: {BIT} bit, fs = {int(fs / 1e6)} MSPS, N = {N} nokta, Blackman-Harris pencere; temel ton "
              f"{f1 / 1e6:.0f} MHz −1 dBFS, HD3 {katla(3 * f1, fs)[1] / 1e6:.0f} MHz en kötü spur, HD2 {katla(2 * f1, fs)[1] / 1e6:.0f} MHz, "
              f"2-yollu interleaving image {(fs / 2 - f1) / 1e6:.0f} MHz; SFDR oku ≈ {sfdr:.0f} dBc; FFT gürültü tabanı ≈ {taban:.0f} dBFS, "
              f"SNR (tüm bant) ≈ {snr:.0f} dB; ikisi arasındaki fark FFT işlem kazancı 10·log10(N/2) ≈ {pg:.1f} dB (pencere ENBW'si "
              f"yaklaşık 3 dB geri alır); NSD ≈ {nsd:.0f} dBFS/Hz")
    out.append(f'<text x="{G["x0"]}" y="22" class="s-baslik">Kurgusal {BIT}-bit ADC, fs = {int(fs / 1e6)} MSPS, N = {N}, Blackman-Harris — tek ton testi</text>')
    for db in range(-130, 11, 20):
        out.append(f'<path d="M{G["x0"]} {py(db):.1f} H{G["x1"]}" class="izgara"/><text x="{G["x0"] - 6}" y="{py(db) + 4:.1f}" text-anchor="end" class="s-kucuk">{db}</text>')
    for fm in range(0, 1201, 200):
        out.append(f'<path d="M{px(fm):.1f} {G["y1"]} V{G["y0"]}" class="izgara"/><text x="{px(fm):.1f}" y="{G["y0"] + 16}" text-anchor="middle" class="s-kucuk">{fm}</text>')
    out.append(f'<rect x="{G["x0"]}" y="{G["y1"]}" width="{G["x1"] - G["x0"]}" height="{G["y0"] - G["y1"]}" class="eksen"/>')
    out.append(f'<text x="{(G["x0"] + G["x1"]) / 2}" y="{G["y0"] + 32}" text-anchor="middle" class="s-kucuk">frekans (MHz) — 1. Nyquist bölgesi</text>')
    out.append(f'<text x="14" y="{(G["y0"] + G["y1"]) / 2}" text-anchor="middle" transform="rotate(-90 14 {(G["y0"] + G["y1"]) / 2})" class="s-kucuk">dBFS (bin başına)</text>')
    step = 3
    xs = [f[i] for i in range(0, M, step)]
    ys = [max(sp[i:i + step]) for i in range(0, M, step)]
    dd = f"M{px(xs[0]):.1f} {py(-130):.1f}" + "".join(f"L{px(a):.1f} {py(max(-130, b)):.1f}" for a, b in zip(xs, ys)) + f"L{px(xs[-1]):.1f} {py(-130):.1f}Z"
    out.append(f'<path d="{dd}" class="spk-gurultu"/>')
    out.append(poly([(px(a), py(max(-130, b))) for a, b in zip(xs, ys)], "yol-sayisal", 'style="stroke-width:1"'))
    out.append(f'<path d="M{px(f[pk]):.1f} {py(-130):.1f} V{py(sp[pk]):.1f}" style="stroke:var(--accent);stroke-width:2.4"/>')
    out.append(f'<text x="{px(f[pk]) + 6:.1f}" y="{py(sp[pk]) + 4:.1f}" class="s-metin s-vurgu">temel ton {f1 / 1e6:.0f} MHz, {sp[pk]:.1f} dBFS</text>')
    for b, ad in ((hd3b, "HD3 (en kötü spur)"), (ilb, "interleaving image fs/2 − f_in"), (hd2b, "HD2")):
        seg = sp[b - 3:b + 4]
        v = max(seg)
        bb = b - 3 + seg.index(v)
        out.append(f'<path d="M{px(f[bb]):.1f} {py(-130):.1f} V{py(v):.1f}" style="stroke:var(--red);stroke-width:2"/>')
        out.append(f'<text x="{px(f[bb]) + 5:.1f}" y="{py(v) - 6:.1f}" class="s-kucuk s-kirmizi">{ad} {v:.0f} dBFS</text>')
    out.append(f'<text x="{px(1130):.1f}" y="{py(-84) - 8:.1f}" text-anchor="end" class="s-kucuk s-kirmizi">offset spur → fs/2</text>')
    xk = px(f[pk]) - 30
    out.append(f'<path d="M{xk:.1f} {py(sp[pk]):.1f} V{py(en_kotu):.1f}" class="yol-kontrol" marker-end="url(#ok-kontrol)" marker-start="url(#ok-kontrol)"/>')
    out.append(f'<text x="{xk - 6:.1f}" y="{(py(sp[pk]) + py(en_kotu)) / 2:.1f}" text-anchor="end" class="s-metin2 s-yesil">SFDR ≈ {sfdr:.0f} dBc</text>')
    out.append(f'<path d="M{G["x0"]} {py(en_kotu):.1f} H{G["x1"]}" class="yol-saat"/>')
    snr_line = sp[pk] - snr
    out.append(f'<path d="M{G["x0"]} {py(snr_line):.1f} H{G["x1"]}" class="spk-filtre"/>')
    out.append(f'<text x="{G["x0"] + 8}" y="{py(snr_line) - 5:.1f}" class="s-kucuk s-altin">toplam gürültü gücü (tüm bant, tek sayı): {snr_line:.0f} dBFS → SNR = {snr:.0f} dB</text>')
    out.append(f'<path d="M{G["x0"]} {py(taban):.1f} H{G["x1"]}" class="spk-filtre"/>')
    out.append(f'<text x="{G["x0"] + 8}" y="{py(taban) + 13:.1f}" class="s-kucuk s-altin">FFT gürültü tabanı (bin başına) ≈ {taban:.0f} dBFS · NSD ≈ {nsd:.0f} dBFS/Hz</text>')
    xa = px(300)
    out.append(f'<path d="M{xa:.1f} {py(snr_line):.1f} V{py(taban):.1f}" class="yol-kontrol" marker-end="url(#ok-kontrol)" marker-start="url(#ok-kontrol)"/>')
    out.append(f'<text x="{xa + 6:.1f}" y="{(py(snr_line) + py(taban)) / 2 + 4:.1f}" class="s-metin2 s-yesil">FFT işlem kazancı 10·log(N/2) = {pg:.1f} dB (− pencere ENBW ≈ 3 dB)</text>')
    out.append(f'<text x="{G["x0"]}" y="{H - 8}" class="s-kucuk">Değerler kurgusal bir cihazı temsil eder; kalıp gerçek datasheet grafikleriyle aynıdır. Gürültü gri dolgu, sinyal mavi, spur kırmızı, seviye çizgileri altın kesikli.</text>')
    out.append("</svg>")
    yaz("g-91-adc-fft-aciklamali.svg", out)


# ------------------------------------------------------------------ g-92
def g_92():
    """Jitter SNR tavanı eğri ailesi (log frekans ekseni)."""
    W, H = 900, 380
    G = dict(x0=62, x1=870, y0=320, y1=40)
    px = lambda f: G["x0"] + (math.log10(f) - 8) / 2 * (G["x1"] - G["x0"])
    py = lambda db: G["y0"] - (db - 30) / 70 * (G["y0"] - G["y1"])
    ref = snr_jitter(IF, JIT)
    drf = snr_jitter(RF, JIT)
    kotu = snr_jitter(IF, 5 * JIT)
    out = bas("g92", W, H,
              "Aperture jitter SNR eğri ailesi: yatay eksen giriş frekansı 100 MHz–10 GHz (logaritmik), düşey eksen SNR tavanı; "
              "σ = 50, 100, 200, 500 fs için −20·log10(2π·f·σ) doğruları (frekans iki katına çıkınca 6 dB düşer); yatay çizgiler "
              f"14 ve 12 bit ideal kuantizasyon SNR'ı (86.0 ve 74.0 dB); referans senaryo çalışma noktası {IF / 1e9:.1f} GHz IF, "
              f"{JIT * 1e15:.0f} fs → {ref:.1f} dB; direct RF örneklemede {RF / 1e9:.1f} GHz, {JIT * 1e15:.0f} fs → {drf:.1f} dB")
    out.append(f'<text x="{G["x0"]}" y="22" class="s-baslik">Jitter SNR tavanı: SNR_j = −20·log10(2π · f_in · σ_j)</text>')
    for db in range(30, 101, 10):
        out.append(f'<path d="M{G["x0"]} {py(db):.1f} H{G["x1"]}" class="izgara"/><text x="{G["x0"] - 6}" y="{py(db) + 4:.1f}" text-anchor="end" class="s-kucuk">{db}</text>')
    for dec in (1e8, 1e9, 1e10):
        for m in range(1, 10):
            f = dec * m
            if f > 1e10:
                break
            out.append(f'<path d="M{px(f):.1f} {G["y1"]} V{G["y0"]}" class="izgara"/>')
            if m in (1, 2, 5):
                lab = f"{f / 1e9:g} GHz" if f >= 1e9 else f"{f / 1e6:.0f} MHz"
                out.append(f'<text x="{px(f):.1f}" y="{G["y0"] + 16}" text-anchor="middle" class="s-kucuk">{lab}</text>')
    out.append(f'<rect x="{G["x0"]}" y="{G["y1"]}" width="{G["x1"] - G["x0"]}" height="{G["y0"] - G["y1"]}" class="eksen"/>')
    out.append(f'<text x="{(G["x0"] + G["x1"]) / 2}" y="{G["y0"] + 32}" text-anchor="middle" class="s-kucuk">giriş frekansı f_in (Hz, log) — fs değil!</text>')
    out.append(f'<text x="14" y="{(G["y0"] + G["y1"]) / 2}" text-anchor="middle" transform="rotate(-90 14 {(G["y0"] + G["y1"]) / 2})" class="s-kucuk">SNR (dB)</text>')
    for n in (14, 12):
        v = 6.02 * n + 1.76
        out.append(f'<path d="M{G["x0"]} {py(v):.1f} H{G["x1"]}" class="spk-filtre"/>')
        out.append(f'<text x="{G["x1"] - 6}" y="{py(v) - 5:.1f}" text-anchor="end" class="s-kucuk s-altin">{n} bit ideal kuantizasyon = {v:.1f} dB</text>')
    for sig, op in ((50, 1.0), (100, 1.0), (200, 0.75), (500, 0.55)):
        pts = []
        for k in range(61):
            f = 10 ** (8 + 2 * k / 60)
            pts.append((px(f), py(snr_jitter(f, sig * 1e-15))))
        out.append(poly(pts, "yol-sayisal", f'style="opacity:{op}"'))
        fl = 1.3e8
        out.append(f'<text x="{px(fl):.1f}" y="{py(snr_jitter(fl, sig * 1e-15)) - 6:.1f}" class="s-kucuk s-vurgu">σ = {sig} fs</text>')
    for f, sig, lab, dy in ((IF, JIT, f"referans: IF {IF / 1e9:.1f} GHz, {JIT * 1e15:.0f} fs → {ref:.1f} dB", -14),
                            (RF, JIT, f"direct RF: {RF / 1e9:.1f} GHz, {JIT * 1e15:.0f} fs → {drf:.1f} dB", 22),
                            (IF, 5 * JIT, f"kötü saat: {5 * JIT * 1e15:.0f} fs → {kotu:.1f} dB", 22)):
        v = snr_jitter(f, sig)
        out.append(f'<circle cx="{px(f):.1f}" cy="{py(v):.1f}" r="5" style="fill:var(--gold);stroke:var(--bg);stroke-width:1.5"/>')
        sag = f > 5e9
        out.append(f'<text x="{px(f) + (-8 if sag else 8):.1f}" y="{py(v) + dy:.1f}" text-anchor="{"end" if sag else "start"}" class="s-kucuk s-altin">{lab}</text>')
    sig86 = 10 ** (-(6.02 * BIT + 1.76) / 20) / (TAU * IF)
    out.append(f'<text x="{G["x0"]}" y="{H - 8}" class="s-kucuk">Okuma: f_in 2× → −6 dB; σ 2× → −6 dB. {BIT} bitin {6.02 * BIT + 1.76:.0f} dB\'sini {IF / 1e9:.1f} GHz\'te görmek için σ ≈ {sig86 * 1e15:.1f} fs gerekir — pratikte erişilmez; jitter GHz girişte baskın terimdir.</text>')
    out.append("</svg>")
    yaz("g-92-jitter-snr.svg", out)


# ------------------------------------------------------------------ g-93
def g_93():
    """Time-interleaving hata mekanizması: 4 çekirdek, offset/kazanç/zamanlama uyumsuzluğu → spektrum."""
    W, H = 900, 420
    fs = FS
    M = 4
    N = 2048
    f1 = 384 * fs / N  # 450 MHz, tam bin
    ofs = [0.0, 0.0025, -0.0015, 0.002]
    kaz = [1.0, 0.994, 1.004, 0.997]
    tau = [0.0, 3e-12, -2e-12, 1.5e-12]
    rnd = random.Random(3)
    q = 2 ** (BIT - 1)
    x = []
    A = 10 ** (-1 / 20)
    for n in range(N):
        k = n % M
        v = kaz[k] * A * math.cos(TAU * f1 * (n / fs + tau[k])) + ofs[k] + rnd.gauss(0, 1e-4)
        x.append(max(-q, min(q - 1, round(v * q))) / q)
    w = pencere("blackman-harris", N)
    s1 = sum(w)
    X = fft([complex(x[k] * w[k], 0) for k in range(N)])
    sp = [20 * math.log10(max(abs(X[k]) * 2 / s1, 1e-12)) for k in range(N // 2 + 1)]
    Mb = len(sp)
    out = bas("g93", W, H,
              "Time-interleaving spur mekanizması: solda zaman domaini — dört ADC çekirdeği (A, B, C, D) sırayla örnekler; "
              "B çekirdeğinin offset'i ve kazancı farklı, D'nin örnekleme anı kaymış. Sağda çıkış spektrumu (hesaplanmış, fs = 2400 MSPS, "
              "giriş tonu 450 MHz −1 dBFS): offset uyumsuzluğu k·fs/4 = 600 ve 1200 MHz'de sinyalden bağımsız tonlar; kazanç ve "
              "zamanlama uyumsuzluğu k·fs/4 ± f_in konumlarında (150, 750, 1050 MHz) sinyalin image'ları.")
    # --- sol: zaman
    Lx0, Lx1, Ly0, Ly1 = 50, 400, 250, 60
    out.append(f'<text x="{Lx0}" y="24" class="s-baslik">Zaman: 4 çekirdek sırayla (A B C D A B …)</text>')
    out.append(f'<rect x="{Lx0}" y="{Ly1}" width="{Lx1 - Lx0}" height="{Ly0 - Ly1}" class="eksen"/>')
    nT = 16
    pxT = lambda n: Lx0 + 12 + n * (Lx1 - Lx0 - 24) / (nT - 1)
    pyT = lambda v: (Ly0 + Ly1) / 2 - v * (Ly0 - Ly1) / 2.4
    pts = [(pxT(k / 25), pyT(A * math.cos(TAU * f1 * (k / 25) / fs))) for k in range(25 * (nT - 1) + 1)]
    out.append(poly(pts, "yol-analog"))
    harf = "ABCD"
    for n in range(nT):
        k = n % M
        vid = A * math.cos(TAU * f1 * n / fs)
        v = kaz[k] * 6 * A * math.cos(TAU * f1 * (n / fs + tau[k] * 60)) + ofs[k] * 40  # hata görünür olsun diye abartılı
        v = vid + (v - 6 * A * math.cos(TAU * f1 * n / fs)) / 6 * 6
        kls = "spk-sinyal" if k == 0 or k == 2 else "spk-image"
        out.append(f'<path d="M{pxT(n):.1f} {pyT(0):.1f} V{pyT(v):.1f}" class="yol-sayisal" style="stroke-width:1"/>')
        out.append(f'<circle cx="{pxT(n):.1f}" cy="{pyT(v):.1f}" r="4" class="{kls}"/>')
        out.append(f'<text x="{pxT(n):.1f}" y="{Ly0 + 14}" text-anchor="middle" class="s-mono2">{harf[k]}</text>')
    out.append(f'<path d="M{Lx0} {pyT(0):.1f} H{Lx1}" class="izgara"/>')
    out.append(f'<text x="{Lx0}" y="{Ly0 + 32}" class="s-kucuk">her çekirdek fs/4 = {int(fs / 4e6)} MSPS ile örnekler; abartılı çizim</text>')
    out.append(f'<text x="{Lx0}" y="{Ly0 + 50}" class="s-kucuk s-kirmizi">B: offset + kazanç farkı · D: örnekleme anı kaymış (skew)</text>')
    out.append(f'<text x="{Lx0}" y="{Ly0 + 68}" class="s-kucuk">→ hata dizisi fs/4 periyotludur → spektrumda fs/4 aralıklı aile</text>')
    # tablo
    ty = Ly0 + 92
    out.append(f'<text x="{Lx0}" y="{ty}" class="s-metin2">Uyumsuzluk → spur konumu</text>')
    for i, (a, b) in enumerate((("offset", "k·fs/M (sinyalden bağımsız)"), ("kazanç", "k·fs/M ± f_in"), ("zamanlama", "k·fs/M ± f_in (f_in ile büyür)"))):
        out.append(f'<text x="{Lx0}" y="{ty + 16 * (i + 1)}" class="s-kucuk"><tspan class="s-kirmizi">{a}</tspan>  →  {b}</text>')
    # --- sağ: spektrum
    G = dict(x0=470, x1=880, y0=330, y1=60)
    px = lambda fm: G["x0"] + fm / 1200 * (G["x1"] - G["x0"])
    py = lambda db: G["y0"] - (db + 120) / 130 * (G["y0"] - G["y1"])
    out.append(f'<text x="{G["x0"]}" y="24" class="s-baslik">Spektrum: M = 4, f_in = {f1 / 1e6:.0f} MHz (hesaplanmış)</text>')
    for db in range(-120, 11, 20):
        out.append(f'<path d="M{G["x0"]} {py(db):.1f} H{G["x1"]}" class="izgara"/><text x="{G["x0"] - 6}" y="{py(db) + 4:.1f}" text-anchor="end" class="s-kucuk">{db}</text>')
    for fm in range(0, 1201, 300):
        out.append(f'<path d="M{px(fm):.1f} {G["y1"]} V{G["y0"]}" class="izgara"/><text x="{px(fm):.1f}" y="{G["y0"] + 16}" text-anchor="middle" class="s-kucuk">{fm}</text>')
    out.append(f'<rect x="{G["x0"]}" y="{G["y1"]}" width="{G["x1"] - G["x0"]}" height="{G["y0"] - G["y1"]}" class="eksen"/>')
    out.append(f'<text x="{(G["x0"] + G["x1"]) / 2}" y="{G["y0"] + 32}" text-anchor="middle" class="s-kucuk">frekans (MHz) · dBFS</text>')
    step = 2
    xs = [k * fs / N / 1e6 for k in range(0, Mb, step)]
    ys = [max(sp[i:i + step]) for i in range(0, Mb, step)]
    dd = f"M{px(xs[0]):.1f} {py(-120):.1f}" + "".join(f"L{px(a):.1f} {py(max(-120, b)):.1f}" for a, b in zip(xs, ys)) + f"L{px(xs[-1]):.1f} {py(-120):.1f}Z"
    out.append(f'<path d="{dd}" class="spk-gurultu"/>')
    out.append(poly([(px(a), py(max(-120, b))) for a, b in zip(xs, ys)], "yol-sayisal", 'style="stroke-width:1"'))
    etiketler = [(f1, "f_in", "s-vurgu", 0), (fs / 4, "fs/4 (offset)", "s-kirmizi", 0), (fs / 2, "fs/2 (offset)", "s-kirmizi", -1),
                 (fs / 4 - f1, "fs/4 − f_in", "s-kirmizi", 0), (fs / 4 + f1, "fs/4 + f_in", "s-kirmizi", 0), (fs / 2 - f1, "fs/2 − f_in", "s-kirmizi", 0)]
    for fr, ad, kls, yon in etiketler:
        b = int(round(fr / fs * N))
        seg = sp[max(0, b - 2):b + 3]
        v = max(seg)
        stroke = "var(--accent)" if kls == "s-vurgu" else "var(--red)"
        out.append(f'<path d="M{px(fr / 1e6):.1f} {py(-120):.1f} V{py(v):.1f}" style="stroke:{stroke};stroke-width:2"/>')
        anchor = "end" if yon < 0 else "middle"
        out.append(f'<text x="{px(fr / 1e6) + (-4 if yon < 0 else 0):.1f}" y="{py(v) - 7:.1f}" text-anchor="{anchor}" class="s-kucuk {kls}">{ad}</text>')
        out.append(f'<text x="{px(fr / 1e6) + (-4 if yon < 0 else 0):.1f}" y="{py(v) - 18:.1f}" text-anchor="{anchor}" class="s-mono2">{v:.0f}</text>')
    out.append(f'<text x="{G["x0"]}" y="{H - 8}" class="s-kucuk">Referans senaryoda f_in = 600 MHz = fs/4 olduğundan fs/4 offset spur\'u ve fs/2 − f_in image\'ı sinyalin tam üstüne düşer (Bölüm 8, tuzak).</text>')
    out.append("</svg>")
    yaz("g-93-interleaving-spur.svg", out)


# ------------------------------------------------------------------ g-100
def g_100():
    """ADC mimarileri hız–çözünürlük haritası (yaklaşık bölgeler)."""
    W, H = 900, 420
    G = dict(x0=70, x1=860, y0=350, y1=50)
    px = lambda fsps: G["x0"] + (math.log10(fsps) - 3) / 8 * (G["x1"] - G["x0"])
    py = lambda bit: G["y0"] - (bit - 4) / 22 * (G["y0"] - G["y1"])
    out = bas("g100", W, H,
              "ADC mimarileri hız–çözünürlük haritası (yaklaşık, öğretici bölgeler): yatay eksen örnekleme hızı 1 kSPS–100 GSPS "
              "logaritmik, düşey eksen çözünürlük bit. Sigma-delta yüksek çözünürlük düşük hız; SAR orta hız orta-yüksek çözünürlük; "
              "pipeline yüksek hız 12–16 bit; flash çok yüksek hız 6–8 bit; time-interleaved pipeline/SAR bölgeyi GSPS'e uzatır. "
              "Direct RF-sampling ADC bölgesi 1–10 GSPS, 12–14 bit; referans senaryo 2.4 GSPS 14 bit işaretli.")
    out.append(f'<text x="{G["x0"]}" y="24" class="s-baslik">ADC mimarileri: hız ↔ çözünürlük (yaklaşık bölgeler, öğretici)</text>')
    for e in range(3, 12):
        f = 10 ** e
        out.append(f'<path d="M{px(f):.1f} {G["y1"]} V{G["y0"]}" class="izgara"/>')
        lab = {3: "1 k", 4: "10 k", 5: "100 k", 6: "1 M", 7: "10 M", 8: "100 M", 9: "1 G", 10: "10 G", 11: "100 G"}[e]
        out.append(f'<text x="{px(f):.1f}" y="{G["y0"] + 16}" text-anchor="middle" class="s-kucuk">{lab}</text>')
    for b in range(4, 27, 2):
        out.append(f'<path d="M{G["x0"]} {py(b):.1f} H{G["x1"]}" class="izgara"/><text x="{G["x0"] - 6}" y="{py(b) + 4:.1f}" text-anchor="end" class="s-kucuk">{b}</text>')
    out.append(f'<rect x="{G["x0"]}" y="{G["y1"]}" width="{G["x1"] - G["x0"]}" height="{G["y0"] - G["y1"]}" class="eksen"/>')
    out.append(f'<text x="{(G["x0"] + G["x1"]) / 2}" y="{G["y0"] + 34}" text-anchor="middle" class="s-kucuk">örnekleme hızı (SPS, log)</text>')
    out.append(f'<text x="16" y="{(G["y0"] + G["y1"]) / 2}" text-anchor="middle" transform="rotate(-90 16 {(G["y0"] + G["y1"]) / 2})" class="s-kucuk">çözünürlük (bit)</text>')
    # bölgeler: (ad, fs_min, fs_max, bit_min, bit_max, sınıf)
    bolgeler = [("ΣΔ (sigma-delta)", 1e3, 2e7, 16, 24, "spk-filtre", "s-altin"),
                ("SAR", 1e4, 1e8, 10, 20, "spk-sinyal", "s-vurgu"),
                ("pipeline", 2e7, 1.5e9, 10, 16, "spk-sinyal", "s-vurgu"),
                ("time-interleaved (pipeline/SAR)", 1e9, 2e10, 8, 14, "spk-image", "s-kirmizi"),
                ("flash", 1e9, 1e11, 4, 8, "spk-gurultu", "s-metin2")]
    for ad, fa, fb, ba, bb, kls, tk in bolgeler:
        cx, cy = (px(fa) + px(fb)) / 2, (py(ba) + py(bb)) / 2
        rx, ry = (px(fb) - px(fa)) / 2, (py(ba) - py(bb)) / 2
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" class="{kls}" opacity=".45"/>')
        out.append(f'<text x="{cx:.1f}" y="{cy + 4:.1f}" text-anchor="middle" class="s-kucuk {tk}">{ad}</text>')
    # direct RF bölgesi
    xa, xb, ya, yb = px(1e9), px(1.2e10), py(14.5), py(11.5)
    out.append(f'<rect x="{xa:.1f}" y="{yb:.1f}" width="{xb - xa:.1f}" height="{ya - yb:.1f}" rx="6" fill="none" stroke="var(--green)" stroke-width="1.6" stroke-dasharray="6 4"/>')
    out.append(f'<text x="{xb - 4:.1f}" y="{yb - 6:.1f}" text-anchor="end" class="s-kucuk s-yesil">direct RF-sampling ADC bölgesi (≈ 1–10 GSPS, 12–14 bit)</text>')
    out.append(f'<circle cx="{px(FS):.1f}" cy="{py(BIT):.1f}" r="6" style="fill:var(--gold);stroke:var(--bg);stroke-width:1.5"/>')
    out.append(f'<text x="{px(FS) + 10:.1f}" y="{py(BIT) + 14:.1f}" class="s-kucuk s-altin">referans senaryo: {FS / 1e9:.1f} GSPS, {BIT} bit</text>')
    # ENOB notu
    out.append(f'<text x="{G["x0"] + 8}" y="{G["y1"] + 16}" class="s-kucuk">Eğilim: hız 10× ↑ ≈ çözünürlük 2–3 bit ↓ (aperture jitter ve güç sınırı). Etiketteki bit ≠ ENOB.</text>')
    out.append(f'<text x="{G["x0"]}" y="{H - 8}" class="s-kucuk">Sınırlar kesin değildir; üreticiler bölgeleri sürekli genişletir. Konum yalnızca "hangi mimari nerede yaşar" sezgisi içindir.</text>')
    out.append("</svg>")
    yaz("g-100-adc-mimari-haritasi.svg", out)


# ------------------------------------------------------------------ g-101
def g_101():
    """Jenerik direct RF-sampling ADC iç blok şeması."""
    W, H = 1000, 380
    out = bas("g101", W, H,
              "Jenerik direct RF-sampling ADC iç blok şeması: analog giriş tamponu ve track-and-hold (altın), M yollu time-interleaved "
              "ADC çekirdekleri, interleave kalibrasyon bloğu; sayısal tarafta (mavi) çip içi DDC — NCO, kompleks mixer, decimation "
              "filtreleri — ve JESD204 verici (lane'ler). Saat girişi, çip içi PLL/bölücü ve SYSREF gri kesikli; SPI/register ve "
              "kalibrasyon kontrolü yeşil. Bypass yolu: DDC atlanıp tam hız reel örnek çıkışı.")
    out.append('<text x="20" y="24" class="s-baslik">Direct RF-sampling ADC — jenerik iç yapı (blok adları üreticiye göre değişir)</text>')
    # analog bölüm zemini
    out.append('<rect x="20" y="40" width="300" height="200" rx="8" class="blok" opacity=".35"/>')
    out.append('<text x="30" y="56" class="s-kucuk s-altin">ANALOG</text>')
    out.append('<rect x="330" y="40" width="470" height="200" rx="8" class="blok" opacity=".35"/>')
    out.append('<text x="340" y="56" class="s-kucuk s-vurgu">SAYISAL (çip içi)</text>')
    out.append('<rect x="810" y="40" width="170" height="200" rx="8" class="blok" opacity=".35"/>')
    out.append('<text x="820" y="56" class="s-kucuk s-vurgu">ARAYÜZ</text>')
    y = 120
    out.append(f'<text x="22" y="{y + 4}" class="s-kucuk s-altin">RF / IF</text>')
    out.append(ok(60, y, 78, y))
    out.append(sym("amp", 80, y - 20, "giriş tamponu"))
    out.append(ok(140, y, 158, y))
    out.append(blok(160, y - 20, 50, 40, "T/H", "blok-analog"))
    out.append(f'<text x="185" y="{y + 34}" text-anchor="middle" class="s-kucuk">örnekle-tut</text>')
    # interleaved çekirdekler
    for i, dy in enumerate((-40, -13, 14, 41)):
        out.append(f'<path d="M210 {y} L232 {y + dy}" class="yol-analog"/>')
        out.append(f'<use href="#sym-adc" x="234" y="{y + dy - 12}" width="40" height="24"/>')
        out.append(f'<path d="M274 {y + dy} L296 {y}" class="yol-sayisal"/>')
    out.append(f'<text x="254" y="{y + 70}" text-anchor="middle" class="s-kucuk">M çekirdek, her biri fs/M</text>')
    out.append(f'<text x="254" y="{y + 84}" text-anchor="middle" class="s-kucuk">(time-interleaved)</text>')
    out.append(blok(300, y - 20, 22, 40, "", "blok"))
    out.append(f'<text x="311" y="{y + 3}" text-anchor="middle" class="s-mono2" transform="rotate(-90 311 {y + 3})">MUX</text>')
    out.append(ok(322, y, 342, y, "yol-sayisal", "ok-sayisal"))
    out.append(blok(344, y - 22, 76, 44, "IL kalibrasyon", "blok", "offset/kazanç/skew"))
    out.append(ok(420, y, 440, y, "yol-sayisal", "ok-sayisal"))
    # DDC
    out.append('<rect x="442" y="66" width="300" height="118" rx="6" fill="none" stroke="var(--accent)" stroke-dasharray="5 4"/>')
    out.append('<text x="450" y="80" class="s-kucuk s-vurgu">DDC (kanal başına; 1–N kanal)</text>')
    out.append(sym("mixer-d", 460, y - 20, "kompleks mixer"))
    out.append(sym("nco", 460, y + 36, "NCO", w=60, h=30))
    out.append(f'<path d="M490 {y + 36} V{y + 20}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    out.append(ok(520, y, 538, y, "yol-sayisal", "ok-sayisal"))
    out.append(sym("lpf", 540, y - 20, "filtre"))
    out.append(ok(600, y, 618, y, "yol-sayisal", "ok-sayisal"))
    out.append(sym("dec", 620, y - 20, "decimation ÷D"))
    out.append(ok(680, y, 700, y, "yol-sayisal", "ok-sayisal"))
    out.append(f'<text x="708" y="{y - 6}" class="s-kucuk s-vurgu">I/Q</text><text x="708" y="{y + 8}" class="s-kucuk">fs/D</text>')
    # bypass
    out.append(f'<path d="M430 {y - 34} H760 V{y + 60} H812" class="yol-sayisal" stroke-dasharray="4 3" marker-end="url(#ok-sayisal)"/>')
    out.append(f'<text x="600" y="{y - 40}" text-anchor="middle" class="s-kucuk">bypass: reel örnek, tam fs</text>')
    out.append(ok(740, y, 812, y, "yol-sayisal", "ok-sayisal"))
    # JESD
    out.append(blok(814, 70, 150, 100, "JESD204B/C TX", "blok-aktif", "transport · scrambler · link · PHY"))
    for i in range(4):
        out.append(f'<path d="M964 {90 + i * 20} H990" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    out.append('<text x="964" y="184" text-anchor="end" class="s-kucuk">L lane × 6–25 Gb/s</text>')
    out.append('<text x="964" y="198" text-anchor="end" class="s-kucuk">→ FPGA GT</text>')
    # saat
    yc = 300
    out.append(sym("saat", 40, yc - 20, "CLK girişi (fs veya fs/k)"))
    out.append(f'<path d="M100 {yc} H140" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(blok(142, yc - 20, 110, 40, "PLL / bölücü", "blok", "çip içi (opsiyonel)"))
    out.append(f'<path d="M252 {yc} H700" class="yol-saat"/>')
    out.append(f'<path d="M254 {yc} V{y + 48}" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(f'<text x="262" y="{yc - 8}" class="s-kucuk">örnekleme saati → T/H ve çekirdekler; sayısal saat → DDC, JESD</text>')
    out.append(f'<path d="M700 {yc} V190" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(f'<path d="M889 {yc} V172" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(f'<path d="M700 {yc} H889" class="yol-saat"/>')
    out.append(f'<text x="860" y="{yc + 18}" class="s-kucuk">SYSREF → LMFC/LEMC</text>')
    out.append(f'<path d="M820 {yc + 30} H889 V{yc}" class="yol-saat"/>')
    # kontrol
    out.append(sym("reg", 40, yc + 30, "SPI / register", h=30))
    out.append(f'<path d="M100 {yc + 45} H382 V{y + 22}" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    out.append(f'<path d="M382 {yc + 45} H490 V{y + 66}" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    out.append(f'<text x="400" y="{yc + 60}" class="s-kucuk s-yesil">kalibrasyon başlat/izle · NCO FTW · decimation · JESD parametreleri</text>')
    out.append("</svg>")
    yaz("g-101-direct-rf-adc-blok.svg", out)


# ------------------------------------------------------------------ g-102
def g_102():
    """RFSoC RF-ADC tile yapısı (jenerik)."""
    W, H = 1000, 400
    out = bas("g102", W, H,
              "RFSoC RF-ADC tile yapısı, jenerik gösterim: bir tile içinde birden çok RF-ADC bloğu; her blokta ADC çekirdeği, "
              "eşik dedektörü, QMC/ofset düzeltme, NCO'lu kompleks mixer, decimation ve FIFO; çıkış PL'ye AXI-Stream ile sabit "
              "genişlikte paralel örnek sözcükleri olarak gider. Tile ortak kaynakları: giriş saati, çip içi PLL, SYSREF girişi ve "
              "çok tile senkronizasyonu. PS, RF Data Converter sürücüsü ile AXI-Lite üzerinden yapılandırır. Blok sayısı ve adlar "
              "nesle göre değişir; bkz. PG269.")
    out.append('<text x="20" y="24" class="s-baslik">RFSoC RF-ADC tile — jenerik yapı (aynı silikonda: RF-ADC + PL + PS)</text>')
    out.append('<rect x="20" y="40" width="700" height="290" rx="10" class="blok" opacity=".35"/>')
    out.append('<text x="30" y="58" class="s-metin2">ADC tile</text>')
    for i in range(2):
        y0 = 70 + i * 120
        out.append(f'<rect x="40" y="{y0}" width="660" height="100" rx="6" class="blok"/>')
        out.append(f'<text x="48" y="{y0 + 14}" class="s-kucuk">RF-ADC blok {i}</text>')
        yc = y0 + 55
        out.append(f'<text x="14" y="{yc + 4}" class="s-kucuk s-altin">RF{i}</text>')
        out.append(ok(40, yc, 58, yc))
        out.append(sym("adc", 60, yc - 20, "ADC çekirdeği"))
        out.append(ok(120, yc, 138, yc, "yol-sayisal", "ok-sayisal"))
        out.append(blok(140, yc - 18, 66, 36, "eşik / QMC", "blok-aktif", "ofset-kazanç"))
        out.append(ok(206, yc, 224, yc, "yol-sayisal", "ok-sayisal"))
        out.append(sym("mixer-d", 226, yc - 20, "mixer"))
        out.append(f'<use href="#sym-nco" x="226" y="{yc + 34}" width="60" height="26"/>')
        out.append(f'<path d="M256 {yc + 34} V{yc + 20}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
        out.append(f'<text x="292" y="{yc + 52}" class="s-kucuk">NCO (48 bit FTW)</text>')
        out.append(ok(286, yc, 304, yc, "yol-sayisal", "ok-sayisal"))
        out.append(sym("dec", 306, yc - 20, "decimation"))
        out.append(ok(366, yc, 384, yc, "yol-sayisal", "ok-sayisal"))
        out.append(sym("fifo", 386, yc - 20, "FIFO"))
        out.append(ok(446, yc, 464, yc, "yol-sayisal", "ok-sayisal"))
        out.append(blok(466, yc - 18, 110, 36, "AXI-Stream", "blok-aktif", "N örnek/saat, 16 bit"))
        out.append(f'<path d="M576 {yc} H760" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
        out.append(f'<text x="600" y="{yc - 6}" class="s-kucuk">tdata[16·N−1:0], tvalid</text>')
        out.append(f'<text x="600" y="{yc + 14}" class="s-kucuk">reel ya da I/Q (mixer moduna göre)</text>')
    # tile ortak
    out.append('<rect x="40" y="290" width="660" height="34" rx="6" class="blok"/>')
    out.append('<text x="48" y="311" class="s-kucuk">tile ortak: </text>')
    out.append(sym("saat", 110, 293, None, w=40, h=28))
    out.append('<text x="156" y="311" class="s-kucuk">ADC_CLK girişi → PLL/bölücü → örnekleme saati</text>')
    out.append('<text x="430" y="311" class="s-kucuk">SYSREF girişi · çok tile senkron (MTS)</text>')
    out.append('<path d="M110 290 V270" class="yol-saat"/><path d="M110 270 H90 V110" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append('<path d="M90 230 H90" class="yol-saat"/><path d="M90 200 V230" class="yol-saat" marker-end="url(#ok-saat)"/>')
    # PL / PS
    out.append('<rect x="770" y="40" width="210" height="130" rx="8" class="blok-aktif" opacity=".7"/>')
    out.append('<text x="875" y="66" text-anchor="middle" class="s-metin2 s-vurgu">PL (FPGA kumaşı)</text>')
    out.append('<text x="875" y="86" text-anchor="middle" class="s-kucuk">DDC devamı · kanallaştırma</text>')
    out.append('<text x="875" y="102" text-anchor="middle" class="s-kucuk">FFT · tespit · PDW (Kısım V–VIII)</text>')
    out.append('<text x="875" y="122" text-anchor="middle" class="s-kucuk">saat: AXI-Stream çıkış saati</text>')
    out.append('<text x="875" y="138" text-anchor="middle" class="s-kucuk">(fs / N, ör. 300 MHz için N = 8)</text>')
    out.append('<rect x="770" y="220" width="210" height="110" rx="8" class="blok-kontrol"/>')
    out.append('<text x="875" y="246" text-anchor="middle" class="s-metin2 s-yesil">PS (Arm çekirdekleri)</text>')
    out.append('<text x="875" y="266" text-anchor="middle" class="s-kucuk">RF Data Converter sürücüsü</text>')
    out.append('<text x="875" y="282" text-anchor="middle" class="s-kucuk">NCO frekansı · decimation · eşik</text>')
    out.append('<text x="875" y="298" text-anchor="middle" class="s-kucuk">kalibrasyon · MTS · durum</text>')
    out.append('<path d="M770 275 H720 V200 H700" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    out.append('<text x="726" y="250" class="s-kucuk s-yesil" transform="rotate(-90 726 250)">AXI-Lite</text>')
    out.append('<path d="M875 170 V220" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    out.append('<text x="882" y="200" class="s-kucuk s-yesil">AXI / DMA</text>')
    out.append(f'<text x="20" y="{H - 24}" class="s-kucuk">Referans senaryo eşlemesi: RF{0} ← IF {int(IF / 1e6)} MHz, fs {int(FS / 1e6)} MSPS, mixer NCO {int(S["ddc"]["nco_hz"] / 1e6)} MHz, decimation ÷{S["ddc"]["decimation_toplam"]} → PL\'ye 300 MSPS I/Q.</text>')
    out.append(f'<text x="20" y="{H - 8}" class="s-kucuk">Jenerik şema; blok sayısı, bit genişliği ve özellikler nesle/ürüne göre değişir — güncel ürün kılavuzuna bakın (doğrulanmadı).</text>')
    out.append("</svg>")
    yaz("g-102-rfsoc-tile.svg", out)


# ------------------------------------------------------------------ g-103
def g_103():
    """Süperhet + IF örnekleme ile direct RF sampling, aynı senaryo, yan yana."""
    W, H = 1000, 380
    fs2 = 5.0e9
    b2, al2, ev2 = katla(RF, fs2)
    out = bas("g103", W, H,
              f"Aynı senaryo için iki almaç zinciri yan yana. Üstte süperhet + IF örnekleme (referans): anten, limiter, LNA, preselector, "
              f"mixer + LO {S['on_uc']['lo_ghz']} GHz, IF filtre {IF / 1e9:.1f} GHz, IF yükselteç, AAF, ADC {int(FS / 1e6)} MSPS, FPGA'da DDC. "
              f"Altta direct RF sampling: anten, limiter, LNA, bant seçici filtre, (opsiyonel) sürücü, RF ADC ≈ {fs2 / 1e9:.0f} GSPS "
              f"(örnek; {RF / 1e9:.1f} GHz {b2}. Nyquist bölgesinde, alias {al2 / 1e6:.0f} MHz{', evrik' if ev2 else ''}) ve çip içi DDC. "
              f"Silinen bloklar: mixer, LO sentezleyici, IF filtre, IF yükselteç. Kalanlar: limiter, LNA, bant seçici filtre, saat kalitesi ihtiyacı (artar).")
    out.append('<text x="20" y="22" class="s-baslik">Aynı darbe, iki zincir — üstte süperhet + IF örnekleme (referans senaryo), altta direct RF sampling</text>')

    def zincir(y, sira, baslik, kls_bas):
        out.append(f'<text x="20" y="{y - 36}" class="s-metin2 {kls_bas}">{baslik}</text>')
        x = 20
        for ad, et, tip in sira:
            if tip == "sil":
                out.append(f'<rect x="{x}" y="{y - 22}" width="60" height="44" rx="4" fill="none" stroke="var(--red)" stroke-dasharray="4 3"/>')
                out.append(f'<text x="{x + 30}" y="{y - 2}" text-anchor="middle" class="s-kucuk s-kirmizi">{ad}</text>')
                out.append(f'<text x="{x + 30}" y="{y + 12}" text-anchor="middle" class="s-kucuk s-kirmizi">silindi</text>')
            else:
                out.append(sym(ad, x, y - 20, et, tkls="s-kucuk"))
            if tip == "sayisal":
                out.append(ok(x + 60, y, x + 78, y, "yol-sayisal", "ok-sayisal"))
            elif tip != "son":
                out.append(ok(x + 60, y, x + 78, y))
            x += 80
        return x
    # üst
    y1 = 100
    sira1 = [("anten", "anten", "a"), ("limiter", "limiter", "a"), ("amp", "LNA", "a"), ("bpf", "preselector", "a"),
             ("mixer", f"mixer", "a"), ("bpf", f"IF filtre {IF / 1e9:.1f} GHz", "a"), ("amp", "IF yükselteç", "a"),
             ("bpf", "AAF (2. bölge)", "a"), ("adc", f"ADC {int(FS / 1e6)} MSPS", "sayisal"), ("fft", "FPGA: DDC…", "son")]
    xe = zincir(y1, sira1, "A · Süperhet + IF örnekleme", "s-altin")
    # LO
    out.append(f'<use href="#sym-lo" x="340" y="{y1 + 40}" width="60" height="30"/>')
    out.append(f'<path d="M370 {y1 + 40} V{y1 + 22}" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(f'<text x="406" y="{y1 + 60}" class="s-kucuk">LO {S["on_uc"]["lo_ghz"]} GHz (low-side)</text>')
    out.append(f'<use href="#sym-saat" x="660" y="{y1 + 40}" width="60" height="30"/>')
    out.append(f'<path d="M690 {y1 + 40} V{y1 + 22}" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(f'<text x="726" y="{y1 + 60}" class="s-kucuk">saat {int(FS / 1e6)} MHz, σ ≈ {JIT * 1e15:.0f} fs → jitter SNR {snr_jitter(IF, JIT):.1f} dB</text>')
    out.append(f'<text x="20" y="{y1 + 92}" class="s-kucuk">RF {RF / 1e9:.1f} GHz → IF {IF / 1e9:.1f} GHz → 2. bölge → {int(S["adc"]["alias_mhz"])} MHz evrik · image {S["on_uc"]["image_ghz"]} GHz preselector ile bastırılır · ADC giriş BW ≥ 2 GHz yeter</text>')
    # alt
    y2 = 250
    sira2 = [("anten", "anten", "a"), ("limiter", "limiter", "a"), ("amp", "LNA", "a"), ("bpf", "bant seçici (X-bant)", "a"),
             ("mixer", "mixer", "sil"), ("bpf", "IF filtre", "sil"), ("amp", "sürücü (ops.)", "a"),
             ("bpf", "AAF (4. bölge)", "a"), ("adc", f"RF ADC ≈ {fs2 / 1e9:.0f} GSPS", "sayisal"), ("fft", "çip içi DDC", "son")]
    zincir(y2, sira2, "B · Direct RF sampling (örnek fs; cihaza göre değişir)", "s-vurgu")
    out.append(f'<use href="#sym-saat" x="660" y="{y2 + 40}" width="60" height="30"/>')
    out.append(f'<path d="M690 {y2 + 40} V{y2 + 22}" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(f'<text x="726" y="{y2 + 60}" class="s-kucuk">saat ≈ {fs2 / 1e9:.0f} GHz, σ ≈ {JIT * 1e15:.0f} fs → jitter SNR {snr_jitter(RF, JIT):.1f} dB (f_in = {RF / 1e9:.1f} GHz!)</text>')
    out.append(f'<text x="20" y="{y2 + 92}" class="s-kucuk">RF {RF / 1e9:.1f} GHz doğrudan → {b2}. bölge → alias {al2 / 1e6:.0f} MHz{", evrik" if ev2 else ""} · ADC analog giriş BW ≥ {RF / 1e9:.1f} GHz şart · bant seçici filtre komşu bölgeleri (ör. {(fs2 - RF % fs2) / 1e9:.1f} GHz, {(RF % fs2) / 1e9:.1f} GHz) bastırmalı</text>')
    out.append(f'<text x="20" y="{H - 8}" class="s-kucuk">Silinenler: mixer, LO sentezleyici, IF filtre, IF yükselteç. Kalanlar: limiter, LNA, bant seçici/AAF. Artanlar: saat kalitesi, ADC giriş BW, güç, veri hızı (çip içi DDC ile geri alınır).</text>')
    out.append("</svg>")
    yaz("g-103-superhet-vs-direct.svg", out)


# ------------------------------------------------------------------ g-110
def g_110():
    """JESD204 katmanları + SYSREF / LMFC zamanlaması, kompakt."""
    W, H = 960, 400
    out = bas("g110", W, H,
              "JESD204 özet: solda ADC (TX) ve FPGA (RX) tarafında aynalı dört katman — transport, scrambler, data link, PHY — "
              "ve aralarındaki L lane; parametre seti (L, M, F, S, N, N′, K) iki uçta aynı olmalı. Sağda subclass 1 zamanlaması: "
              "device clock, SYSREF kenarı her iki cihazın LMFC/LEMC sayacını hizalar, SYNC~ bırakılır, ILAS ve veri LMFC "
              "sınırında başlar, RX elastik tampon veriyi LMFC + RBD anında bırakır → deterministik gecikme.")
    out.append('<text x="20" y="22" class="s-baslik">JESD204B/C tek bakışta — katmanlar (sol) ve SYSREF ile deterministik gecikme (sağ)</text>')
    kat = [("Transport", "M örnek → oktet → frame (F, S, N′)"), ("Scrambler", "1+x¹⁴+x¹⁵ (B) · x⁵⁸+x³⁹+1 (C)"),
           ("Data link", "B: CGS/ILAS, 8b/10b · C: sync header, 64b/66b"), ("PHY (SerDes)", "CDR, eşitleme, L lane")]
    for i, (ad, alt) in enumerate(kat):
        y = 60 + i * 56
        out.append(blok(20, y, 150, 44, ad, "blok-aktif" if i < 3 else "blok", alt, r=5))
        out.append(blok(330, y, 150, 44, ad, "blok-aktif" if i < 3 else "blok", alt, r=5))
    out.append('<text x="95" y="52" text-anchor="middle" class="s-metin2">ADC = TX</text>')
    out.append('<text x="405" y="52" text-anchor="middle" class="s-metin2">FPGA = RX</text>')
    for i in range(4):
        y = 250 + i * 8
        out.append(f'<path d="M170 {y} H330" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    out.append('<text x="250" y="244" text-anchor="middle" class="s-kucuk s-vurgu">L lane · lane hızı = fs·N′·M·(10/8 | 66/64)/L</text>')
    out.append('<path d="M250 60 V240" class="yol-saat"/>')
    out.append('<text x="250" y="130" text-anchor="middle" class="s-kucuk" transform="rotate(-90 250 130)">parametreler iki uçta aynı</text>')
    out.append(f'<text x="20" y="{300}" class="s-kucuk">Senaryo, 204B örneği: M = 1, N = {BIT}, N′ = 16, fs = {int(FS / 1e6)} MSPS → {FS * 16 / 1e9:.1f} Gb/s ham; L = 8 → lane {FS * 16 * 10 / 8 / 8 / 1e9:.1f} Gb/s</text>')
    out.append(f'<text x="20" y="{318}" class="s-kucuk">204C, 64b/66b: L = 4 → lane {FS * 16 * 66 / 64 / 4 / 1e9:.2f} Gb/s (≈ %3 ek yük, 204B\'de %25)</text>')
    out.append('<text x="20" y="344" class="s-kucuk s-altin">Yazılımcı: link-up = SYNC~ / CGS / ILAS / veri; hata sayaçları ve "link kalktı ama veri çöp" → parametre uyuşmazlığı</text>')
    # sağ: zamanlama
    tx0, tx1 = 540, 940
    out.append(f'<text x="{tx0}" y="52" class="s-metin2">Subclass 1 zamanlaması (şematik)</text>')
    satirlar = ["device clock", "SYSREF", "LMFC (TX)", "LMFC (RX)", "SYNC~", "lane verisi", "RX çıkışı"]
    for i, ad in enumerate(satirlar):
        y = 78 + i * 38
        out.append(f'<text x="{tx0 - 6}" y="{y + 14}" text-anchor="end" class="s-kucuk">{ad}</text>')
        out.append(f'<path d="M{tx0} {y + 26} H{tx1}" class="izgara"/>')
    # device clock
    y = 78
    d = f"M{tx0} {y + 20}"
    for k in range(40):
        xa = tx0 + k * 10
        d += f"H{xa + 5} V{y + 4} H{xa + 10} V{y + 20}"
    out.append(f'<path d="{d}" class="yol-saat" style="stroke-dasharray:none"/>')
    # SYSREF
    y = 116
    out.append(f'<path d="M{tx0} {y + 20} H{tx0 + 60} V{y + 4} H{tx0 + 80} V{y + 20} H{tx1}" class="yol-saat" style="stroke-dasharray:none"/>')
    out.append(f'<path d="M{tx0 + 60} {y - 4} V{78 + 7 * 38}" class="yol-gurultu"/>')
    out.append(f'<text x="{tx0 + 64}" y="{y - 2}" class="s-kucuk s-kirmizi">SYSREF kenarı: sayaçlar sıfırlanır</text>')
    # LMFC TX / RX
    for j, y in enumerate((154, 192)):
        d = f"M{tx0} {y + 20}"
        for k in range(4):
            xa = tx0 + 60 + k * 90
            d += f"H{xa} V{y + 4} H{xa + 6} V{y + 20}"
        d += f"H{tx1}"
        out.append(f'<path d="{d}" class="yol-kontrol"/>')
        out.append(f'<text x="{tx0 + 100}" y="{y + 14}" class="s-kucuk s-yesil">K frame = 1 multiframe</text>')
    # SYNC~
    y = 230
    out.append(f'<path d="M{tx0} {y + 20} H{tx0 + 150} V{y + 4} H{tx1}" class="yol-kontrol"/>')
    out.append(f'<text x="{tx0 + 154}" y="{y + 2}" class="s-kucuk s-yesil">RX: CGS tamam → SYNC~ bırakılır</text>')
    # lane verisi
    y = 268
    out.append(f'<rect x="{tx0}" y="{y + 4}" width="240" height="16" class="blok"/><text x="{tx0 + 120}" y="{y + 16}" text-anchor="middle" class="s-kucuk">K28.5 (CGS)</text>')
    out.append(f'<rect x="{tx0 + 240}" y="{y + 4}" width="90" height="16" class="spk-filtre" style="fill:var(--gold-soft)"/><text x="{tx0 + 285}" y="{y + 16}" text-anchor="middle" class="s-kucuk">ILAS</text>')
    out.append(f'<rect x="{tx0 + 330}" y="{y + 4}" width="70" height="16" class="spk-sinyal"/><text x="{tx0 + 365}" y="{y + 16}" text-anchor="middle" class="s-kucuk">veri</text>')
    out.append(f'<text x="{tx0 + 240}" y="{y + 32}" class="s-kucuk">TX: bir sonraki LMFC sınırında başlar</text>')
    # RX çıkışı
    y = 306
    out.append(f'<rect x="{tx0 + 360}" y="{y + 4}" width="40" height="16" class="spk-sinyal"/>')
    out.append(f'<path d="M{tx0 + 330} {y + 10} H{tx0 + 358}" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    out.append(f'<text x="{tx0}" y="{y + 16}" class="s-kucuk">elastik tampon veriyi LMFC + RBD anında bırakır</text>')
    out.append(f'<text x="{tx0}" y="{y + 44}" class="s-kucuk">→ gecikme her açılışta ve her çipte aynı = deterministik gecikme; çok çip için SYSREF ortak</text>')
    out.append(f'<text x="{tx0}" y="{y + 62}" class="s-kucuk">RFSoC\'da bu katmanlar yok: örnekler AXI-Stream ile PL\'ye gelir; SYSREF yine çok tile hizası için gerekir</text>')
    out.append("</svg>")
    yaz("g-110-jesd204-ozet.svg", out)


# ------------------------------------------------------------------ g-111
def g_111():
    """Saat ağacı: referans → jitter cleaner → ADC saati, SYSREF, FPGA saatleri."""
    W, H = 1000, 360
    out = bas("g111", W, H,
              "Almaç kartı saat ağacı: sistem referansı (10/100 MHz OCXO ya da şasi referansı) → jitter temizleyici çift döngülü PLL "
              "(PLL1 dar bantlı VCXO'ya kilitler, PLL2 geniş bantlı VCO ile GHz'e çarpar) → bölücüler → ADC örnekleme saati "
              f"{int(FS / 1e6)} MHz, ADC SYSREF, FPGA GT referans saati, FPGA SYSREF ve isteğe bağlı fabric saati; PS saati ayrı. "
              "Saat yolları gri kesikli, çiftler (DCLK/SYSREF) aynı bölücü zincirinden. Jitter bütçesi: σ_toplam² = σ_saat² + σ_aperture².")
    out.append('<text x="20" y="22" class="s-baslik">Saat ağacı — referanstan ADC örnekleme saatine ve FPGA\'ya</text>')
    y = 120
    out.append(sym("saat", 20, y - 20, "sistem referansı"))
    out.append('<text x="50" y="{}" text-anchor="middle" class="s-kucuk">10 / 100 MHz OCXO ya da şasi</text>'.format(y + 46))
    out.append(f'<path d="M80 {y} H118" class="yol-saat" marker-end="url(#ok-saat)"/>')
    # jitter cleaner kutusu
    out.append('<rect x="120" y="50" width="330" height="200" rx="8" class="blok" opacity=".5"/>')
    out.append('<text x="130" y="68" class="s-metin2">jitter temizleyici / saat üreteci (çift döngü)</text>')
    out.append(blok(140, y - 22, 90, 44, "PLL1", "blok-aktif", "dar bant, temizler"))
    out.append(f'<path d="M230 {y} H258" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(blok(260, y - 22, 70, 44, "VCXO", "blok", "ör. 100 MHz"))
    out.append(f'<path d="M330 {y} H358" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(blok(360, y - 22, 80, 44, "PLL2 + VCO", "blok-aktif", "geniş bant, çarpar"))
    out.append(f'<path d="M400 {y + 22} V{y + 60}" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append(blok(300, y + 62, 140, 40, "bölücüler / dağıtım", "blok", "DCLK + SYSREF çiftleri"))
    out.append(f'<text x="140" y="{y + 60}" class="s-kucuk">PLL1 çıkışı: referansın uzun vadeli doğruluğu</text>')
    out.append(f'<text x="140" y="{y + 74}" class="s-kucuk">+ VCXO\'nun temiz faz gürültüsü</text>')
    out.append(f'<text x="140" y="{y + 88}" class="s-kucuk">PLL2 çıkışı: GHz sınıfı, σ ≈ on–yüz fs</text>')
    # çıkışlar
    cik = [(f"ADC saati {int(FS / 1e6)} MHz", 70, "yol-saat"), ("ADC SYSREF", 110, "yol-saat"),
           ("FPGA GT refclk (ör. 300 MHz)", 160, "yol-saat"), ("FPGA SYSREF", 200, "yol-saat"),
           ("fabric saati (ör. 300 MHz, ops.)", 240, "yol-saat")]
    for ad, yy, kls in cik:
        out.append(f'<path d="M440 {y + 82} H470 V{yy} H560" class="{kls}" marker-end="url(#ok-saat)"/>')
        out.append(f'<text x="566" y="{yy + 4}" class="s-kucuk">{ad}</text>')
    # ADC ve FPGA kutuları
    out.append('<rect x="760" y="50" width="220" height="80" rx="8" class="blok-analog"/>')
    out.append('<text x="870" y="74" text-anchor="middle" class="s-metin2 s-altin">ADC</text>')
    out.append('<text x="870" y="92" text-anchor="middle" class="s-kucuk">örnekleme saati → T/H · SYSREF → LMFC</text>')
    out.append(f'<text x="870" y="110" text-anchor="middle" class="s-kucuk">σ_toplam² = σ_saat² + σ_aperture²</text>')
    out.append(f'<path d="M740 70 H758" class="yol-saat" marker-end="url(#ok-saat)"/><path d="M740 110 H758" class="yol-saat" marker-end="url(#ok-saat)"/>')
    out.append('<rect x="760" y="150" width="220" height="110" rx="8" class="blok-aktif"/>')
    out.append('<text x="870" y="172" text-anchor="middle" class="s-metin2 s-vurgu">FPGA</text>')
    out.append('<text x="870" y="190" text-anchor="middle" class="s-kucuk">GT refclk → SerDes PLL (JESD PHY)</text>')
    out.append('<text x="870" y="206" text-anchor="middle" class="s-kucuk">SYSREF → LMFC (RX), fabric\'te yakalanır</text>')
    out.append('<text x="870" y="222" text-anchor="middle" class="s-kucuk">fabric saati: JESD çıkışından (link clock)</text>')
    out.append('<text x="870" y="238" text-anchor="middle" class="s-kucuk">ya da ayrı giriş; MMCM ile türetilir</text>')
    out.append(f'<path d="M740 160 H758" class="yol-saat" marker-end="url(#ok-saat)"/><path d="M740 200 H758" class="yol-saat" marker-end="url(#ok-saat)"/><path d="M740 240 H758" class="yol-saat" marker-end="url(#ok-saat)"/>')
    # PS saati
    out.append('<rect x="760" y="280" width="220" height="50" rx="8" class="blok-kontrol"/>')
    out.append('<text x="870" y="300" text-anchor="middle" class="s-metin2 s-yesil">PS (işlemci) saati</text>')
    out.append('<text x="870" y="318" text-anchor="middle" class="s-kucuk">ayrı kristal; örnekleme saatiyle ilişkisiz</text>')
    out.append(f'<text x="20" y="{H - 30}" class="s-kucuk">Kural 1: DCLK ve SYSREF aynı çipin aynı bölücü zincirinden çıkar; faz ilişkisi tasarım parametresidir (RF Örnekleme, SYSREF bölümü).</text>')
    out.append(f'<text x="20" y="{H - 12}" class="s-kucuk">Kural 2: örnekleme saatini FPGA\'dan üretme — fabric MMCM\'in ps sınıfı jitter\'ı 1.8 GHz girişte SNR\'ı 40 dB\'nin altına iter (Bölüm 9, F. jitter).</text>')
    out.append("</svg>")
    yaz("g-111-saat-agaci.svg", out)


# ------------------------------------------------------------------ g-112
def g_112():
    """SSR: tek hızlı akış → N paralel faz (örnek/saat)."""
    W, H = 960, 380
    N = 8
    fclk = FS / N
    out = bas("g112", W, H,
              f"SSR (super-sample rate) gösterimi: üstte ADC'nin {int(FS / 1e6)} MSPS'lik tek örnek akışı x[0], x[1], … ; altta FPGA'da "
              f"{int(fclk / 1e6)} MHz fabric saatinin her vuruşunda {N} örneklik bir vektör: saat n'de lane k örneği x[{N}n + k] taşır. "
              f"Sözcük genişliği {N} × 16 bit = {N * 16} bit AXI-Stream; en düşük indisli lane en eski örnektir (sıra sözleşmesi belgelenmeli). "
              f"14 bitlik örnek 16 bitlik sözcüğe işaret uzatma ya da MSB hizalama ile yerleşir.")
    out.append(f'<text x="20" y="22" class="s-baslik">SSR: {int(FS / 1e6)} MSPS tek akış → {N} paralel örnek × {int(fclk / 1e6)} MHz fabric saati</text>')
    # üst: hızlı akış
    y = 70
    out.append(f'<text x="20" y="{y - 12}" class="s-kucuk s-vurgu">ADC çıkışı: örnek başına {1e9 / FS * 1e3:.0f} ps</text>')
    for k in range(24):
        x = 20 + k * 38
        kls = "blok-aktif" if (k // N) % 2 == 0 else "blok"
        out.append(f'<rect x="{x}" y="{y}" width="36" height="26" rx="3" class="{kls}"/>')
        out.append(f'<text x="{x + 18}" y="{y + 17}" text-anchor="middle" class="s-mono2">x[{k}]</text>')
    out.append(f'<text x="{20 + 24 * 38 + 4}" y="{y + 17}" class="s-kucuk">…</text>')
    # saat çizgisi hızlı
    d = f"M20 {y + 44}"
    for k in range(24):
        x = 20 + k * 38
        d += f"H{x + 19} V{y + 34} H{x + 38} V{y + 44}"
    out.append(f'<path d="{d}" class="yol-saat" style="stroke-dasharray:none"/>')
    out.append(f'<text x="20" y="{y + 60}" class="s-kucuk">örnekleme saati {int(FS / 1e6)} MHz (fabric bunu tutamaz)</text>')
    # oklar: gruplar aşağı
    for g in range(3):
        xa = 20 + g * N * 38 + N * 38 / 2
        out.append(f'<path d="M{xa:.1f} {y + 66} V{y + 96}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
        out.append(f'<text x="{xa + 6:.1f}" y="{y + 86}" class="s-kucuk">saat {g}</text>')
    # alt: vektörler
    y2 = 190
    out.append(f'<text x="20" y="{y2 - 12}" class="s-kucuk s-vurgu">FPGA: her fabric saatinde {N} örneklik sözcük (tdata[{N * 16 - 1}:0])</text>')
    for g in range(3):
        x0 = 20 + g * 300
        kls = "blok-aktif" if g % 2 == 0 else "blok"
        for k in range(N):
            yy = y2 + k * 18
            out.append(f'<rect x="{x0}" y="{yy}" width="110" height="16" rx="2" class="{kls}"/>')
            out.append(f'<text x="{x0 + 4}" y="{yy + 12}" class="s-mono2">lane {k}: x[{N * g + k}]</text>')
        out.append(f'<text x="{x0 + 120}" y="{y2 + 12}" class="s-kucuk">bit [{16 * N - 1}:{16 * (N - 1)}] ← lane {N - 1}</text>')
        out.append(f'<text x="{x0 + 120}" y="{y2 + 7 * 18 + 12}" class="s-kucuk">bit [15:0] ← lane 0 (en eski)</text>')
        out.append(f'<text x="{x0 + 55}" y="{y2 + N * 18 + 14}" text-anchor="middle" class="s-kucuk">saat {g} · t = {g / fclk * 1e9:.2f} ns</text>')
    # fabric saati
    d = f"M20 {y2 + 175}"
    for g in range(3):
        x = 20 + g * 300
        d += f"H{x + 150} V{y2 + 165} H{x + 300} V{y2 + 175}"
    out.append(f'<path d="{d}" class="yol-saat" style="stroke-dasharray:none"/>')
    out.append(f'<text x="20" y="{y2 + 192}" class="s-kucuk">fabric saati {int(fclk / 1e6)} MHz · veri hızı aynı: {N} × 16 bit × {int(fclk / 1e6)} MHz = {N * 16 * fclk / 1e9:.1f} Gb/s</text>')
    out.append(f'<text x="20" y="{H - 30}" class="s-kucuk">Örnek sözcüğü (16 bit): 14 bit 2\'nin tümleyeni → işaret uzatma [s s d13 … d0] ya da MSB hizalı [d13 … d0 0 0]; hangisi olduğunu belge söyler, ölçek 4 kat farklıdır.</text>')
    out.append(f'<text x="20" y="{H - 12}" class="s-kucuk">DSP tarafında sonuç: her blok (NCO, FIR, CIC) saat başına {N} örnek işler — Bölüm 12 ve 14\'teki SSR gerçeklemesi bu sözleşmeyle başlar.</text>')
    out.append("</svg>")
    yaz("g-112-ssr-paralel.svg", out)


URETICILER = {
    "g-80": g_80, "g-81": g_81, "g-90": g_90, "g-91": g_91, "g-92": g_92, "g-93": g_93,
    "g-100": g_100, "g-101": g_101, "g-102": g_102, "g-103": g_103,
    "g-110": g_110, "g-111": g_111, "g-112": g_112,
}


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
