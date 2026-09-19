#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k1.py — Kısım I (Bölüm 1–4) hesaplanmış şekil üreticisi

gen_figures.py ile aynı yardımcıları kullanır (fft, path_from, eksen);
yalnızca Kısım I'in şekillerini üretir:

  g-10  aynı sinyalin zaman ve frekans görünümü        g-11  dB merdiveni
  g-20  dönen fazör ve I/Q izdüşümleri                 g-21  reel vs kompleks spektrum
  g-22  I/Q dengesizliği ve image                      g-30  darbe anatomisi
  g-31  PW–spektrum ilişkisi                           g-32  MOP türleri zaman–frekans
  g-40  kaskad seviye diyagramı (scenario.json)        g-41  bant genişliği–gürültü tabanı

  python build/gen_figures_k1.py          # hepsi
  python build/gen_figures_k1.py g-40     # yalnızca biri
"""
import cmath
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_figures import S, SVG, TAU, eksen, fft, path_from, pencere  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KTB = 10 * math.log10(1.380649e-23 * 290 * 1000)   # −173.98 dBm/Hz


# ------------------------------------------------------------------ ortak yardımcılar
def db10(x):
    return 10 * math.log10(max(x, 1e-300))


def db20(x):
    return 20 * math.log10(max(x, 1e-300))


def lin10(db):
    return 10 ** (db / 10)


def sinc(x):
    return 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)


def bas(gid, W, H, title):
    return [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-{gid}">',
            f'<title id="t-{gid}">{title}</title>']


def yaz(dosya, parcalar):
    parcalar.append("</svg>")
    (SVG / dosya).write_text("\n".join(parcalar), encoding="utf-8")
    print("  ✓", dosya)


def cizgi_yolu(xs, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax, seyrelt_=True):
    """path_from gibi ama seyreltmesiz (osilasyonlu zaman sinyalleri için)."""
    if seyrelt_:
        return path_from(xs, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    d = []
    for k, (x, y) in enumerate(zip(xs, ys)):
        px = x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)
        py = y0 - (max(ymin, min(ymax, y)) - ymin) / (ymax - ymin) * (y0 - y1)
        d.append(("M" if k == 0 else "L") + f"{px:.1f} {py:.1f}")
    return "".join(d)


def spektrum(x, tip="blackman-harris"):
    N = len(x)
    w = pencere(tip, N)
    s1 = sum(w)
    X = fft([x[k] * w[k] for k in range(N)])
    out = [20 * math.log10(max(abs(X[k]) / s1, 1e-15)) for k in range(N)]
    return out[N // 2:] + out[:N // 2]


def ok(x1, y1, x2, y2, kls="yol-sayisal", marker="ok-sayisal", sw=None):
    s = f' stroke-width="{sw}"' if sw else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{kls}"{s} marker-end="url(#{marker})"/>'


def olcu(x1, y1, x2, y2, metin, kls="s-kucuk", dx=0, dy=-4):
    """İki ucu tikli ölçü çizgisi + etiket (yatay ya da düşey)."""
    p = [f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="var(--ink-2)" stroke-width="1"/>']
    if abs(y1 - y2) < 0.5:   # yatay
        p.append(f'<line x1="{x1:.1f}" y1="{y1 - 4:.1f}" x2="{x1:.1f}" y2="{y1 + 4:.1f}" stroke="var(--ink-2)" stroke-width="1"/>')
        p.append(f'<line x1="{x2:.1f}" y1="{y1 - 4:.1f}" x2="{x2:.1f}" y2="{y1 + 4:.1f}" stroke="var(--ink-2)" stroke-width="1"/>')
        p.append(f'<text x="{(x1 + x2) / 2 + dx:.1f}" y="{y1 + dy:.1f}" text-anchor="middle" class="{kls}">{metin}</text>')
    else:
        p.append(f'<line x1="{x1 - 4:.1f}" y1="{y1:.1f}" x2="{x1 + 4:.1f}" y2="{y1:.1f}" stroke="var(--ink-2)" stroke-width="1"/>')
        p.append(f'<line x1="{x1 - 4:.1f}" y1="{y2:.1f}" x2="{x1 + 4:.1f}" y2="{y2:.1f}" stroke="var(--ink-2)" stroke-width="1"/>')
        p.append(f'<text x="{x1 + 6 + dx:.1f}" y="{(y1 + y2) / 2 + 4 + dy:.1f}" class="{kls}">{metin}</text>')
    return "".join(p)


# ================================================================== g-10
def g_10():
    """Aynı sinyalin zaman ve frekans görünümü: tek ton (A, T, φ işaretli) ve iki ton toplamı."""
    W, H = 860, 430
    out = bas("g10", W, H, "Aynı sinyalin iki görünümü. Üst sıra: A·cos(2πft+φ) tek tonu zaman ekseninde (genlik A, periyot T = 1/f ve faz kayması φ işaretli) ve frekans ekseninde tek bir çizgi. Alt sıra: 1 MHz ve 3 MHz'lik iki tonun toplamı zamanda karmaşık görünür, frekansta iki temiz çizgiye ayrılır.")
    # --- üst sol: tek ton
    f1, A, fi = 1e6, 1.0, math.radians(60)
    x0, x1, y0, y1 = 60, 470, 190, 40
    tmin, tmax = 0, 2.5e-6
    n = 500
    ts = [tmin + (tmax - tmin) * k / (n - 1) for k in range(n)]
    ref = [A * math.cos(TAU * f1 * t) for t in ts]
    sig = [A * math.cos(TAU * f1 * t + fi) for t in ts]
    out.append('<text x="60" y="26" class="s-baslik">Zaman domaini</text>')
    out.append(eksen(x0, x1, y0, y1, [0, 0.5e-6, 1e-6, 1.5e-6, 2e-6, 2.5e-6], [-1, 0, 1], tmin, tmax, -1.3, 1.3,
                     lambda v: f"{v * 1e6:g}", lambda v: f"{v:g}"))
    out.append(f'<path d="{cizgi_yolu(ts, ref, x0, x1, y0, y1, tmin, tmax, -1.3, 1.3, False)}" fill="none" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')
    out.append(f'<path d="{cizgi_yolu(ts, sig, x0, x1, y0, y1, tmin, tmax, -1.3, 1.3, False)}" fill="none" stroke="var(--accent)" stroke-width="2"/>')
    px = lambda t: x0 + (t - tmin) / (tmax - tmin) * (x1 - x0)
    py = lambda v: y0 - (v + 1.3) / 2.6 * (y0 - y1)
    # genlik oku: tepe noktası t = -φ/(2πf) + T → t = 1 µs - 1/6 µs
    tp = 1e-6 - fi / (TAU * f1)
    out.append(olcu(px(tp), py(0), px(tp), py(A), "A (genlik)", "s-kucuk s-vurgu", dx=2, dy=0))
    # periyot
    out.append(olcu(px(tp), py(-1.15), px(tp + 1 / f1), py(-1.15), "T = 1/f = 1 µs", "s-kucuk", dy=12))
    # faz kayması: referans tepe t=1 µs, sinyal tepesi tp
    out.append(olcu(px(tp), py(1.18), px(1e-6), py(1.18), "φ", "s-kucuk s-altin", dy=-3))
    out.append(f'<text x="{px(1.3e-6):.1f}" y="{py(-1.02):.1f}" class="s-kucuk">kesikli: referans cos (φ = 0)</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">zaman (µs)</text>')
    out.append(f'<text x="{x0 - 46}" y="{(y0 + y1) / 2:.0f}" class="s-kucuk" transform="rotate(-90 {x0 - 46} {(y0 + y1) / 2:.0f})" text-anchor="middle">genlik (V)</text>')
    # --- üst sağ: tek çizgi
    fx0, fx1 = 560, 830
    out.append('<text x="560" y="26" class="s-baslik">Frekans domaini</text>')
    out.append(eksen(fx0, fx1, y0, y1, [0, 1e6, 2e6, 3e6, 4e6], [0, 0.5, 1], 0, 4.5e6, 0, 1.3, lambda v: f"{v / 1e6:g}", lambda v: f"{v:g}"))
    fpx = lambda f: fx0 + f / 4.5e6 * (fx1 - fx0)
    fpy = lambda v: y0 - v / 1.3 * (y0 - y1)
    out.append(f'<line x1="{fpx(f1):.1f}" y1="{y0}" x2="{fpx(f1):.1f}" y2="{fpy(A):.1f}" stroke="var(--accent)" stroke-width="3"/>')
    out.append(f'<circle cx="{fpx(f1):.1f}" cy="{fpy(A):.1f}" r="4" fill="var(--accent)"/>')
    out.append(f'<text x="{fpx(f1) + 8:.1f}" y="{fpy(A) + 4:.1f}" class="s-kucuk">f = 1 MHz, genlik A, faz φ</text>')
    out.append(f'<text x="{(fx0 + fx1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">frekans (MHz)</text>')
    # ok
    out.append(f'<text x="515" y="{(y0 + y1) / 2 - 8:.0f}" text-anchor="middle" class="s-metin2">Fourier</text>')
    out.append(f'<line x1="485" y1="{(y0 + y1) / 2:.0f}" x2="545" y2="{(y0 + y1) / 2:.0f}" stroke="var(--ink-2)" stroke-width="1.4" marker-end="url(#ok-ince)" marker-start="url(#ok-ince)"/>')
    # --- alt sıra: iki ton
    y0b, y1b = 400, 250
    f2, A2 = 3e6, 0.4
    sig2 = [A * math.cos(TAU * f1 * t) + A2 * math.cos(TAU * f2 * t) for t in ts]
    out.append(f'<text x="60" y="236" class="s-baslik">İki ton toplamı: 1.0·cos(2π·1 MHz·t) + 0.4·cos(2π·3 MHz·t)</text>')
    out.append(eksen(x0, x1, y0b, y1b, [0, 0.5e-6, 1e-6, 1.5e-6, 2e-6, 2.5e-6], [-1, 0, 1], tmin, tmax, -1.6, 1.6,
                     lambda v: f"{v * 1e6:g}", lambda v: f"{v:g}"))
    out.append(f'<path d="{cizgi_yolu(ts, sig2, x0, x1, y0b, y1b, tmin, tmax, -1.6, 1.6, False)}" fill="none" stroke="var(--accent)" stroke-width="2"/>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0b + 28}" text-anchor="middle" class="s-kucuk">zaman (µs) — göz iki tonu ayıramaz</text>')
    out.append(eksen(fx0, fx1, y0b, y1b, [0, 1e6, 2e6, 3e6, 4e6], [0, 0.5, 1], 0, 4.5e6, 0, 1.3, lambda v: f"{v / 1e6:g}", lambda v: f"{v:g}"))
    fpyb = lambda v: y0b - v / 1.3 * (y0b - y1b)
    for f, a in ((f1, A), (f2, A2)):
        out.append(f'<line x1="{fpx(f):.1f}" y1="{y0b}" x2="{fpx(f):.1f}" y2="{fpyb(a):.1f}" stroke="var(--accent)" stroke-width="3"/>')
        out.append(f'<circle cx="{fpx(f):.1f}" cy="{fpyb(a):.1f}" r="4" fill="var(--accent)"/>')
        out.append(f'<text x="{fpx(f) + 7:.1f}" y="{fpyb(a) + 4:.1f}" class="s-kucuk">{a:g}</text>')
    out.append(f'<text x="{(fx0 + fx1) / 2:.0f}" y="{y0b + 28}" text-anchor="middle" class="s-kucuk">frekans (MHz) — iki çizgi, iki ton</text>')
    out.append(f'<line x1="485" y1="{(y0b + y1b) / 2:.0f}" x2="545" y2="{(y0b + y1b) / 2:.0f}" stroke="var(--ink-2)" stroke-width="1.4" marker-end="url(#ok-ince)" marker-start="url(#ok-ince)"/>')
    yaz("g-10-zaman-frekans.svg", out)


# ================================================================== g-11
def g_11():
    """dB merdiveni: −180 … +40 dBm; sol kolon güç/gerilim karşılıkları, sağ kolon senaryodan tipik seviyeler."""
    W, H = 860, 560
    out = bas("g11", W, H, "dB merdiveni: −180 dBm'den +40 dBm'e düşey eksen. Solda her 10 dB'de mutlak güç (W) ve 50 Ω'daki rms gerilim; sağda kTB (−174 dBm/Hz), 2 MHz ve 300 MHz bantta gürültü tabanı, referans senaryonun MDS'i (−68.2 dBm), gelen darbe (−60 dBm), LNA çıkışı, ADC tam ölçeği (+4 dBm), 1 mW (0 dBm) ve 1 W (+30 dBm) işaretli. Sağ altta 3/6/10/20 dB ezber kartı.")
    x_eks = 330
    ymin, ymax = -180, 40
    y0, y1 = 520, 40
    py = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    out.append(f'<rect x="{x_eks - 10}" y="{y1}" width="20" height="{y0 - y1}" fill="var(--dia-blok)" stroke="var(--line-2)"/>')
    # gürültü bölgesi (gri) ve doyum bölgesi (kırmızımsı) referans senaryo için
    taban = KTB + db10(300e6) + S["on_uc"]["nf_toplam_db"]
    out.append(f'<rect x="{x_eks - 10}" y="{py(taban):.1f}" width="20" height="{y0 - py(taban):.1f}" class="spk-gurultu"/>')
    fs_dbm = S["adc"]["tam_olcek_dbm"]
    out.append(f'<rect x="{x_eks - 10}" y="{y1}" width="20" height="{py(fs_dbm) - y1:.1f}" fill="var(--red)" opacity=".35"/>')
    out.append(f'<text x="{x_eks}" y="{y1 - 12}" text-anchor="middle" class="s-kucuk s-kirmizi">doyum (ADC tam ölçek üstü)</text>')
    out.append(f'<text x="{x_eks}" y="{y0 + 16}" text-anchor="middle" class="s-kucuk">gürültünün altı (300 MHz bant, NF 6 dB)</text>')
    # tikler ve sol kolonlar
    for v in range(-180, 41, 10):
        yy = py(v)
        buyuk = v % 20 == 0
        out.append(f'<line x1="{x_eks - (14 if buyuk else 10)}" y1="{yy:.1f}" x2="{x_eks + 10}" y2="{yy:.1f}" stroke="var(--ink-3)" stroke-width="1"/>')
        if buyuk:
            w = 10 ** ((v - 30) / 10)
            vrms = math.sqrt(w * 50)
            def si(x, birim):
                for e, p in ((1, ""), (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p"), (1e-15, "f"), (1e-18, "a"), (1e-21, "z")):
                    if x >= e * 0.999:
                        return f"{x / e:.3g} {p}{birim}"
                return f"{x:.2g} {birim}"
            out.append(f'<text x="{x_eks - 22}" y="{yy + 4:.1f}" text-anchor="end" class="s-mono">{v:+d} dBm</text>')
            out.append(f'<text x="{x_eks - 110}" y="{yy + 4:.1f}" text-anchor="end" class="s-mono2">{si(w, "W")}</text>')
            out.append(f'<text x="{x_eks - 200}" y="{yy + 4:.1f}" text-anchor="end" class="s-mono2">{si(vrms, "V")}</text>')
    out.append(f'<text x="{x_eks - 22}" y="{y1 - 30}" text-anchor="end" class="s-kucuk">dBm</text>')
    out.append(f'<text x="{x_eks - 110}" y="{y1 - 30}" text-anchor="end" class="s-kucuk">güç</text>')
    out.append(f'<text x="{x_eks - 200}" y="{y1 - 30}" text-anchor="end" class="s-kucuk">Vrms (50 Ω)</text>')
    # sağ işaretler
    isaretler = [
        (30, "1 W = +30 dBm (küçük bir verici)", "s-metin2", ""),
        (fs_dbm, f"ADC tam ölçek {fs_dbm:+g} dBm ≈ 1 Vpp (50 Ω)", "s-metin2 s-altin", ""),
        (0, "1 mW = 0 dBm (referans)", "s-metin2", ""),
        (-20, "IF yükselteç çıkışı, referans darbe (−60 + 40 dB kazanç)", "s-metin2", ""),
        (-40.5, "LNA çıkışı (−60 − 0.5 + 20 dB)", "s-metin2", ""),
        (S["sinyal"]["seviye_dbm_giris"], "gelen darbe, anten girişi −60 dBm", "s-metin2 s-vurgu", ""),
        (round(taban + 15, 1), f"MDS = taban + 15 dB SNR = {taban + 15:.1f} dBm", "s-metin2 s-yesil", ""),
        (round(taban, 1), f"gürültü tabanı 300 MHz, NF 6 dB = {taban:.1f} dBm", "s-metin2 s-kirmizi", ""),
        (round(KTB + db10(2e6), 1), f"kTB · 2 MHz = {KTB + db10(2e6):.0f} dBm (1 µs darbeye eşlenik bant)", "s-metin2", ""),
        (-174, "kTB = −174 dBm/Hz (290 K, 1 Hz)", "s-metin2 s-kirmizi", ""),
    ]
    son_y = -1e9
    for v, metin, kls, _ in isaretler:
        yy = py(v)
        ty = max(yy, son_y + 15)
        son_y = ty
        out.append(f'<line x1="{x_eks + 10}" y1="{yy:.1f}" x2="{x_eks + 40}" y2="{ty:.1f}" stroke="var(--ink-3)" stroke-width="1"/>')
        out.append(f'<circle cx="{x_eks + 10}" cy="{yy:.1f}" r="3" fill="var(--ink-2)"/>')
        out.append(f'<text x="{x_eks + 46}" y="{ty + 4:.1f}" class="{kls}">{metin}</text>')
    # ezber kartı
    kx, ky = 560, 380
    out.append(f'<rect x="{kx}" y="{ky}" width="280" height="150" rx="6" fill="var(--dia-panel)" stroke="var(--line-2)"/>')
    out.append(f'<text x="{kx + 12}" y="{ky + 20}" class="s-baslik">Ezber kartı</text>')
    satirlar = [("güç ×2", "+3 dB", "genlik ×2", "+6 dB"), ("güç ×4", "+6 dB", "genlik ×√2", "+3 dB"),
                ("güç ×10", "+10 dB", "genlik ×10", "+20 dB"), ("güç ×100", "+20 dB", "genlik ×100", "+40 dB"),
                ("güç ÷2", "−3 dB", "güç ×1000", "+30 dB")]
    for i, (a, b, c, d) in enumerate(satirlar):
        yy = ky + 42 + i * 21
        out.append(f'<text x="{kx + 12}" y="{yy}" class="s-mono2">{a}</text><text x="{kx + 90}" y="{yy}" class="s-mono s-vurgu">{b}</text>')
        out.append(f'<text x="{kx + 150}" y="{yy}" class="s-mono2">{c}</text><text x="{kx + 236}" y="{yy}" class="s-mono s-vurgu">{d}</text>')
    yaz("g-11-db-merdiveni.svg", out)


# ================================================================== g-20
def g_20():
    """Dönen fazör: birim çember üzerinde e^{jθ}, I = cos θ ve Q = sin θ izdüşümleri; sağda I(t), Q(t); altta ters dönen çift."""
    W, H = 860, 440
    out = bas("g20", W, H, "Dönen fazör ve I/Q izdüşümleri. Solda birim çember üzerinde saat yönünün tersine dönen e^{jθ} vektörü; yatay izdüşümü I = cos θ, düşey izdüşümü Q = sin θ; ilk sekiz örnek noktalanmış. Sağda aynı örneklerin zamanda I(t) ve Q(t) olarak açılmış hali: Q, I'yı 90° geriden izler. Altta reel kosinüsün iki ters dönen fazörün toplamı olduğu (pozitif ve negatif frekans) gösterilir.")
    cx, cy, R = 170, 150, 100
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="var(--dia-blok)" stroke="var(--line-2)" stroke-width="1.5"/>')
    out.append(f'<line x1="{cx - R - 20}" y1="{cy}" x2="{cx + R + 24}" y2="{cy}" stroke="var(--ink-3)" stroke-width="1" marker-end="url(#ok-ince)"/>')
    out.append(f'<line x1="{cx}" y1="{cy + R + 20}" x2="{cx}" y2="{cy - R - 24}" stroke="var(--ink-3)" stroke-width="1" marker-end="url(#ok-ince)"/>')
    out.append(f'<text x="{cx + R + 8}" y="{cy + 16}" class="s-metin">I (reel)</text>')
    out.append(f'<text x="{cx + 8}" y="{cy - R - 12}" class="s-metin">Q (sanal)</text>')
    n_ornek, adim = 8, TAU / 12   # 30° adım
    for k in range(n_ornek):
        th = k * adim
        px_, py_ = cx + R * math.cos(th), cy - R * math.sin(th)
        out.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="3.5" fill="var(--accent)" opacity="{0.35 + 0.65 * (k + 1) / n_ornek:.2f}"/>')
        out.append(f'<text x="{cx + (R + 12) * math.cos(th):.1f}" y="{cy - (R + 12) * math.sin(th) + 4:.1f}" text-anchor="middle" class="s-mono2">{k}</text>')
    th = 4 * adim  # 120°
    vx, vy = cx + R * math.cos(th), cy - R * math.sin(th)
    out.append(f'<line x1="{cx}" y1="{cy}" x2="{vx:.1f}" y2="{vy:.1f}" stroke="var(--accent)" stroke-width="2.5" marker-end="url(#ok-sayisal)"/>')
    out.append(f'<line x1="{vx:.1f}" y1="{vy:.1f}" x2="{vx:.1f}" y2="{cy}" stroke="var(--green)" stroke-width="1.2" stroke-dasharray="3 3"/>')
    out.append(f'<line x1="{vx:.1f}" y1="{vy:.1f}" x2="{cx}" y2="{vy:.1f}" stroke="var(--purple)" stroke-width="1.2" stroke-dasharray="3 3"/>')
    out.append(f'<text x="{vx - 4:.1f}" y="{cy + 14}" text-anchor="end" class="s-kucuk s-yesil">I = cos θ</text>')
    out.append(f'<text x="{cx + 6}" y="{vy - 4:.1f}" class="s-kucuk s-mor">Q = sin θ</text>')
    # açı yayı
    out.append(f'<path d="M{cx + 28} {cy} A28 28 0 0 0 {cx + 28 * math.cos(th):.1f} {cy - 28 * math.sin(th):.1f}" fill="none" stroke="var(--gold)" stroke-width="1.6"/>')
    out.append(f'<text x="{cx + 30}" y="{cy - 22}" class="s-kucuk s-altin">θ = 2πft + φ</text>')
    # dönüş oku
    out.append(f'<path d="M{cx + (R + 22) * math.cos(math.radians(300)):.1f} {cy - (R + 22) * math.sin(math.radians(300)):.1f} A{R + 22} {R + 22} 0 0 0 {cx + (R + 22) * math.cos(math.radians(340)):.1f} {cy - (R + 22) * math.sin(math.radians(340)):.1f}" fill="none" stroke="var(--gold)" stroke-width="2" marker-end="url(#ok-analog)"/>')
    out.append(f'<text x="{cx + R + 10}" y="{cy + R - 10}" class="s-kucuk s-altin">+f: saat yönünün tersi</text>')
    out.append(f'<text x="{cx}" y="{cy + R + 44}" text-anchor="middle" class="s-metin2">e^(jθ) = cos θ + j·sin θ, |e^(jθ)| = 1</text>')
    # sağ: I(t), Q(t)
    x0, x1, y0, y1 = 400, 830, 250, 50
    tmin, tmax = 0, 14
    n = 400
    ts = [tmin + (tmax - tmin) * k / (n - 1) for k in range(n)]
    I = [math.cos(t * adim) for t in ts]
    Q = [math.sin(t * adim) for t in ts]
    out.append(eksen(x0, x1, y0, y1, [0, 3, 6, 9, 12], [-1, 0, 1], tmin, tmax, -1.3, 1.3, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    out.append(f'<path d="{cizgi_yolu(ts, I, x0, x1, y0, y1, tmin, tmax, -1.3, 1.3, False)}" fill="none" stroke="var(--green)" stroke-width="2"/>')
    out.append(f'<path d="{cizgi_yolu(ts, Q, x0, x1, y0, y1, tmin, tmax, -1.3, 1.3, False)}" fill="none" stroke="var(--purple)" stroke-width="2"/>')
    ppx = lambda t: x0 + (t - tmin) / (tmax - tmin) * (x1 - x0)
    ppy = lambda v: y0 - (v + 1.3) / 2.6 * (y0 - y1)
    for k in range(n_ornek):
        out.append(f'<circle cx="{ppx(k):.1f}" cy="{ppy(math.cos(k * adim)):.1f}" r="3" fill="var(--green)"/>')
        out.append(f'<circle cx="{ppx(k):.1f}" cy="{ppy(math.sin(k * adim)):.1f}" r="3" fill="var(--purple)"/>')
    out.append(f'<text x="{x0}" y="{y1 - 10}" class="s-baslik">Aynı örnekler zamanda</text>')
    out.append(f'<text x="{x1 - 4}" y="{ppy(1) - 8:.1f}" text-anchor="end" class="s-kucuk s-yesil">I(t) = cos</text>')
    out.append(f'<text x="{x1 - 4}" y="{ppy(-1) + 14:.1f}" text-anchor="end" class="s-kucuk s-mor">Q(t) = sin — 90° geride</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">örnek no (her örnek 30° = T/12)</text>')
    out.append(olcu(ppx(0), ppy(1.22), ppx(3), ppy(1.22), "T/4", "s-kucuk", dy=-3))
    # alt: negatif frekans
    bx, by = 400, 300
    out.append(f'<text x="{bx}" y="{by}" class="s-baslik">Reel kosinüs = iki ters dönen fazörün toplamı</text>')
    for i, (isaret, etiket) in enumerate(((1, "e^(+jθ)  (+f)"), (-1, "e^(−jθ)  (−f)"))):
        ccx, ccy, r = bx + 40 + i * 130, by + 50, 32
        out.append(f'<circle cx="{ccx}" cy="{ccy}" r="{r}" fill="none" stroke="var(--line-2)"/>')
        th2 = math.radians(50) * isaret
        out.append(f'<line x1="{ccx}" y1="{ccy}" x2="{ccx + r * math.cos(th2):.1f}" y2="{ccy - r * math.sin(th2):.1f}" stroke="var(--accent)" stroke-width="2" marker-end="url(#ok-sayisal)"/>')
        sweep = 0 if isaret > 0 else 1
        out.append(f'<path d="M{ccx + (r + 8) * math.cos(math.radians(-20 * isaret)):.1f} {ccy - (r + 8) * math.sin(math.radians(-20 * isaret)):.1f} A{r + 8} {r + 8} 0 0 {sweep} {ccx + (r + 8) * math.cos(math.radians(20 * isaret)):.1f} {ccy - (r + 8) * math.sin(math.radians(20 * isaret)):.1f}" fill="none" stroke="var(--gold)" stroke-width="1.6" marker-end="url(#ok-analog)"/>')
        out.append(f'<text x="{ccx}" y="{ccy + r + 22}" text-anchor="middle" class="s-mono2">{etiket}</text>')
    out.append(f'<text x="{bx + 105}" y="{by + 54}" text-anchor="middle" class="s-metin">+</text>')
    out.append(f'<text x="{bx + 236}" y="{by + 54}" text-anchor="middle" class="s-metin">=</text>')
    ccx, ccy, r = bx + 300, by + 50, 32
    out.append(f'<circle cx="{ccx}" cy="{ccy}" r="{r}" fill="none" stroke="var(--line-2)"/>')
    out.append(f'<line x1="{ccx}" y1="{ccy}" x2="{ccx + 2 * r * math.cos(math.radians(50)):.1f}" y2="{ccy}" stroke="var(--green)" stroke-width="2.5" marker-end="url(#ok-kontrol)"/>')
    out.append(f'<line x1="{ccx}" y1="{ccy}" x2="{ccx + r * math.cos(math.radians(50)):.1f}" y2="{ccy - r * math.sin(math.radians(50)):.1f}" stroke="var(--accent)" stroke-width="1" stroke-dasharray="3 2"/>')
    out.append(f'<line x1="{ccx}" y1="{ccy}" x2="{ccx + r * math.cos(math.radians(50)):.1f}" y2="{ccy + r * math.sin(math.radians(50)):.1f}" stroke="var(--accent)" stroke-width="1" stroke-dasharray="3 2"/>')
    out.append(f'<text x="{ccx}" y="{ccy + r + 22}" text-anchor="middle" class="s-mono2">2·cos θ — hep reel eksende</text>')
    out.append(f'<text x="{bx}" y="{by + 124}" class="s-kucuk">Q bileşenleri birbirini götürür; reel sinyalin spektrumunda +f ve −f birlikte görünür.</text>')
    yaz("g-20-fazor-iq.svg", out)


# ================================================================== g-21
def g_21():
    """Reel vs kompleks spektrum: darbeli ton için zaman ve frekans yan yana (hesaplanmış)."""
    W, H = 860, 400
    out = bas("g21", W, H, "Reel ve kompleks sinyalin spektrumu (hesaplanmış). Üst sıra: reel darbeli ton cos(2π·20 MHz·t), zaman ekseninde tek iz; spektrumu +20 ve −20 MHz'de simetrik iki kopya (her biri yarım genlikte). Alt sıra: kompleks darbeli ton e^{j2π·20 MHz·t}, zaman ekseninde I ve Q izleri; spektrumu yalnızca +20 MHz'de tek kopya. Örnekleme 300 MSPS, darbe 0.4 µs.")
    fs, f0, pw = 300e6, 20e6, 0.4e-6
    N = 2048
    ts = [k / fs for k in range(N)]
    t0 = 0.6e-6
    zarf = [1.0 if t0 <= t < t0 + pw else 0.0 for t in ts]
    xr = [zarf[k] * math.cos(TAU * f0 * ts[k]) for k in range(N)]
    xc = [zarf[k] * cmath.exp(1j * TAU * f0 * ts[k]) for k in range(N)]
    sp_r = spektrum([complex(v, 0) for v in xr], "hann")
    sp_c = spektrum(xc, "hann")
    fx = [(k - N / 2) * fs / N / 1e6 for k in range(N)]
    # normalize: kompleks tepe 0 dB
    tepe = max(sp_c)
    sp_r = [v - tepe for v in sp_r]
    sp_c = [v - tepe for v in sp_c]
    tmin, tmax = 0.4e-6, 1.2e-6
    for row, (baslik, sp, sinyaller) in enumerate((("Reel sinyal: x(t) = zarf(t)·cos(2πf₀t)", sp_r, [(xr, "var(--accent)")]),
                                                    ("Kompleks sinyal: x(t) = zarf(t)·e^(j2πf₀t) = I + jQ", sp_c, [([v.real for v in xc], "var(--green)"), ([v.imag for v in xc], "var(--purple)")]))):
        y1 = 40 + row * 185
        y0 = y1 + 130
        x0, x1 = 60, 400
        out.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">{baslik}</text>')
        out.append(eksen(x0, x1, y0, y1, [0.4e-6, 0.6e-6, 0.8e-6, 1e-6, 1.2e-6], [-1, 0, 1], tmin, tmax, -1.3, 1.3, lambda v: f"{v * 1e6:.1f}", lambda v: f"{v:g}"))
        idx = [k for k in range(N) if tmin <= ts[k] <= tmax]
        for sig, renk in sinyaller:
            out.append(f'<path d="{cizgi_yolu([ts[k] for k in idx], [sig[k] for k in idx], x0, x1, y0, y1, tmin, tmax, -1.3, 1.3, False)}" fill="none" stroke="{renk}" stroke-width="1.4"/>')
        out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">zaman (µs)</text>')
        if row == 1:
            out.append(f'<text x="{x1 - 4}" y="{y1 + 12}" text-anchor="end" class="s-kucuk"><tspan class="s-yesil">I</tspan> · <tspan class="s-mor">Q</tspan></text>')
        fx0, fx1 = 470, 830
        xmin, xmax, ymin, ymax = -150, 150, -60, 5
        out.append(eksen(fx0, fx1, y0, y1, [-150, -100, -50, 0, 50, 100, 150], [0, -20, -40, -60], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        d = path_from(fx, sp, fx0, fx1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}L{fx1} {y0}L{fx0} {y0}Z" class="spk-sinyal" opacity=".2"/>')
        out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.4"/>')
        fpx = lambda f: fx0 + (f - xmin) / (xmax - xmin) * (fx1 - fx0)
        out.append(f'<line x1="{fpx(0):.1f}" y1="{y1}" x2="{fpx(0):.1f}" y2="{y0}" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')
        if row == 0:
            out.append(f'<text x="{fpx(20) + 6:.1f}" y="{y1 + 22}" class="s-kucuk s-vurgu">+f₀ (−6 dB)</text>')
            out.append(f'<text x="{fpx(-20) - 6:.1f}" y="{y1 + 22}" text-anchor="end" class="s-kucuk s-vurgu">−f₀ (−6 dB)</text>')
            out.append(f'<text x="{fpx(-150) + 6:.1f}" y="{y0 - 8}" class="s-kucuk">simetrik: negatif taraf yeni bilgi taşımaz</text>')
        else:
            out.append(f'<text x="{fpx(20) + 6:.1f}" y="{y1 + 22}" class="s-kucuk s-vurgu">yalnızca +f₀ (0 dB)</text>')
            out.append(f'<text x="{fpx(-150) + 6:.1f}" y="{y0 - 8}" class="s-kucuk">−f₀ boş: işaret ve yön bilgisi korunur</text>')
        out.append(f'<text x="{(fx0 + fx1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">frekans (MHz), dB (kompleks tepeye göre)</text>')
    yaz("g-21-reel-kompleks-spektrum.svg", out)


# ================================================================== g-22
def g_22():
    """I/Q dengesizliği: elips, spektrumda image (hesaplanmış), I/Q yer değişince aynalanma."""
    W, H = 860, 330
    fs, f0, N = 300e6, 20e6, 2048
    g_db, phi_deg = 1.0, 10.0
    g, phi = 10 ** (g_db / 20), math.radians(phi_deg)
    irr = 20 * math.log10(abs(1 + g * cmath.exp(1j * phi))) - 20 * math.log10(abs(1 - g * cmath.exp(-1j * phi)))
    out = bas("g22", W, H, f"I/Q dengesizliği ve image (hesaplanmış). Solda: ideal I/Q çemberi ile {g_db:g} dB kazanç ve {phi_deg:g}° faz hatalı elips. Ortada: +20 MHz tonunun spektrumunda −20 MHz'de beliren image bileşeni, {irr:.1f} dB aşağıda. Sağda: I ve Q yer değiştirince spektrumun tamamının aynalanması — ton −20 MHz'e taşınır.")
    # sol: elips
    cx, cy, R = 130, 150, 95
    out.append('<text x="40" y="28" class="s-baslik">I/Q düzlemi</text>')
    out.append(f'<line x1="{cx - R - 12}" y1="{cy}" x2="{cx + R + 12}" y2="{cy}" stroke="var(--ink-3)" stroke-width="1"/>')
    out.append(f'<line x1="{cx}" y1="{cy + R + 12}" x2="{cx}" y2="{cy - R - 12}" stroke="var(--ink-3)" stroke-width="1"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="var(--accent)" stroke-width="1.4" stroke-dasharray="4 3"/>')
    pts = []
    for k in range(121):
        th = TAU * k / 120
        i_, q_ = math.cos(th), g * math.sin(th + phi)
        pts.append(f"{cx + R * i_:.1f},{cy - R * q_:.1f}")
    out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="var(--red)" stroke-width="2"/>')
    out.append(f'<text x="{cx + R + 4}" y="{cy + 14}" class="s-kucuk">I</text><text x="{cx + 6}" y="{cy - R - 2}" class="s-kucuk">Q</text>')
    out.append(f'<text x="{cx}" y="{cy + R + 34}" text-anchor="middle" class="s-kucuk s-vurgu">ideal: çember (|x| sabit)</text>')
    out.append(f'<text x="{cx}" y="{cy + R + 50}" text-anchor="middle" class="s-kucuk s-kirmizi">hatalı: elips (g = {g_db:g} dB, φ = {phi_deg:g}°)</text>')
    # orta ve sağ: spektrumlar
    ts = [k / fs for k in range(N)]
    x_hata = [complex(math.cos(TAU * f0 * t), g * math.sin(TAU * f0 * t + phi)) for t in ts]
    x_swap = [complex(v.imag, v.real) for v in x_hata]
    fx = [(k - N / 2) * fs / N / 1e6 for k in range(N)]
    for col, (baslik, x, notlar) in enumerate((("Spektrum: image belirir", x_hata, [(20, "ton +20 MHz", "s-vurgu"), (-20, f"image −{irr:.1f} dBc", "s-kirmizi")]),
                                              ("I ↔ Q yer değişti: aynalanır", x_swap, [(-20, "ton −20 MHz", "s-kirmizi"), (20, "image", "s-kirmizi")]))):
        sp = spektrum(x, "blackman-harris")
        tepe = max(sp)
        sp = [v - tepe for v in sp]
        fx0 = 300 + col * 280
        fx1 = fx0 + 240
        y0, y1 = 250, 50
        xmin, xmax, ymin, ymax = -150, 150, -80, 5
        out.append(f'<text x="{fx0}" y="28" class="s-baslik">{baslik}</text>')
        out.append(eksen(fx0, fx1, y0, y1, [-150, -75, 0, 75, 150], [0, -20, -40, -60, -80], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        d = path_from(fx, sp, fx0, fx1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}L{fx1} {y0}L{fx0} {y0}Z" class="spk-sinyal" opacity=".2"/>')
        out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.3"/>')
        fpx = lambda f: fx0 + (f - xmin) / (xmax - xmin) * (fx1 - fx0)
        fpy = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
        # image bölgesi kırmızı vurgu
        im_f = -20 if col == 0 else 20
        out.append(f'<rect x="{fpx(im_f - 6):.1f}" y="{y1}" width="{fpx(im_f + 6) - fpx(im_f - 6):.1f}" height="{y0 - y1}" fill="var(--red)" opacity=".12"/>')
        for f, metin, kls in notlar:
            seviye = 0 if "ton" in metin else -irr
            sag = f > 0
            out.append(f'<text x="{fpx(f) + (6 if sag else -6):.1f}" y="{fpy(seviye) - 6:.1f}" text-anchor="{"start" if sag else "end"}" class="s-kucuk {kls}">{metin}</text>')
        out.append(f'<text x="{(fx0 + fx1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">frekans (MHz) · dBc</text>')
    yaz("g-22-iq-dengesizlik-image.svg", out)
    return irr


# ================================================================== g-30
def g_30():
    """Darbe anatomisi: zarf üzerinde PW, rise/fall, overshoot, droop; altta darbe katarı PRI/PRF/duty."""
    W, H = 860, 430
    pw_us, pri_ms = S["sinyal"]["pw_us"], S["sinyal"]["pri_ms"]
    out = bas("g30", W, H, f"Darbe anatomisi. Üstte tek darbenin zarfı: tepe genliği (PA), %10–%90 yükselme süresi (rise time), düşme süresi, tepe aşımı (overshoot), tepe eğimi (droop) ve %50 noktaları arasında ölçülen darbe genişliği PW = {pw_us} µs işaretli; zarfın içinde taşıyıcı çizgileri. Altta darbe katarı: PRI = {pri_ms} ms, PRF = 1/PRI = 1 kHz, duty = PW/PRI = %0.1; ortalama güç tepe gücün 30 dB altında.")
    # zarf modeli: kosinüs kenar + overshoot sönümlü salınım + üstel droop
    tr, tf, pw = 0.08, 0.10, 1.0   # µs
    def zarf(t):
        if t < 0:
            return 0.0
        if t < tr:
            v = 0.5 - 0.5 * math.cos(math.pi * t / tr)
        elif t < pw - tf:
            v = 1.0
        elif t < pw:
            v = 0.5 - 0.5 * math.cos(math.pi * (pw - t) / tf)
        else:
            return 0.0
        droop = 1 - 0.06 * max(0.0, (t - tr)) / (pw - tr - tf)
        osc = 0.12 * math.exp(-(t - tr) / 0.06) * math.cos(TAU * (t - tr) / 0.08) if tr <= t < pw - tf else 0.0
        return max(0.0, v * droop + osc)
    n = 700
    tmin, tmax = -0.15, 1.35
    ts = [tmin + (tmax - tmin) * k / (n - 1) for k in range(n)]
    zs = [zarf(t) for t in ts]
    x0, x1, y0, y1 = 70, 770, 240, 40
    ymin, ymax = -0.05, 1.3
    px = lambda t: x0 + (t - tmin) / (tmax - tmin) * (x1 - x0)
    py = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    out.append(eksen(x0, x1, y0, y1, [0, 0.25, 0.5, 0.75, 1.0, 1.25], [0, 0.5, 1.0], tmin, tmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    # taşıyıcı (yüksek frekanslı) zarf içinde — 40 MHz temsilî
    tas = [zs[k] * math.cos(TAU * 40 * ts[k]) for k in range(n)]
    out.append(f'<path d="{cizgi_yolu(ts, tas, x0, x1, y0, y1, tmin, tmax, ymin, ymax, False)}" fill="none" stroke="var(--accent)" stroke-width=".8" opacity=".55"/>')
    out.append(f'<path d="{cizgi_yolu(ts, zs, x0, x1, y0, y1, tmin, tmax, ymin, ymax, False)}" fill="none" stroke="var(--gold)" stroke-width="2.2"/>')
    # seviye çizgileri
    for lv, ad in ((1.0, "%100 (PA)"), (0.9, "%90"), (0.5, "%50"), (0.1, "%10")):
        out.append(f'<line x1="{x0}" y1="{py(lv):.1f}" x2="{x1}" y2="{py(lv):.1f}" stroke="var(--ink-3)" stroke-width=".8" stroke-dasharray="2 4"/>')
        out.append(f'<text x="{x1 + 4}" y="{py(lv) + 4:.1f}" class="s-kucuk">{ad}</text>')
    # rise: t10 ve t90 kosinüs kenardan
    def t_seviye(lv, yukselen=True):
        if yukselen:
            return tr / math.pi * math.acos(1 - 2 * lv)
        return pw - tf / math.pi * math.acos(1 - 2 * lv)
    t10, t90 = t_seviye(0.1), t_seviye(0.9)
    f90, f10 = t_seviye(0.9, False), t_seviye(0.1, False)
    out.append(olcu(px(t10), py(1.18), px(t90), py(1.18), "yükselme (10→90)", "s-kucuk", dx=-40, dy=-4))
    out.append(f'<line x1="{px(t10):.1f}" y1="{py(0.1):.1f}" x2="{px(t10):.1f}" y2="{py(1.18):.1f}" stroke="var(--ink-3)" stroke-width=".8"/>')
    out.append(f'<line x1="{px(t90):.1f}" y1="{py(0.9):.1f}" x2="{px(t90):.1f}" y2="{py(1.18):.1f}" stroke="var(--ink-3)" stroke-width=".8"/>')
    out.append(olcu(px(f90), py(1.18), px(f10), py(1.18), "düşme (90→10)", "s-kucuk", dx=40, dy=-4))
    out.append(f'<line x1="{px(f90):.1f}" y1="{py(0.9):.1f}" x2="{px(f90):.1f}" y2="{py(1.18):.1f}" stroke="var(--ink-3)" stroke-width=".8"/>')
    out.append(f'<line x1="{px(f10):.1f}" y1="{py(0.1):.1f}" x2="{px(f10):.1f}" y2="{py(1.18):.1f}" stroke="var(--ink-3)" stroke-width=".8"/>')
    # PW %50
    t50a, t50b = t_seviye(0.5), t_seviye(0.5, False)
    out.append(olcu(px(t50a), py(0.5), px(t50b), py(0.5), f"PW = {pw_us} µs (%50 noktaları arası)", "s-metin2", dy=16))
    # overshoot & droop
    tep = max(range(n), key=lambda k: zs[k])
    out.append(f'<line x1="{px(ts[tep]) + 6:.1f}" y1="{py(zs[tep]):.1f}" x2="{px(ts[tep]) + 40:.1f}" y2="{py(zs[tep]) - 14:.1f}" stroke="var(--red)" stroke-width="1"/>')
    out.append(f'<text x="{px(ts[tep]) + 44:.1f}" y="{py(zs[tep]) - 16:.1f}" class="s-kucuk s-kirmizi">overshoot (tepe aşımı)</text>')
    out.append(f'<text x="{px(0.55):.1f}" y="{py(0.97) - 8:.1f}" text-anchor="middle" class="s-kucuk s-kirmizi">droop (tepe eğimi)</text>')
    out.append(f'<line x1="{px(0.3):.1f}" y1="{py(zarf(0.3)):.1f}" x2="{px(0.85):.1f}" y2="{py(zarf(0.85)):.1f}" stroke="var(--red)" stroke-width="1" stroke-dasharray="3 2"/>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">zaman (µs) — zarf altın, taşıyıcı mavi</text>')
    out.append(f'<text x="{x0}" y="{y1 - 14}" class="s-baslik">Tek darbe: ölçü noktaları</text>')
    # alt: darbe katarı
    y0b, y1b = 400, 300
    out.append(f'<text x="{x0}" y="{y1b - 14}" class="s-baslik">Darbe katarı: PRI = {pri_ms} ms, PRF = 1 kHz, duty = PW/PRI = %{S["sinyal"]["duty_yuzde"]}</text>')
    out.append(eksen(x0, x1, y0b, y1b, [0, 1, 2, 3], [0, 1], -0.2, 3.2, -0.05, 1.3, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    pxb = lambda t: x0 + (t + 0.2) / 3.4 * (x1 - x0)
    pyb = lambda v: y0b - (v + 0.05) / 1.35 * (y0b - y1b)
    for k in range(4):
        t = k * pri_ms
        out.append(f'<rect x="{pxb(t) - 1.5:.1f}" y="{pyb(1):.1f}" width="3" height="{pyb(0) - pyb(1):.1f}" fill="var(--gold)"/>')
    out.append(olcu(pxb(0), pyb(1.15), pxb(1), pyb(1.15), "PRI = 1 ms (PRF = 1/PRI = 1 kHz)", "s-kucuk", dy=-4))
    out.append(f'<line x1="{x0}" y1="{pyb(0.001):.1f}" x2="{x1}" y2="{pyb(0.001):.1f}" stroke="var(--red)" stroke-width="1.2" stroke-dasharray="4 3"/>')
    out.append(f'<text x="{pxb(1.15):.1f}" y="{pyb(0.5):.1f}" class="s-kucuk">1 µs darbe bu ölçekte bir çizgi kalınlığında; PRI/PW = 1000</text>')
    out.append(f'<text x="{pxb(1.15):.1f}" y="{pyb(0.5) + 16:.1f}" class="s-kucuk s-kirmizi">ortalama güç = tepe × duty → −30 dB (kırmızı çizgi, ölçek dışı küçük)</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0b + 26}" text-anchor="middle" class="s-kucuk">zaman (ms)</text>')
    yaz("g-30-darbe-anatomisi.svg", out)


# ================================================================== g-31
def g_31():
    """PW–spektrum: 1 µs ve 0.25 µs darbe; sinc zarfı, ilk sıfır 1/PW, PRF çizgileri büyüteçte."""
    W, H = 860, 470
    out = bas("g31", W, H, "Darbe genişliği ile spektrum ilişkisi (hesaplanmış). Üst sıra: 1 µs darbe ve |sinc| spektrumu — ilk sıfır 1/PW = 1 MHz, ana lob (sıfırdan sıfıra) 2 MHz, −3 dB genişliği ≈ 0.886/PW = 886 kHz. Alt sıra: 0.25 µs darbe — ilk sıfır 4 MHz, ana lob 8 MHz; darbe kısaldıkça spektrum genişler. Sağ üstteki büyüteç, zarfın altında PRF = 1 kHz aralıklı ayrık çizgileri gösterir (PRI = 1 ms).")
    fmax = 6.0  # MHz
    for row, pw in enumerate((1.0, 0.25)):
        y1 = 40 + row * 215
        y0 = y1 + 150
        # zaman
        x0, x1 = 60, 300
        tmin, tmax = -0.6, 1.6
        out.append(eksen(x0, x1, y0, y1, [-0.5, 0, 0.5, 1, 1.5], [0, 1], tmin, tmax, -0.1, 1.25, lambda v: f"{v:g}", lambda v: f"{v:g}"))
        px = lambda t: x0 + (t - tmin) / (tmax - tmin) * (x1 - x0)
        py = lambda v: y0 - (v + 0.1) / 1.35 * (y0 - y1)
        out.append(f'<path d="M{px(tmin):.1f} {py(0):.1f}H{px(0):.1f}V{py(1):.1f}H{px(pw):.1f}V{py(0):.1f}H{px(tmax):.1f}" fill="none" stroke="var(--gold)" stroke-width="2.2"/>')
        # taşıyıcı
        n = 300
        ts = [k * pw / (n - 1) for k in range(n)]
        out.append(f'<path d="{cizgi_yolu(ts, [math.cos(TAU * 30 * t) for t in ts], x0, x1, y0, y1, tmin, tmax, -0.1, 1.25, False)}" fill="none" stroke="var(--accent)" stroke-width=".7" opacity=".5"/>')
        out.append(olcu(px(0), py(1.12), px(pw), py(1.12), f"PW = {pw:g} µs", "s-metin2", dy=-4))
        out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">zaman (µs)</text>')
        out.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">PW = {pw:g} µs</text>')
        # spektrum |sinc|
        fx0, fx1 = 350, 660
        nf = 1200
        fsx = [-fmax + 2 * fmax * k / (nf - 1) for k in range(nf)]
        sp = [20 * math.log10(max(abs(sinc(f * pw)), 1e-6)) for f in fsx]
        xmin, xmax, ymin, ymax = -fmax, fmax, -40, 3
        out.append(eksen(fx0, fx1, y0, y1, [-6, -4, -2, 0, 2, 4, 6], [0, -10, -20, -30, -40], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        d = path_from(fsx, sp, fx0, fx1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}L{fx1} {y0}L{fx0} {y0}Z" class="spk-sinyal" opacity=".18"/>')
        out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.6"/>')
        fpx = lambda f: fx0 + (f - xmin) / (xmax - xmin) * (fx1 - fx0)
        fpy = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
        nul = 1 / pw
        out.append(olcu(fpx(-nul), fpy(-2), fpx(nul), fpy(-2), f"ana lob 2/PW = {2 * nul:g} MHz", "s-metin2", dy=-6))
        out.append(f'<line x1="{fpx(nul):.1f}" y1="{y1}" x2="{fpx(nul):.1f}" y2="{y0}" stroke="var(--ink-3)" stroke-width=".8" stroke-dasharray="3 3"/>')
        out.append(f'<text x="{fpx(nul) + 4:.1f}" y="{y0 - 6}" class="s-kucuk">ilk sıfır 1/PW = {nul:g} MHz</text>')
        b3 = 0.886 / pw / 2
        out.append(f'<line x1="{fpx(-b3):.1f}" y1="{fpy(-3):.1f}" x2="{fpx(b3):.1f}" y2="{fpy(-3):.1f}" stroke="var(--green)" stroke-width="2"/>')
        out.append(f'<text x="{fpx(b3) + 4:.1f}" y="{fpy(-3) + 14:.1f}" class="s-kucuk s-yesil">−3 dB: 0.886/PW = {0.886 / pw * 1000:.0f} kHz</text>')
        if pw > 0.5:
            out.append(f'<text x="{fpx(1.5):.1f}" y="{fpy(-13.3) - 6:.1f}" class="s-kucuk">yan lob −13.3 dB</text>')
        out.append(f'<text x="{(fx0 + fx1) / 2:.0f}" y="{y0 + 28}" text-anchor="middle" class="s-kucuk">frekans − f₀ (MHz), dB (tepeye göre)</text>')
    # büyüteç: PRF çizgileri
    bx0, bx1, by0, by1 = 700, 840, 190, 62
    out.append(f'<rect x="{bx0 - 8}" y="{by1 - 22}" width="{bx1 - bx0 + 16}" height="{by0 - by1 + 50}" rx="5" fill="var(--dia-panel)" stroke="var(--line-2)"/>')
    out.append(f'<text x="{bx0}" y="{by1 - 8}" class="s-kucuk">büyüteç: ±3.5 kHz, PRI = 1 ms</text>')
    out.append(eksen(bx0, bx1, by0, by1, [-3, -2, -1, 0, 1, 2, 3], [0], -3.5, 3.5, -0.05, 1.2, lambda v: f"{v:d}", lambda v: ""))
    for k in range(-3, 4):
        lx = bx0 + (k + 3.5) / 7 * (bx1 - bx0)
        h = abs(sinc(k * 1e-3 * 1.0))
        out.append(f'<line x1="{lx:.1f}" y1="{by0}" x2="{lx:.1f}" y2="{by0 - h * (by0 - by1) * 0.85:.1f}" stroke="var(--accent)" stroke-width="2"/>')
    out.append(f'<text x="{(bx0 + bx1) / 2:.0f}" y="{by0 + 24}" text-anchor="middle" class="s-kucuk">kHz — çizgi aralığı PRF = 1 kHz</text>')
    yaz("g-31-pw-spektrum.svg", out)


# ================================================================== g-32
def g_32():
    """MOP türleri: zaman dalga şekli, anlık frekans/faz, spektrum — sabit, LFM, Barker-13, frekans atlamalı (hesaplanmış)."""
    W, H = 900, 520
    pw = 1e-6
    bw = S["sinyal"]["varyant_b"]["chirp_bw_hz"]
    out = bas("g32", W, H, "Darbe içi modülasyon (MOP) türlerinin üç görünümü (hesaplanmış). Sütunlar: modülasyonsuz sabit frekanslı darbe; 10 MHz LFM chirp; Barker-13 faz kodlu darbe; dört adımlı frekans atlamalı darbe. Satırlar: zaman dalga şekli (reel kısım), darbe boyunca anlık frekans ya da faz, ve genlik spektrumu. Sabit darbenin bant genişliği ≈ 1/PW = 1 MHz; LFM'de ≈ 10 MHz; Barker-13'te ≈ 13/PW = 13 MHz; atlamalıda adımlar arası boşluklu.")
    fs = 128e6
    N = 4096
    n_pw = int(pw * fs)   # 128 örnek
    ts = [k / fs for k in range(N)]
    barker = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]
    hop = [-15e6, 5e6, -5e6, 15e6]
    def faz(tip, t):
        if tip == "lfm":
            return math.pi * (bw / pw) * (t - pw / 2) ** 2 - math.pi * bw / pw * (pw / 2) ** 2
        if tip == "barker":
            c = min(12, int(t / pw * 13))
            return math.pi if barker[c] < 0 else 0.0
        if tip == "hop":
            c = min(3, int(t / pw * 4))
            return TAU * hop[c] * (t - c * pw / 4)
        return 0.0
    def anlik(tip, t):
        if tip == "lfm":
            return (bw / pw) * (t - pw / 2)
        if tip == "hop":
            return hop[min(3, int(t / pw * 4))]
        return 0.0
    sutunlar = (("Sabit frekans (MOP yok)", "yok", "anlık frekans"), (f"LFM chirp, B = {bw / 1e6:g} MHz", "lfm", "anlık frekans"),
                ("Barker-13 faz kodu", "barker", "faz (0 / 180°)"), ("Frekans atlamalı (4 adım)", "hop", "anlık frekans"))
    gen = 200
    for c, (baslik, tip, orta_ad) in enumerate(sutunlar):
        x0 = 50 + c * 215
        x1 = x0 + 185
        out.append(f'<text x="{x0}" y="26" class="s-baslik">{baslik}</text>')
        # sinyal
        x = [complex(0, 0)] * N
        f_gor = 24e6  # görsel taşıyıcı ofseti (zaman çizimi için)
        gor = []
        for k in range(n_pw):
            t = k / fs
            x[k + 64] = cmath.exp(1j * faz(tip, t))
        # satır 1: zaman (reel kısım; görsel taşıyıcı ile)
        y1, y0 = 40, 150
        nn = 360
        tt = [k * pw / (nn - 1) for k in range(nn)]
        gor = [math.cos(TAU * f_gor * t + faz(tip, t)) for t in tt]
        out.append(eksen(x0, x1, y0, y1, [0, 0.5e-6, 1e-6], [-1, 0, 1], -0.1e-6, 1.1e-6, -1.3, 1.3, lambda v: f"{v * 1e6:g}", lambda v: f"{v:g}"))
        out.append(f'<path d="{cizgi_yolu(tt, gor, x0, x1, y0, y1, -0.1e-6, 1.1e-6, -1.3, 1.3, False)}" fill="none" stroke="var(--accent)" stroke-width=".9"/>')
        px = lambda t: x0 + (t + 0.1e-6) / 1.2e-6 * (x1 - x0)
        py = lambda v: y0 - (v + 1.3) / 2.6 * (y0 - y1)
        out.append(f'<path d="M{px(-0.1e-6):.1f} {py(0):.1f}H{px(0):.1f}V{py(1):.1f}H{px(pw):.1f}V{py(0):.1f}H{px(1.1e-6):.1f}" fill="none" stroke="var(--gold)" stroke-width="1.4" stroke-dasharray="4 3"/>')
        if c == 0:
            out.append(f'<text x="{x0 - 38}" y="{(y0 + y1) / 2:.0f}" class="s-kucuk" transform="rotate(-90 {x0 - 38} {(y0 + y1) / 2:.0f})" text-anchor="middle">zaman</text>')
        if tip == "barker":
            for k in range(1, 13):
                if barker[k] != barker[k - 1]:
                    out.append(f'<line x1="{px(k * pw / 13):.1f}" y1="{y1}" x2="{px(k * pw / 13):.1f}" y2="{y0}" stroke="var(--red)" stroke-width=".8" stroke-dasharray="2 2"/>')
        # satır 2: anlık frekans / faz
        y1, y0 = 190, 300
        if tip == "barker":
            ymn, ymx = -30, 210
            ys = [math.degrees(faz(tip, t)) for t in tt]
            tik = [0, 180]
            fmt = lambda v: f"{v:d}°"
        else:
            ymn, ymx = -20e6, 20e6
            ys = [anlik(tip, t) for t in tt]
            tik = [-15e6, 0, 15e6]
            fmt = lambda v: f"{v / 1e6:+g}"
        out.append(eksen(x0, x1, y0, y1, [0, 0.5e-6, 1e-6], tik, -0.1e-6, 1.1e-6, ymn, ymx, lambda v: f"{v * 1e6:g}", fmt))
        # adım fonksiyonları için noktaları sıçramada kes
        d, prev = "", None
        for t, v in zip(tt, ys):
            X = x0 + (t + 0.1e-6) / 1.2e-6 * (x1 - x0)
            Y = y0 - (v - ymn) / (ymx - ymn) * (y0 - y1)
            if prev is not None and abs(v - prev) > (ymx - ymn) * 0.2:
                d += f"M{X:.1f} {Y:.1f}"
            else:
                d += ("M" if not d else "L") + f"{X:.1f} {Y:.1f}"
            prev = v
        out.append(f'<path d="{d}" fill="none" stroke="var(--green)" stroke-width="2"/>')
        out.append(f'<text x="{x0 + 4}" y="{y1 + 12}" class="s-kucuk">{orta_ad}{" (MHz)" if tip != "barker" else ""}</text>')
        if c == 0:
            out.append(f'<text x="{x0 - 38}" y="{(y0 + y1) / 2:.0f}" class="s-kucuk" transform="rotate(-90 {x0 - 38} {(y0 + y1) / 2:.0f})" text-anchor="middle">f(t) / φ(t)</text>')
        # satır 3: spektrum
        y1, y0 = 340, 470
        sp = spektrum(x, "rect")
        tepe = max(sp)
        sp = [v - tepe for v in sp]
        fx = [(k - N / 2) * fs / N / 1e6 for k in range(N)]
        xmin, xmax, ymin, ymax = -25, 25, -50, 3
        out.append(eksen(x0, x1, y0, y1, [-20, -10, 0, 10, 20], [0, -20, -40], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        dd = path_from(fx, sp, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{dd}L{x1} {y0}L{x0} {y0}Z" class="spk-sinyal" opacity=".2"/>')
        out.append(f'<path d="{dd}" fill="none" stroke="var(--accent)" stroke-width="1.2"/>')
        bwlar = {"yok": "≈ 1/PW = 1 MHz", "lfm": "≈ B = 10 MHz", "barker": "≈ 13/PW = 13 MHz", "hop": "adımlar ±15 MHz'e yayılır"}
        out.append(f'<rect x="{x0 + 1}" y="{y1 + 1}" width="{x1 - x0 - 2}" height="15" fill="var(--dia-panel)" opacity=".85"/>')
        out.append(f'<text x="{x0 + 4}" y="{y1 + 12}" class="s-kucuk s-vurgu">BW {bwlar[tip]}</text>')
        out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 26}" text-anchor="middle" class="s-kucuk">f − f₀ (MHz) · dB</text>')
        if c == 0:
            out.append(f'<text x="{x0 - 38}" y="{(y0 + y1) / 2:.0f}" class="s-kucuk" transform="rotate(-90 {x0 - 38} {(y0 + y1) / 2:.0f})" text-anchor="middle">spektrum</text>')
    yaz("g-32-mop-turleri.svg", out)


# ================================================================== g-40
def g_40():
    """Kaskad seviye diyagramı: scenario.json on_uc.kaskad — sinyal ve gürültü seviyesi bloktan bloğa (300 MHz bant)."""
    kask = S["on_uc"]["kaskad"]
    bw = S["ddc"]["cikis_bant_mhz"] * 2 * 1e6   # 300 MHz
    giris = S["sinyal"]["seviye_dbm_giris"]
    # Friis
    F, G, adim = 0.0, 1.0, []
    for i, b in enumerate(kask):
        f, g = lin10(b["nf_db"]), lin10(b["kazanc_db"])
        F = f if i == 0 else F + (f - 1) / G
        G *= g
        adim.append((db10(F), db10(G)))
    nf_top = db10(F)
    n0 = KTB + db10(bw)
    sinyal = [giris]
    gurultu = [n0]
    for i, b in enumerate(kask):
        sinyal.append(sinyal[-1] + b["kazanc_db"])
        gurultu.append(n0 + adim[i][0] + adim[i][1])
    W, H = 1000, 470
    out = bas("g40", W, H, f"Referans ön uç kaskadının seviye diyagramı (hesaplanmış, B = 300 MHz). Üstte blok sembolleri: limiter, LNA, preselector, mixer, IF filtre, IF yükselteç, AAF + sürücü. Altta bloktan bloğa sinyal seviyesi (mavi, −60 dBm girişten −20 dBm çıkışa) ve gürültü seviyesi (gri dolgu). Girişte SNR {giris - n0:.1f} dB, çıkışta {sinyal[-1] - gurultu[-1]:.1f} dB; fark {nf_top:.2f} dB = Friis ile kaskad NF'i. Her bloğun altında kümülatif NF: LNA'dan sonra neredeyse değişmez. ADC tam ölçeği +4 dBm altın kesikli.")
    semboller = ["limiter", "amp", "bpf", "mixer", "bpf", "amp", "lpf"]
    x0, x1, y0, y1 = 80, 940, 380, 120
    n_nokta = len(kask) + 1
    xs = [x0 + 40 + k * (x1 - x0 - 80) / (n_nokta - 1) for k in range(n_nokta)]
    ymin, ymax = -100, 10
    py = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    # semboller
    out.append(f'<use href="#sym-anten" x="{xs[0] - 30:.1f}" y="14" width="60" height="40"/>')
    for i, sy in enumerate(semboller):
        X = (xs[i] + xs[i + 1]) / 2
        out.append(f'<use href="#sym-{sy}" x="{X - 30:.1f}" y="14" width="60" height="40"/>')
        out.append(f'<text x="{X:.1f}" y="68" text-anchor="middle" class="s-kucuk">{kask[i]["ad"]}</text>')
        out.append(f'<text x="{X:.1f}" y="82" text-anchor="middle" class="s-mono2">G {kask[i]["kazanc_db"]:+g} · NF {kask[i]["nf_db"]:g}</text>')
        if i < len(semboller) - 1:
            out.append(f'<line x1="{X + 30:.1f}" y1="34" x2="{(xs[i + 1] + xs[i + 2]) / 2 - 30:.1f}" y2="34" class="yol-analog"/>')
    out.append(f'<line x1="{xs[0]:.1f}" y1="34" x2="{(xs[0] + xs[1]) / 2 - 30:.1f}" y2="34" class="yol-analog"/>')
    out.append(f'<text x="{x1}" y="34" text-anchor="start" class="s-kucuk">→ ADC</text>')
    out.append(f'<line x1="{xs[-1]:.1f}" y1="34" x2="{x1 - 4:.1f}" y2="34" class="yol-analog" marker-end="url(#ok-analog)"/>')
    # LO
    out.append(f'<use href="#sym-lo" x="{(xs[3] + xs[4]) / 2 - 30:.1f}" y="88" width="60" height="40"/>')
    out.append(f'<text x="{(xs[3] + xs[4]) / 2 + 34:.1f}" y="112" class="s-kucuk">LO {S["on_uc"]["lo_ghz"]} GHz</text>')
    # eksen
    out.append(eksen(x0, x1, y0, y1, [], [0, -20, -40, -60, -80, -100], 0, 1, ymin, ymax, str, lambda v: f"{v:d}"))
    out.append(f'<text x="{x0 - 52}" y="{(y0 + y1) / 2:.0f}" class="s-kucuk" transform="rotate(-90 {x0 - 52} {(y0 + y1) / 2:.0f})" text-anchor="middle">seviye (dBm)</text>')
    # gürültü dolgusu (basamaklı)
    d = f"M{xs[0]:.1f} {y0}"
    for k in range(n_nokta):
        d += f"L{xs[k]:.1f} {py(gurultu[k]):.1f}"
        if k + 1 < n_nokta:
            d += f"L{xs[k + 1]:.1f} {py(gurultu[k]):.1f}"
    d += f"L{xs[-1]:.1f} {y0}Z"
    out.append(f'<path d="{d}" class="spk-gurultu" opacity=".7"/>')
    dg = ""
    for k in range(n_nokta):
        dg += ("M" if k == 0 else "L") + f"{xs[k]:.1f} {py(gurultu[k]):.1f}"
        if k + 1 < n_nokta:
            dg += f"L{xs[k + 1]:.1f} {py(gurultu[k]):.1f}"
    out.append(f'<path d="{dg}" fill="none" stroke="var(--ink-2)" stroke-width="1.4"/>')
    # sinyal
    ds = ""
    for k in range(n_nokta):
        ds += ("M" if k == 0 else "L") + f"{xs[k]:.1f} {py(sinyal[k]):.1f}"
        if k + 1 < n_nokta:
            ds += f"L{xs[k + 1]:.1f} {py(sinyal[k]):.1f}"
    out.append(f'<path d="{ds}" fill="none" stroke="var(--accent)" stroke-width="2.4"/>')
    for k in range(n_nokta):
        out.append(f'<circle cx="{xs[k]:.1f}" cy="{py(sinyal[k]):.1f}" r="4" fill="var(--accent)"/>')
        out.append(f'<text x="{xs[k]:.1f}" y="{py(sinyal[k]) - 9:.1f}" text-anchor="middle" class="s-mono2 s-vurgu">{sinyal[k]:.1f}</text>')
        out.append(f'<text x="{xs[k]:.1f}" y="{py(gurultu[k]) + 14:.1f}" text-anchor="middle" class="s-mono2">{gurultu[k]:.1f}</text>')
        # düşey ayraç
        out.append(f'<line x1="{xs[k]:.1f}" y1="{y1}" x2="{xs[k]:.1f}" y2="{y0}" stroke="var(--line)" stroke-width=".8" stroke-dasharray="2 4"/>')
    # ADC tam ölçek
    fsd = S["adc"]["tam_olcek_dbm"]
    out.append(f'<line x1="{x0}" y1="{py(fsd):.1f}" x2="{x1}" y2="{py(fsd):.1f}" class="spk-filtre"/>')
    out.append(f'<text x="{x1 - 4}" y="{py(fsd) - 5:.1f}" text-anchor="end" class="s-kucuk s-altin">ADC tam ölçek {fsd:+g} dBm → {fsd - sinyal[-1]:.0f} dB tepe payı</text>')
    # SNR okları
    for k, etiket in ((0, "SNR giriş"), (n_nokta - 1, "SNR çıkış")):
        X = xs[k] + (14 if k == 0 else -14)
        out.append(f'<line x1="{X:.1f}" y1="{py(sinyal[k]):.1f}" x2="{X:.1f}" y2="{py(gurultu[k]):.1f}" stroke="var(--green)" stroke-width="1.4" marker-end="url(#ok-kontrol)" marker-start="url(#ok-kontrol)"/>')
        out.append(f'<text x="{X + (6 if k == 0 else -6):.1f}" y="{(py(sinyal[k]) + py(gurultu[k])) / 2 + 4:.1f}" class="s-kucuk s-yesil" text-anchor="{"start" if k == 0 else "end"}">{etiket} {sinyal[k] - gurultu[k]:.1f} dB</text>')
    out.append(f'<text x="{x0 + 6}" y="{py(gurultu[0]) + 30:.1f}" class="s-kucuk">kTB·B = {n0:.1f} dBm (300 MHz, NF 0)</text>')
    # kümülatif NF satırı
    out.append(f'<text x="{x0 - 60}" y="{y0 + 22}" class="s-kucuk">kümülatif NF</text>')
    out.append(f'<text x="{x0 - 60}" y="{y0 + 40}" class="s-kucuk">kümülatif G</text>')
    for k in range(1, n_nokta):
        out.append(f'<text x="{xs[k]:.1f}" y="{y0 + 22}" text-anchor="middle" class="s-mono s-kirmizi">{adim[k - 1][0]:.2f}</text>')
        out.append(f'<text x="{xs[k]:.1f}" y="{y0 + 40}" text-anchor="middle" class="s-mono2">{adim[k - 1][1]:+.1f}</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 66}" text-anchor="middle" class="s-metin2">Friis: kaskad NF = {nf_top:.2f} dB = SNR kaybı ({sinyal[0] - gurultu[0]:.1f} → {sinyal[-1] - gurultu[-1]:.1f} dB). LNA\'dan sonraki blokların katkısı 20 dB kazançla bölünür.</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 84}" text-anchor="middle" class="s-kucuk">Sistem bütçesi NF = {S["on_uc"]["nf_toplam_db"]} dB: LNA öncesi kablo/konektör kaybı (~1 dB doğrudan eklenir) + ADC eşdeğer gürültüsü + sıcaklık/üretim payı. Sayılar öğreticidir.</text>')
    yaz("g-40-seviye-diyagrami.svg", out)
    return nf_top, sinyal, gurultu


# ================================================================== g-41
def g_41():
    """Bant genişliği–gürültü tabanı: log eksende kTB·B ve +NF; sağda darbe spektrumu ile iki farklı almaç bandı."""
    W, H = 860, 400
    nf = S["on_uc"]["nf_toplam_db"]
    snr = S["tespit"]["tespit_snr_db"]
    out = bas("g41", W, H, f"Bant genişliği ile gürültü tabanı ve hassasiyet ilişkisi. Solda logaritmik bant genişliği ekseni (1 kHz–10 GHz): kTB·B çizgisi (NF = 0), NF = {nf} dB ile kayan gürültü tabanı ve +{snr} dB tespit SNR'ı ile MDS; 2 MHz (darbeye eşlenik), 300 MHz (referans) ve 1 GHz noktaları işaretli. Her on kat bant genişliği tabanı 10 dB yükseltir. Sağda 1 µs darbenin spektrumu üstünde iki almaç bandı: dar bant (2 MHz) az gürültü alır ama darbenin frekansını önceden bilmeyi gerektirir; geniş bant (300 MHz) darbeyi nerede olursa olsun yakalar (POI), bedeli 21.8 dB daha yüksek gürültü tabanı.")
    x0, x1, y0, y1 = 70, 470, 330, 50
    bmin, bmax = 1e3, 1e10
    ymin, ymax = -150, -40
    px = lambda b: x0 + (math.log10(b) - 3) / 7 * (x1 - x0)
    py = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    out.append('<text x="70" y="30" class="s-baslik">Gürültü tabanı = kTB · B · F</text>')
    # eksen
    for e in range(3, 11):
        X = px(10 ** e)
        out.append(f'<line x1="{X:.1f}" y1="{y1}" x2="{X:.1f}" y2="{y0}" class="izgara"/>')
        etik = {3: "1 kHz", 4: "10 k", 5: "100 k", 6: "1 MHz", 7: "10 M", 8: "100 M", 9: "1 GHz", 10: "10 G"}[e]
        out.append(f'<text x="{X:.1f}" y="{y0 + 14}" text-anchor="middle" class="s-mono2">{etik}</text>')
    for v in range(-150, -39, 10):
        out.append(f'<line x1="{x0}" y1="{py(v):.1f}" x2="{x1}" y2="{py(v):.1f}" class="izgara"/>')
        out.append(f'<text x="{x0 - 6}" y="{py(v) + 4:.1f}" text-anchor="end" class="s-mono2">{v}</text>')
    out.append(f'<rect x="{x0}" y="{y1}" width="{x1 - x0}" height="{y0 - y1}" class="eksen"/>')
    # gürültü dolgusu NF'li çizginin altı
    out.append(f'<path d="M{px(bmin):.1f} {py(KTB + 30 + nf):.1f}L{px(bmax):.1f} {py(KTB + 100 + nf):.1f}L{px(bmax):.1f} {y0}L{px(bmin):.1f} {y0}Z" class="spk-gurultu" opacity=".55"/>')
    for ofs, kls, etiket in ((0, 'stroke="var(--ink-2)" stroke-width="1.2" stroke-dasharray="4 3"', "kTB·B (NF = 0)"),
                             (nf, 'stroke="var(--red)" stroke-width="2"', f"taban, NF = {nf} dB"),
                             (nf + snr, 'stroke="var(--green)" stroke-width="2"', f"MDS = taban + {snr} dB")):
        out.append(f'<line x1="{px(bmin):.1f}" y1="{py(KTB + 30 + ofs):.1f}" x2="{px(bmax):.1f}" y2="{py(KTB + 100 + ofs):.1f}" {kls}/>')
        out.append(f'<text x="{px(1.3e3):.1f}" y="{py(KTB + 31 + ofs) + (13 if ofs == 0 else -5):.1f}" class="s-kucuk">{etiket}</text>')
    # noktalar
    for b, ad in ((2e6, "2 MHz"), (300e6, "300 MHz"), (1e9, "1 GHz")):
        t = KTB + db10(b) + nf
        out.append(f'<circle cx="{px(b):.1f}" cy="{py(t):.1f}" r="4.5" fill="var(--red)"/>')
        out.append(f'<circle cx="{px(b):.1f}" cy="{py(t + snr):.1f}" r="4" fill="var(--green)"/>')
        out.append(f'<text x="{px(b) + 7:.1f}" y="{py(t) + 14:.1f}" class="s-mono2">{ad}: {t:.1f}</text>')
        out.append(f'<text x="{px(b) + 7:.1f}" y="{py(t + snr) - 6:.1f}" class="s-mono2 s-yesil">MDS {t + snr:.1f}</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 32}" text-anchor="middle" class="s-kucuk">bant genişliği B (log) · dBm — her ×10 bant = +10 dB gürültü</text>')
    # sağ panel: darbe spektrumu + iki bant
    fx0, fx1, fy0, fy1 = 540, 830, 330, 50
    out.append('<text x="540" y="30" class="s-baslik">Aynı darbe, iki almaç bandı</text>')
    xmin, xmax = -160, 160   # MHz, darbe f0 = 0 merkezde
    fpx = lambda f: fx0 + (f - xmin) / (xmax - xmin) * (fx1 - fx0)
    fpy = lambda v: fy0 - (v + 40) / 43 * (fy0 - fy1)
    out.append(eksen(fx0, fx1, fy0, fy1, [-150, -100, -50, 0, 50, 100, 150], [0, -20, -40], xmin, xmax, -40, 3, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    # gürültü tabanı: taban ~ sinyal tepe−(−60 − (−83.2)) → sinyal −60 dBm ise tepe SNR 23 dB (300 MHz); göstermek için sabit gri şerit −23 dB
    n300 = KTB + db10(300e6) + nf
    snr300 = S["sinyal"]["seviye_dbm_giris"] - n300
    out.append(f'<rect x="{fx0}" y="{fpy(-snr300):.1f}" width="{fx1 - fx0}" height="{fy0 - fpy(-snr300):.1f}" class="spk-gurultu" opacity=".6"/>')
    out.append(f'<text x="{fx0 + 4}" y="{fpy(-snr300) - 4:.1f}" class="s-kucuk">gürültü tabanı (300 MHz): darbe tepesinin {snr300:.1f} dB altında</text>')
    n2 = KTB + db10(2e6) + nf
    out.append(f'<line x1="{fpx(-1)}" y1="{fpy(-(S["sinyal"]["seviye_dbm_giris"] - n2)):.1f}" x2="{fpx(1)}" y2="{fpy(-(S["sinyal"]["seviye_dbm_giris"] - n2)):.1f}" stroke="var(--ink-2)" stroke-width="3"/>')
    nf_ = 1200
    fsx = [xmin + (xmax - xmin) * k / (nf_ - 1) for k in range(nf_)]
    sp = [20 * math.log10(max(abs(sinc(f * 1.0)), 1e-6)) for f in fsx]  # PW 1 µs, f MHz
    d = path_from(fsx, sp, fx0, fx1, fy0, fy1, xmin, xmax, -40, 3)
    out.append(f'<path d="{d}L{fx1} {fy0}L{fx0} {fy0}Z" class="spk-sinyal" opacity=".25"/>')
    out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.2"/>')
    # bantlar
    out.append(f'<rect x="{fpx(-150):.1f}" y="{fy1 + 6}" width="{fpx(150) - fpx(-150):.1f}" height="{fy0 - fy1 - 6:.1f}" fill="none" class="spk-filtre"/>')
    out.append(f'<text x="{fpx(-148):.1f}" y="{fy1 + 20}" class="s-kucuk s-altin">geniş: 300 MHz → taban {n300:.1f} dBm, POI yüksek</text>')
    out.append(f'<rect x="{fpx(-1):.1f}" y="{fy1 + 30}" width="{fpx(1) - fpx(-1):.1f}" height="{fy0 - fy1 - 30:.1f}" fill="var(--gold)" opacity=".25"/>')
    out.append(f'<text x="{fpx(3):.1f}" y="{fy1 + 44}" class="s-kucuk s-altin">dar: 2 MHz → taban {n2:.1f} dBm</text>')
    out.append(f'<text x="{fpx(3):.1f}" y="{fy1 + 58}" class="s-kucuk">ama f₀ bilinmeli ya da taranmalı</text>')
    out.append(f'<text x="{fpx(3):.1f}" y="{fy1 + 72}" class="s-kucuk">(POI düşer)</text>')
    out.append(f'<text x="{(fx0 + fx1) / 2:.0f}" y="{fy0 + 32}" text-anchor="middle" class="s-kucuk">f − f₀ (MHz) · dB (darbe tepesine göre)</text>')
    yaz("g-41-bant-gurultu-tabani.svg", out)


# ================================================================== g-12
def g_12():
    """Üç cetvel: anten dBm, ADC girişi dBm (+40 dB kazanç), dBFS (0 dBFS = +4 dBm)."""
    W, H = 860, 340
    G = S["on_uc"]["kazanc_toplam_db"]
    fsd = S["adc"]["tam_olcek_dbm"]
    giris = S["sinyal"]["seviye_dbm_giris"]
    taban_in = KTB + db10(300e6) + S["on_uc"]["nf_toplam_db"]
    out = bas("g12", W, H, f"Üç cetvel: aynı seviyenin anten girişinde dBm, ADC girişinde dBm (zincir kazancı +{G} dB) ve sayısal alanda dBFS (0 dBFS = +{fsd} dBm) karşılıkları. İşaretli seviyeler: ADC tam ölçeği, referans darbe (−60 dBm antende → −20 dBm ADC'de → −24 dBFS), 300 MHz gürültü tabanı ve MDS. İki sabit (kazanç ve tam ölçek dBm'i) bilinince FFT ekranındaki dBFS anten girişine referanslanır.")
    x_ant, x_adc, x_fs = 150, 430, 710
    ymin, ymax = -100, 10          # ADC girişi dBm ölçeği
    y0, y1 = 290, 70
    py = lambda v: y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    for x, ad, ofs, kls, sym in ((x_ant, "anten girişi (dBm)", -G, "s-altin", "anten"), (x_adc, "ADC girişi (dBm)", 0, "s-altin", "adc"), (x_fs, "sayısal alan (dBFS)", -fsd, "s-vurgu", "fft")):
        out.append(f'<rect x="{x - 8}" y="{y1}" width="16" height="{y0 - y1}" fill="var(--dia-blok)" stroke="var(--line-2)"/>')
        out.append(f'<use href="#sym-{sym}" x="{x - 30}" y="8" width="60" height="40"/>')
        out.append(f'<text x="{x}" y="{y1 - 8}" text-anchor="middle" class="s-baslik {kls}">{ad}</text>')
        for v in range(-100, 11, 10):
            yy = py(v)
            out.append(f'<line x1="{x - 12}" y1="{yy:.1f}" x2="{x + 12}" y2="{yy:.1f}" stroke="var(--ink-3)" stroke-width="1"/>')
            out.append(f'<text x="{x - 16}" y="{yy + 4:.1f}" text-anchor="end" class="s-mono2">{v + ofs:+d}</text>')
    isaretler = [(fsd, "ADC tam ölçek", f"+{fsd} dBm = 0 dBFS", "s-kirmizi"),
                 (giris + G, "referans darbe", f"{giris} → {giris + G} dBm → {giris + G - fsd} dBFS", "s-vurgu"),
                 (taban_in + G + 15, "MDS", f"{taban_in + 15:.1f} → {taban_in + 15 + G:.1f} dBm → {taban_in + 15 + G - fsd:.1f} dBFS", "s-yesil"),
                 (taban_in + G, "gürültü tabanı (300 MHz)", f"{taban_in:.1f} → {taban_in + G:.1f} dBm → {taban_in + G - fsd:.1f} dBFS", "s-kirmizi")]
    for v, ad, metin, kls in isaretler:
        yy = py(v)
        out.append(f'<line x1="{x_ant}" y1="{yy:.1f}" x2="{x_fs}" y2="{yy:.1f}" stroke="var(--ink-2)" stroke-width="1" stroke-dasharray="4 3"/>')
        for x in (x_ant, x_adc, x_fs):
            out.append(f'<circle cx="{x}" cy="{yy:.1f}" r="3.5" fill="var(--accent)"/>')
        out.append(f'<text x="{x_fs + 16}" y="{yy + 4:.1f}" class="s-kucuk {kls}">{ad}</text>')
        out.append(f'<text x="{(x_ant + x_adc) / 2:.0f}" y="{yy - 5:.1f}" text-anchor="middle" class="s-kucuk">{metin}</text>')
    out.append(f'<line x1="{x_ant + 16}" y1="{y0 + 18}" x2="{x_adc - 16}" y2="{y0 + 18}" class="yol-analog" marker-end="url(#ok-analog)"/>')
    out.append(f'<text x="{(x_ant + x_adc) / 2:.0f}" y="{y0 + 36}" text-anchor="middle" class="s-metin2">+{G} dB zincir kazancı (ölçülür, sıcaklıkla kayar)</text>')
    out.append(f'<line x1="{x_adc + 16}" y1="{y0 + 18}" x2="{x_fs - 16}" y2="{y0 + 18}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    out.append(f'<text x="{(x_adc + x_fs) / 2:.0f}" y="{y0 + 36}" text-anchor="middle" class="s-metin2">−{fsd} dB: 0 dBFS = +{fsd} dBm (ADC sabiti)</text>')
    yaz("g-12-uc-cetvel.svg", out)


# ================================================================== g-42
def g_42():
    """Gürültünün istatistiği: Gauss PDF (gerilim), I/Q saçılımı, zarfın Rayleigh dağılımı ve 5.26σ eşiği."""
    import random
    W, H = 860, 330
    esik = S["tespit"]["esik_rayleigh_sigma"]
    out = bas("g42", W, H, f"Gürültünün üç istatistik yüzü (hesaplanmış). Solda tek kanalın (I ya da Q) Gauss olasılık yoğunluğu: ortalama 0, standart sapma σ; ±3σ dışı %0.27. Ortada 600 kompleks gürültü örneğinin I/Q düzleminde saçılımı: yönsüz bulut, çoğu 3σ çemberi içinde. Sağda zarfın (√(I²+Q²)) Rayleigh dağılımı: sıfırda sıfır, tepe σ'da, kuyruk Gauss'tan uzun; Pfa = 10⁻⁶ eşiği {esik}σ işaretli (Bölüm 21).")
    x0, x1, y0, y1 = 50, 290, 270, 60
    n = 240
    xs = [-4 + 8 * k / (n - 1) for k in range(n)]
    ys = [math.exp(-x * x / 2) / math.sqrt(TAU) for x in xs]
    out.append('<text x="50" y="30" class="s-baslik">Tek kanal: Gauss</text>')
    out.append(eksen(x0, x1, y0, y1, [-3, -2, -1, 0, 1, 2, 3], [], -4, 4, 0, 0.45, lambda v: (f"{v:+d}σ" if v else "0"), str))
    d = cizgi_yolu(xs, ys, x0, x1, y0, y1, -4, 4, 0, 0.45, False)
    out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-gurultu" opacity=".7"/>')
    out.append(f'<path d="{d}" fill="none" stroke="var(--ink)" stroke-width="1.6"/>')
    px = lambda v: x0 + (v + 4) / 8 * (x1 - x0)
    py = lambda v: y0 - v / 0.45 * (y0 - y1)
    kx = [x for x in xs if x >= 3]
    ky = [math.exp(-x * x / 2) / math.sqrt(TAU) for x in kx]
    dk = cizgi_yolu(kx, ky, x0, x1, y0, y1, -4, 4, 0, 0.45, False)
    out.append(f'<path d="{dk}L{x1} {y0}L{px(3):.1f} {y0}Z" fill="var(--red)" opacity=".6"/>')
    out.append(f'<line x1="{px(1):.1f}" y1="{py(0.242):.1f}" x2="{px(-1):.1f}" y2="{py(0.242):.1f}" stroke="var(--accent)" stroke-width="1.4"/>')
    out.append(f'<text x="{px(0):.1f}" y="{py(0.242) - 6:.1f}" text-anchor="middle" class="s-kucuk s-vurgu">σ = rms = √güç</text>')
    out.append(f'<text x="{px(3.1):.1f}" y="{py(0.05):.1f}" class="s-kucuk s-kirmizi">P(&gt;3σ) = %0.13</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">gerilim (σ birimiyle) · −83.2 dBm → σ = 15.5 µV</text>')
    cx, cy, R = 430, 165, 95
    out.append('<text x="335" y="30" class="s-baslik">I/Q düzlemi: yönsüz bulut</text>')
    out.append(f'<line x1="{cx - R - 10}" y1="{cy}" x2="{cx + R + 10}" y2="{cy}" stroke="var(--ink-3)" stroke-width="1"/>')
    out.append(f'<line x1="{cx}" y1="{cy + R + 10}" x2="{cx}" y2="{cy - R - 10}" stroke="var(--ink-3)" stroke-width="1"/>')
    for r_s, kls in ((1, "var(--line-2)"), (3, "var(--accent)")):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{R * r_s / 4:.1f}" fill="none" stroke="{kls}" stroke-width="1" stroke-dasharray="3 3"/>')
    out.append(f'<text x="{cx + R * 3 / 4 + 2:.1f}" y="{cy - 4}" class="s-kucuk s-vurgu">3σ</text>')
    out.append(f'<text x="{cx + R / 4 + 2:.1f}" y="{cy - 4}" class="s-kucuk">σ</text>')
    rnd = random.Random(42)
    for _ in range(600):
        i_, q_ = rnd.gauss(0, 1), rnd.gauss(0, 1)
        out.append(f'<circle cx="{cx + R * i_ / 4:.1f}" cy="{cy - R * q_ / 4:.1f}" r="1.6" fill="var(--accent)" opacity=".55"/>')
    out.append(f'<text x="{cx + R + 4}" y="{cy + 14}" class="s-kucuk">I</text><text x="{cx + 4}" y="{cy - R - 2}" class="s-kucuk">Q</text>')
    out.append(f'<text x="{cx}" y="{cy + R + 34}" text-anchor="middle" class="s-kucuk">I ve Q bağımsız Gauss, her biri σ² güçlü</text>')
    x0, x1 = 590, 830
    out.append('<text x="590" y="30" class="s-baslik">Zarf √(I²+Q²): Rayleigh</text>')
    rmax = 6
    xs = [rmax * k / (n - 1) for k in range(n)]
    ys = [r * math.exp(-r * r / 2) for r in xs]
    out.append(eksen(x0, x1, y0, y1, [0, 1, 2, 3, 4, 5, 6], [], 0, rmax, 0, 0.7, lambda v: (f"{v:d}σ" if v else "0"), str))
    d = cizgi_yolu(xs, ys, x0, x1, y0, y1, 0, rmax, 0, 0.7, False)
    out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-gurultu" opacity=".7"/>')
    out.append(f'<path d="{d}" fill="none" stroke="var(--ink)" stroke-width="1.6"/>')
    gy = [2 * math.exp(-r * r / 2) / math.sqrt(TAU) for r in xs]
    out.append(f'<path d="{cizgi_yolu(xs, gy, x0, x1, y0, y1, 0, rmax, 0, 0.7, False)}" fill="none" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')
    px = lambda v: x0 + v / rmax * (x1 - x0)
    py = lambda v: y0 - v / 0.7 * (y0 - y1)
    out.append(f'<line x1="{px(esik):.1f}" y1="{y1}" x2="{px(esik):.1f}" y2="{y0}" class="yol-gurultu"/>')
    out.append(f'<text x="{px(esik) - 4:.1f}" y="{y1 + 14}" text-anchor="end" class="s-kucuk s-kirmizi">eşik {esik}σ → Pfa = 10⁻⁶</text>')
    out.append(f'<text x="{px(1) + 4:.1f}" y="{py(0.61) - 4:.1f}" class="s-kucuk">tepe σ, ortalama 1.25σ</text>')
    out.append(f'<text x="{px(2.2):.1f}" y="{py(0.12):.1f}" class="s-kucuk">kesikli: |Gauss| (karşılaştırma)</text>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">zarf (σ birimiyle) — eşik bu kuyruğa konur (Bölüm 21, 22)</text>')
    yaz("g-42-gurultu-istatistigi.svg", out)


URETICILER = {"g-10": g_10, "g-11": g_11, "g-20": g_20, "g-21": g_21, "g-22": g_22,
              "g-30": g_30, "g-31": g_31, "g-32": g_32, "g-40": g_40, "g-41": g_41, "g-12": g_12, "g-42": g_42}


def main():
    secim = sys.argv[1:] or list(URETICILER)
    for ad in secim:
        if ad not in URETICILER:
            print("  ? bilinmeyen:", ad)
            continue
        URETICILER[ad]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
