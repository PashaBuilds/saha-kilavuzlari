#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k6.py — Kısım VI (FFT, pencereleme, FPGA'da FFT) hesaplanmış şekilleri

Bölüm 18: g-180 DFT korelasyon yorumu · g-181 bin ızgarası ve sızıntı · g-182 FFT tabanı / SNR / NSD
Bölüm 19: g-190 pencere galerisi · g-191 yan lobun zayıf sinyali maskelemesi
Bölüm 20: g-200 streaming FFT veri akışı · g-201 darbe–pencere hizalanması · g-202 spektrogram

Yardımcılar (fft, path_from, eksen, seyrelt) gen_figures.py'den alınır; yalnızca stdlib.

  python build/gen_figures_k6.py          # hepsi
  python build/gen_figures_k6.py g-182    # yalnızca biri
"""
import cmath
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_figures import fft, path_from, eksen, seyrelt, S, SVG, TAU  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FS_DDC = S["ddc"]["cikis_fs_msps"] * 1e6          # 300 MSPS kompleks
FS_ADC = S["adc"]["fs_hz"]                        # 2400 MSPS reel
NFFT = S["fft"]["n"]                              # 1024
BIN = FS_DDC / NFFT                               # 292 968.75 Hz
PW = S["sinyal"]["pw_s"]                          # 1 µs
CHIRP = S["sinyal"]["varyant_b"]["chirp_bw_hz"]   # 10 MHz
SNR14 = 6.02 * S["adc"]["bit"] + 1.76             # 86.04 dB

# Ek D (content/34-ek-d-pencere-tablosu.md) sayıları — burada yeniden hesaplanmaz, etikette kullanılır
EK_D = {
    "rect":            ("Dikdörtgen",        "−13.3 dB", "1.00", "1.00", "3.92 dB"),
    "hann":            ("Hann",              "−31.5 dB", "1.50", "1.50", "1.42 dB"),
    "hamming":         ("Hamming",           "−42.7 dB", "1.36", "1.38", "1.75 dB"),
    "blackman-harris": ("Blackman-Harris 4", "−92.0 dB", "2.00", "2.00", "0.83 dB"),
    "kaiser":          ("Kaiser β = 8",      "−58.7 dB", "1.67", "1.63", "1.18 dB"),
    "flat-top":        ("Flat-top",          "−93 dB*",  "3.77", "3.75", "0.01 dB"),
}


# ------------------------------------------------------------------ DSP eşdeğerleri
def i0(x):
    s, t, k = 1.0, 1.0, 1
    while True:
        t *= (x / (2 * k)) ** 2
        s += t
        k += 1
        if t < 1e-12 * s or k > 200:
            return s


def pencere(tip, N, beta=8.0):
    """dsp-core DSP.pencere eşdeğeri (periyodik tanım, Kaiser simetrik)."""
    if tip == "rect":
        return [1.0] * N
    if tip == "hann":
        return [0.5 - 0.5 * math.cos(TAU * k / N) for k in range(N)]
    if tip == "hamming":
        return [0.54 - 0.46 * math.cos(TAU * k / N) for k in range(N)]
    if tip == "blackman-harris":
        a = (0.35875, 0.48829, 0.14128, 0.01168)
        return [a[0] - a[1] * math.cos(TAU * k / N) + a[2] * math.cos(2 * TAU * k / N) - a[3] * math.cos(3 * TAU * k / N) for k in range(N)]
    if tip == "flat-top":
        a = (0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368)
        return [sum(((-1) ** m) * a[m] * math.cos(m * TAU * k / N) for m in range(5)) for k in range(N)]
    if tip == "kaiser":
        d = i0(beta)
        out = []
        for k in range(N):
            r = 2 * k / (N - 1) - 1
            out.append(i0(beta * math.sqrt(max(0.0, 1 - r * r))) / d)
        return out
    raise ValueError(tip)


def prng(seed):
    """Küçük deterministik LCG + Box-Muller (yalnızca şekil için)."""
    st = [seed]

    def u():
        st[0] = (st[0] * 1103515245 + 12345) % 2 ** 31
        return (st[0] + 0.5) / 2 ** 31

    def gauss(sigma=1.0):
        return sigma * math.sqrt(-2 * math.log(u())) * math.cos(TAU * u())
    return gauss


def spektrum_kompleks(x, tip="rect", zp=1):
    """Kompleks dizi → dBFS (tam ölçek kompleks ton 0 dBFS), fftshift'li, opsiyonel sıfır doldurma."""
    N = len(x)
    w = pencere(tip, N)
    s1 = sum(w)
    xs = [x[k] * w[k] for k in range(N)] + [0j] * (N * (zp - 1))
    X = fft(xs)
    M = len(X)
    out = [20 * math.log10(max(abs(X[k]) / s1, 1e-15)) for k in range(M)]
    return out[M // 2:] + out[:M // 2]


def spektrum_reel(x, tip="rect"):
    """Reel dizi → tek taraflı dBFS (tam ölçek sinüs 0 dBFS), 0…fs/2, N/2 bin."""
    N = len(x)
    w = pencere(tip, N)
    s1 = sum(w)
    X = fft([complex(x[k] * w[k], 0.0) for k in range(N)])
    return [20 * math.log10(max(2 * abs(X[k]) / s1, 1e-15)) for k in range(N // 2)]


def dtft_db(w, oversample=64, binler=12):
    """Pencerenin DTFT'si (dB, tepe 0), ±binler aralığında, bin başına oversample nokta."""
    N = len(w)
    s1 = sum(w)
    M = N * oversample
    X = fft([complex(v, 0) for v in w] + [0j] * (M - N))
    xs, ys = [], []
    lim = int(binler * oversample)
    for m in range(-lim, lim + 1):
        xs.append(m / oversample)
        ys.append(20 * math.log10(max(abs(X[m % M]) / s1, 1e-15)))
    return xs, ys


def svg_bas(gid, W, H, baslik):
    return [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-{gid}">',
            f'<title id="t-{gid}">{baslik}</title>']


def yaz(ad, satirlar):
    (SVG / ad).write_text("\n".join(satirlar) + "\n</svg>", encoding="utf-8")
    print(f"  ✓ {ad}")


def px_of(v, vmin, vmax, p0, p1):
    return p0 + (v - vmin) / (vmax - vmin) * (p1 - p0)


# =================================================================== g-180
def g_180():
    """DFT = N referans sinüsle korelasyon. N = 32, x = cos(2π·5n/32) + 0.5·cos(2π·11n/32)."""
    N = 32
    x = [math.cos(TAU * 5 * n / N) + 0.5 * math.cos(TAU * 11 * n / N) for n in range(N)]
    W, H = 860, 470
    o = svg_bas("g180", W, H, "DFT'nin korelasyon yorumu: 32 örneklik giriş dizisi (üstte solda), üç referans kosinüsle (k = 3, 5, 11) nokta nokta çarpılıp toplanır; k = 3'te çarpımlar birbirini götürür ve toplam 0 olur, k = 5'te tüm çarpımlar pozitif kalır ve toplam 16 (N/2) çıkar, k = 11'de toplam 8; sağda 0…16 arası tüm bin'ler için |X[k]| çubukları — yalnızca 5 ve 11'de çubuk var.")
    # --- sol: giriş
    x0, x1, y0, y1 = 40, 330, 120, 30
    o.append(f'<text x="{x0}" y="{y1 - 10}" class="s-baslik">Giriş x[n] — N = 32 örnek</text>')
    o.append(eksen(x0, x1, y0, y1, [0, 8, 16, 24, 31], [-1.5, 0, 1.5], 0, 31, -1.6, 1.6, lambda v: f"{v:d}", lambda v: f"{v:.1f}"))
    ym = (y0 + y1) / 2
    for n in range(N):
        px = px_of(n, 0, 31, x0, x1)
        py = px_of(x[n], -1.6, 1.6, y0, y1)
        o.append(f'<line x1="{px:.1f}" y1="{ym:.1f}" x2="{px:.1f}" y2="{py:.1f}" class="yol-sayisal"/><circle cx="{px:.1f}" cy="{py:.1f}" r="2.4" fill="var(--accent)"/>')
    o.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">n (örnek) · x = cos(2π·5n/32) + 0.5·cos(2π·11n/32)</text>')
    # --- orta: üç referans ve çarpımlar
    o.append(f'<text x="{x0}" y="170" class="s-baslik">Referans kosinüs ile çarp, topla → X[k]</text>')
    kk = [3, 5, 11]
    for i, k in enumerate(kk):
        py1 = 185 + i * 92
        py0 = py1 + 70
        ref = [math.cos(TAU * k * n / N) for n in range(N)]
        carp = [x[n] * ref[n] for n in range(N)]
        top = sum(carp)
        o.append(eksen(x0, x1, py0, py1, [0, 16, 31], [], 0, 31, -1.6, 1.6, lambda v: f"{v:d}"))
        # referans (gri kesikli sürekli)
        xs = [n / 4 for n in range(0, 4 * 31 + 1)]
        ys = [math.cos(TAU * k * v / N) for v in xs]
        o.append(f'<path d="{path_from(xs, ys, x0, x1, py0, py1, 0, 31, -1.6, 1.6)}" class="yol-saat" stroke-width="1"/>')
        ymid = (py0 + py1) / 2
        for n in range(N):
            px = px_of(n, 0, 31, x0, x1)
            py = px_of(carp[n], -1.6, 1.6, py0, py1)
            kls = "var(--accent)" if carp[n] >= 0 else "var(--red)"
            o.append(f'<rect x="{px - 2.5:.1f}" y="{min(py, ymid):.1f}" width="5" height="{abs(py - ymid):.1f}" fill="{kls}" opacity=".75"/>')
        o.append(f'<text x="{x0 + 4}" y="{py1 + 12}" class="s-mono2">k = {k}</text>')
        renk = "s-vurgu" if abs(top) > 1 else "s-kirmizi"
        o.append(f'<text x="{x1 + 10}" y="{ymid - 4:.1f}" class="s-metin {renk}">∑ = {top:+.1f}</text>')
        o.append(f'<text x="{x1 + 10}" y="{ymid + 12:.1f}" class="s-kucuk">{"pozitif ve negatif çarpımlar birbirini götürür" if abs(top) < 1 else ("tüm çarpımlar aynı işaretli: hizalı" if k == 5 else "yarı genlik → yarı toplam")}</text>')
    o.append(f'<text x="{x0}" y="{H - 12}" class="s-kucuk">Gri kesikli: referans cos(2πkn/N). Çubuk: x[n]·ref[n] (mavi +, kırmızı −). Gerçek DFT aynı işlemi sin ile de yapar (kompleks referans); |X[k]| ikisinin karesel toplamıdır.</text>')
    # --- sağ: |X[k]| çubukları
    bx0, bx1, by0, by1 = 600, 830, 300, 60
    o.append(f'<text x="{bx0}" y="{by1 - 30}" class="s-baslik">|X[k]| — 17 bin (reel giriş, 0…N/2)</text>')
    Xk = fft([complex(v, 0) for v in x])
    o.append(eksen(bx0, bx1, by0, by1, [0, 5, 11, 16], [0, 8, 16], 0, 16, 0, 18, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    for k in range(17):
        px = px_of(k, 0, 16, bx0, bx1)
        mag = abs(Xk[k])
        py = px_of(mag, 0, 18, by0, by1)
        if mag > 0.01:
            o.append(f'<rect x="{px - 5:.1f}" y="{py:.1f}" width="10" height="{by0 - py:.1f}" class="spk-sinyal"/>')
            o.append(f'<text x="{px:.1f}" y="{py - 5:.1f}" text-anchor="middle" class="s-mono2">{mag:.0f}</text>')
    o.append(f'<text x="{bx1}" y="{by0 + 28}" text-anchor="end" class="s-kucuk">bin k · bin genişliği = fs/N</text>')
    o.append(f'<text x="{bx0}" y="{by0 + 58}" class="s-metin2">Bin 5: genlik 1 → N/2 = 16</text>')
    o.append(f'<text x="{bx0}" y="{by0 + 76}" class="s-metin2">Bin 11: genlik 0.5 → 8</text>')
    o.append(f'<text x="{bx0}" y="{by0 + 94}" class="s-metin2">Diğer bin\'ler: tam 0 — ton bin</text>')
    o.append(f'<text x="{bx0}" y="{by0 + 108}" class="s-metin2">merkezinde (koherent örnekleme)</text>')
    o.append(f'<text x="{bx0}" y="{by0 + 132}" class="s-kucuk">FFT aynı 17 (aslında 32) toplamı</text>')
    o.append(f'<text x="{bx0}" y="{by0 + 146}" class="s-kucuk">N² yerine N·log₂N çarpımla hesaplar.</text>')
    yaz("g-180-dft-korelasyon.svg", o)


# =================================================================== g-181
def g_181():
    """Bin ızgarası ve sızıntı: 34.00 periyot (koherent) vs 34.13 periyot (10.000 MHz) — fs 300 MSPS, N 1024."""
    N, fs = NFFT, FS_DDC
    T = N / fs
    f_koh = 34 * BIN                 # 9.9609375 MHz
    f_sz = 10.0e6                    # 34.13 bin
    W, H = 860, 560
    o = svg_bas("g181", W, H, "Bin ızgarası ve spektral sızıntı. Üst sıra: 1024 örneklik çerçevenin sonu ile periyodik kopyasının başı — 34 tam periyotluk 9.961 MHz ton kesintisiz devam eder, 34.13 periyotluk 10.000 MHz tonda çerçeve sınırında sıçrama oluşur. Alt sıra: aynı iki tonun bin 24–44 arasındaki spektrumu; sürekli DTFT gri çizgi, bin örnekleri nokta. Koherent tonda tek bin 0 dBFS, diğerleri sıfır; 10 MHz tonda enerji komşu bin'lere sızar (−13 dB yan lob, ~−40 dB uzak bin'ler) ve tepe ≈ 0.3 dB düşer (scalloping).")
    # --- üst: zaman panelleri
    for i, (f, ad, koh) in enumerate([(f_koh, "34.00 periyot → koherent (9.961 MHz)", True), (f_sz, "34.13 periyot → sızıntı (10.000 MHz)", False)]):
        x0 = 50 + i * 410
        x1 = x0 + 370
        y1, y0 = 40, 170
        tmin, tmax = T - 0.25e-6, T + 0.25e-6
        o.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">{ad}</text>')
        o.append(eksen(x0, x1, y0, y1, [T - 0.2e-6, T, T + 0.2e-6], [-1, 0, 1], tmin, tmax, -1.3, 1.3,
                       lambda v: ("T−0.2µs" if v < T - 1e-9 else ("T = 3.41 µs" if abs(v - T) < 1e-9 else "T+0.2µs")), lambda v: f"{v:d}"))
        # çerçeve içi (sol yarı) ve periyodik kopya (sağ yarı): kopyada t → t − T
        xs, ys = [], []
        M = 400
        for m in range(M + 1):
            t = tmin + (tmax - tmin) * m / M
            tt = t if t < T else t - T
            xs.append(t)
            ys.append(math.cos(TAU * f * tt))
        # çerçeve boyası
        px_T = px_of(T, tmin, tmax, x0, x1)
        o.append(f'<rect x="{x0}" y="{y1}" width="{px_T - x0:.1f}" height="{y0 - y1}" fill="var(--accent-soft)" opacity=".45"/>')
        o.append(f'<text x="{px_T - 6:.1f}" y="{y1 + 14}" text-anchor="end" class="s-kucuk s-vurgu">çerçeve (N = 1024 örnek)</text>')
        o.append(f'<text x="{px_T + 6:.1f}" y="{y1 + 14}" class="s-kucuk">periyodik kopya (DFT\'nin varsayımı)</text>')
        o.append(f'<path d="{path_from(xs, ys, x0, x1, y0, y1, tmin, tmax, -1.3, 1.3)}" class="yol-sayisal"/>')
        o.append(f'<line x1="{px_T:.1f}" y1="{y1}" x2="{px_T:.1f}" y2="{y0}" class="yol-saat"/>')
        if not koh:
            jy = px_of(math.cos(TAU * f * (T - 1e-12)), -1.3, 1.3, y0, y1)
            o.append(f'<circle cx="{px_T:.1f}" cy="{jy:.1f}" r="5" fill="none" stroke="var(--red)" stroke-width="1.6"/>')
            o.append(f'<text x="{px_T + 8:.1f}" y="{jy - 8:.1f}" class="s-kucuk s-kirmizi">sıçrama → geniş bant enerji</text>')
        o.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">zaman · fs = 300 MSPS</text>')
    # --- alt: spektrum panelleri
    for i, (f, ad, koh) in enumerate([(f_koh, "koherent: tek bin", True), (f_sz, "sızıntı: bin\'lere yayılma + scalloping", False)]):
        x0 = 50 + i * 410
        x1 = x0 + 370
        y1, y0 = 240, 470
        bmin, bmax, ymin, ymax = 24, 44, -80, 5
        o.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">{ad}</text>')
        o.append(eksen(x0, x1, y0, y1, [24, 29, 34, 39, 44], [0, -20, -40, -60, -80], bmin, bmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        # DTFT (dikdörtgen pencere): |sin(πNδ)/(N sin(πδ))|
        fb = f / BIN
        xs, ys = [], []
        M = 800
        for m in range(M + 1):
            b = bmin + (bmax - bmin) * m / M
            d = b - fb
            v = abs(math.sin(math.pi * d) / (N * math.sin(math.pi * d / N))) if abs(d) > 1e-9 else 1.0
            xs.append(b)
            ys.append(20 * math.log10(max(v, 1e-8)))
        o.append(f'<path d="{path_from(xs, ys, x0, x1, y0, y1, bmin, bmax, ymin, ymax)}" stroke="var(--ink-3)" fill="none" stroke-width="1" opacity=".8"/>')
        # bin örnekleri
        x = [cmath.exp(1j * TAU * f * n / fs) for n in range(N)]
        sp = spektrum_kompleks(x, "rect")
        for b in range(bmin, bmax + 1):
            v = sp[N // 2 + b]
            px = px_of(b, bmin, bmax, x0, x1)
            py = px_of(max(v, ymin), ymin, ymax, y0, y1)
            o.append(f'<line x1="{px:.1f}" y1="{y0}" x2="{px:.1f}" y2="{py:.1f}" stroke="var(--accent)" stroke-width="1.2" opacity=".6"/>')
            o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{"var(--accent)" if v > -30 else "var(--red)"}"/>')
        o.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">bin no · 1 bin = 293 kHz · dBFS</text>')
        if koh:
            o.append(f'<text x="{x0 + 8}" y="{y1 + 18}" class="s-kucuk">DTFT\'nin sıfırları tam bin merkezlerine düşer:</text>')
            o.append(f'<text x="{x0 + 8}" y="{y1 + 32}" class="s-kucuk">diğer bin\'ler sıfır okur (picket fence — çitin arasından bakış).</text>')
        else:
            tepe = max(sp)
            o.append(f'<text x="{x0 + 8}" y="{y1 + 18}" class="s-kucuk s-kirmizi">tepe {tepe:.2f} dBFS (scalloping, 0.13 bin kayma)</text>')
            o.append(f'<text x="{x0 + 8}" y="{y1 + 32}" class="s-kucuk">yan lob zarfı ≈ 1/(π·δ): 10 bin ötede ≈ −30 dB</text>')
    o.append(f'<text x="50" y="{H - 40}" class="s-metin2">Sızıntı, sinyalin değil gözlemin özelliğidir: DFT çerçevenin periyodik tekrarını analiz eder; çerçeve sınırındaki sıçrama, dikdörtgen pencerenin sinc yan loblarıdır.</text>')
    o.append(f'<text x="50" y="{H - 22}" class="s-metin2">Çare iki türlü: bin merkezine oturt (koherent örnekleme — sahada nadiren mümkün) ya da çerçeve kenarlarını yumuşat (pencere — Bölüm 19).</text>')
    yaz("g-181-bin-izgarasi-sizinti.svg", o)


# =================================================================== g-182
def g_182():
    """FFT tabanı / SNR / NSD ilişkisi — reel 14-bit ADC çıkışı, fs 2400, N 1024, ton 600 MHz (bin 256)."""
    N, fs = NFFT, FS_ADC
    f = S["ddc"]["nco_hz"]                          # 600 MHz = bin 256 → koherent
    snr = SNR14
    sigma = math.sqrt(0.5 * 10 ** (-snr / 10))      # ton gücü 0.5 (genlik 1)
    g = prng(2024)
    W, H = 900, 640
    taban = -snr - 10 * math.log10(N / 2)
    taban4k = -snr - 10 * math.log10(4096 / 2)
    nsd = -snr - 10 * math.log10(fs / 2)
    binw = fs / N
    o = svg_bas("g182", W, H, f"FFT tabanı, SNR ve NSD'nin ilişkisi (hesaplanmış). Üstte 14-bit reel ADC çıkışının 1024 noktalı FFT'si: 0 dBFS ton 600 MHz'de, tek çekim gürültü tabanı yaklaşık {taban:.0f} dBFS çevresinde saçılır, 64 ortalamalı taban aynı seviyede düz bir çizgi olur. SNR = {snr:.1f} dB tonun tüm banttaki (0–1200 MHz) toplam gürültüye oranıdır; FFT tabanı = −SNR − 10·log10(N/2) = {taban:.1f} dBFS/bin; NSD = −SNR − 10·log10(fs/2) = {nsd:.1f} dBFS/Hz. Altta üç büyüklüğü birbirine bağlayan dönüşüm şeması: bin genişliği değişince yalnızca FFT tabanı değişir.")
    # --- spektrum paneli
    x0, x1, y0, y1 = 70, 860, 300, 40
    xmin, xmax, ymin, ymax = 0, fs / 2 / 1e6, -140, 5
    o.append(f'<text x="{x0}" y="{y1 - 14}" class="s-baslik">14-bit reel ADC çıkışı, N = 1024, dikdörtgen pencere, koherent ton — tek çekim (mavi) ve 64 ortalama (altın)</text>')
    o.append(eksen(x0, x1, y0, y1, [0, 200, 400, 600, 800, 1000, 1200], [0, -40, -80, -120], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    xs = [k * binw / 1e6 for k in range(N // 2)]
    acc = [0.0] * (N // 2)
    tek = None
    for it in range(64):
        x = [math.cos(TAU * f * n / fs) + g(sigma) for n in range(N)]
        x = [round(v * 8191) / 8191 for v in x]     # 14-bit kuantizasyon (mid-tread)
        sp = spektrum_reel(x, "rect")
        if tek is None:
            tek = sp
        for k in range(N // 2):
            acc[k] += 10 ** (sp[k] / 10)
    ort = [10 * math.log10(acc[k] / 64) for k in range(N // 2)]
    d = path_from(xs, tek, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    o.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-sinyal" opacity=".15"/>')
    o.append(f'<path d="{d}" stroke="var(--accent)" fill="none" stroke-width="1"/>')
    o.append(f'<path d="{path_from(xs, ort, x0, x1, y0, y1, xmin, xmax, ymin, ymax)}" stroke="var(--gold)" fill="none" stroke-width="1.6"/>')
    # teorik taban çizgileri
    for v, lab, kls in [(taban, f"FFT tabanı N = 1024: −{snr:.0f} − 10·log10(512) = {taban:.1f} dBFS/bin", "s-kirmizi"), (taban4k, f"N = 4096 olsaydı: {taban4k:.1f} dBFS/bin (4× N → −6 dB)", "s-mor")]:
        py = px_of(v, ymin, ymax, y0, y1)
        o.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" class="{"yol-gurultu" if kls == "s-kirmizi" else "yol-saat"}"/>')
        o.append(f'<text x="{x1 - 6}" y="{(py - 5) if kls == "s-kirmizi" else (py + 13):.1f}" text-anchor="end" class="s-kucuk {kls}">{lab}</text>')
    # SNR ok/braket
    pxt = px_of(f / 1e6, xmin, xmax, x0, x1)
    o.append(f'<path d="M{pxt + 40:.1f} {px_of(0, ymin, ymax, y0, y1):.1f} V{px_of(taban, ymin, ymax, y0, y1) - 4:.1f}" stroke="var(--ink-2)" stroke-width="1.2" marker-end="url(#ok-ince)" marker-start="url(#ok-ince)"/>')
    o.append(f'<text x="{pxt + 48:.1f}" y="{px_of(-50, ymin, ymax, y0, y1):.1f}" class="s-metin2">tepe − taban = SNR + işlem kazancı</text>')
    o.append(f'<text x="{pxt + 48:.1f}" y="{px_of(-58, ymin, ymax, y0, y1):.1f}" class="s-metin2">= {snr:.0f} + {10 * math.log10(N / 2):.1f} = {snr + 10 * math.log10(N / 2):.1f} dB</text>')
    o.append(f'<text x="{pxt + 48:.1f}" y="{px_of(-72, ymin, ymax, y0, y1):.1f}" class="s-kucuk">tek çekim taban ±10 dB saçılır; ortalama seviyeyi değil varyansı düşürür</text>')
    o.append(f'<text x="{pxt - 8:.1f}" y="{y1 + 14}" text-anchor="end" class="s-kucuk s-vurgu">ton 600 MHz, 0 dBFS</text>')
    o.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">frekans (MHz) · dBFS · bin = {binw / 1e6:.2f} MHz</text>')
    # --- ilişki şeması
    by = 380
    kutu = [(70, "SNR (datasheet)", f"{snr:.1f} dB", "referans bant: fs/2 = 1200 MHz", "ton gücü / tüm bant gürültü gücü", "blok-analog"),
            (350, "NSD", f"{nsd:.1f} dBFS/Hz", "referans bant: 1 Hz", "bant ve N'den bağımsız — değişmez", "blok-aktif"),
            (630, "FFT tabanı", f"{taban:.1f} dBFS/bin", f"referans bant: bin = {binw / 1e6:.2f} MHz (N = 1024)", "N ile değişir: 4·N → −6 dB", "blok")]
    for (bx, ad, deg, bant, not_, kls) in kutu:
        o.append(f'<rect x="{bx}" y="{by}" width="200" height="96" rx="8" class="{kls}"/>')
        o.append(f'<text x="{bx + 100}" y="{by + 22}" text-anchor="middle" class="s-baslik">{ad}</text>')
        o.append(f'<text x="{bx + 100}" y="{by + 46}" text-anchor="middle" class="s-mono" style="font-size:15px">{deg}</text>')
        o.append(f'<text x="{bx + 100}" y="{by + 66}" text-anchor="middle" class="s-kucuk">{bant}</text>')
        o.append(f'<text x="{bx + 100}" y="{by + 84}" text-anchor="middle" class="s-kucuk">{not_}</text>')
    # oklar ve dönüşümler
    o.append(f'<path d="M270 {by + 48} H346" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<text x="308" y="{by + 40}" text-anchor="middle" class="s-mono2">−10·log10(fs/2)</text>')
    o.append(f'<text x="308" y="{by + 66}" text-anchor="middle" class="s-kucuk">−{10 * math.log10(fs / 2):.1f} dB</text>')
    o.append(f'<path d="M550 {by + 48} H626" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<text x="588" y="{by + 40}" text-anchor="middle" class="s-mono2">+10·log10(bin·ENBW)</text>')
    o.append(f'<text x="588" y="{by + 66}" text-anchor="middle" class="s-kucuk">+{10 * math.log10(binw):.1f} dB (dikd.)</text>')
    o.append(f'<path d="M170 {by + 96} V{by + 130} H730 V{by + 100}" class="yol-kontrol" fill="none" marker-end="url(#ok-kontrol)"/>')
    o.append(f'<text x="450" y="{by + 146}" text-anchor="middle" class="s-mono2 s-yesil">kestirme: FFT tabanı = −SNR − 10·log10(N/2) = −{snr:.1f} − {10 * math.log10(N / 2):.1f} = {taban:.1f} dBFS</text>')
    o.append(f'<text x="70" y="{by + 178}" class="s-metin2">Üç sayı aynı gürültüyü üç farklı bantta ölçer. Datasheet SNR\'ı ile FFT tabanı arasındaki {10 * math.log10(N / 2):.0f} dB "kayıp" değil, bin\'in bandın 1/512\'si olmasıdır.</text>')
    o.append(f'<text x="70" y="{by + 198}" class="s-metin2">Kompleks I/Q girişte (DDC çıkışı) gürültü N bin\'e yayılır: işlem kazancı 10·log10(N) = {10 * math.log10(N):.1f} dB; NSD yolu her iki durumda aynı sonucu verir.</text>')
    o.append(f'<text x="70" y="{by + 224}" class="s-kucuk">Sayılar öğretici referans senaryodandır (14 bit ideal); gerçek ADC\'de datasheet SNR\'ı kullanılır. Pencere varsa taban +10·log10(ENBW) (Hann: +1.76 dB).</text>')
    yaz("g-182-fft-tabani-snr-nsd.svg", o)


# =================================================================== g-190
def g_190():
    """Pencere galerisi: 6 pencerenin zaman şekli ve DTFT'si (N = 64, 64× oversample), Ek D sayıları etikette."""
    tipler = ["rect", "hann", "hamming", "blackman-harris", "kaiser", "flat-top"]
    N = 64
    W, H = 900, 600
    o = svg_bas("g190", W, H, "Altı pencere fonksiyonunun zaman şekli (üst küçük panel) ve frekans yanıtı (alt panel, dB, ±12 bin): dikdörtgen en dar ana lob ama −13 dB yan lob; Hann −31.5 dB yan lob ve 18 dB/oktav düşüş; Hamming ilk yan lobu −42.7 dB'ye bastırır ama uzak yan loblar yavaş düşer; Blackman-Harris 4 terim −92 dB yan lob, 2 bin ana lob; Kaiser β=8 ayarlanabilir orta yol; flat-top 3.75 bin genişliğinde düz tepe, 0.01 dB scalloping. Her panelde Ek D'den en yüksek yan lob, ENBW ve scalloping kaybı yazılıdır.")
    for i, tip in enumerate(tipler):
        col, row = i % 3, i // 3
        cx = 50 + col * 290
        cy = 30 + row * 290
        ad, yl, enbw, b3, sc = EK_D[tip]
        w = pencere(tip, N)
        o.append(f'<text x="{cx}" y="{cy}" class="s-baslik">{ad}</text>')
        # zaman şekli
        tx0, tx1, ty0, ty1 = cx, cx + 240, cy + 60, cy + 12
        o.append(f'<rect x="{tx0}" y="{ty1}" width="{tx1 - tx0}" height="{ty0 - ty1}" class="eksen"/>')
        xs = list(range(N))
        ys = [max(-0.05, v) for v in w]
        o.append(f'<path d="{path_from(xs, ys, tx0, tx1, ty0, ty1, 0, N - 1, -0.1, 1.1)}L{tx1} {ty0}L{tx0} {ty0}Z" fill="var(--gold-soft)"/>')
        o.append(f'<path d="{path_from(xs, ys, tx0, tx1, ty0, ty1, 0, N - 1, -0.1, 1.1)}" stroke="var(--gold)" fill="none" stroke-width="1.6"/>')
        o.append(f'<text x="{tx1 - 4}" y="{ty0 - 4}" text-anchor="end" class="s-kucuk">w[n], N örnek</text>')
        # frekans yanıtı
        fx0, fx1, fy0, fy1 = cx + 30, cx + 240, cy + 235, cy + 100
        o.append(f'<text x="{cx}" y="{cy + 76}" class="s-kucuk">yan lob {yl} · ENBW {enbw} bin</text>')
        o.append(f'<text x="{cx}" y="{cy + 90}" class="s-kucuk">−3 dB {b3} bin · scallop {sc}</text>')
        xmin, xmax, ymin, ymax = -12, 12, -120, 2
        o.append(eksen(fx0, fx1, fy0, fy1, [-12, -6, 0, 6, 12], [0, -40, -80, -120], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        dx, dy = dtft_db(w, 64, 12)
        d = path_from(dx, dy, fx0, fx1, fy0, fy1, xmin, xmax, ymin, ymax)
        o.append(f'<path d="{d}L{fx1} {fy0}L{fx0} {fy0}Z" class="spk-sinyal" opacity=".14"/>')
        o.append(f'<path d="{d}" stroke="var(--accent)" fill="none" stroke-width="1.3"/>')
        o.append(f'<text x="{fx1}" y="{fy0 + 26}" text-anchor="end" class="s-kucuk">bin · dB</text>')
    o.append(f'<text x="50" y="{H - 12}" class="s-kucuk">Hesap: N = 64, 64× sıfır doldurmalı DTFT, tepe 0 dB. Sayılar Ek D (N = 1024) ile aynıdır; eksen bin cinsinden olduğundan şekil N\'den bağımsızdır. * ilk dipten sonra.</text>')
    yaz("g-190-pencere-galerisi.svg", o)


# =================================================================== g-191
def g_191():
    """Yan lobun zayıf sinyali maskelemesi: 0 dBFS ton (bin 34.27) yanında −70 dBFS ton 11.8 bin ötede — dikdörtgen vs Blackman-Harris."""
    N, fs = NFFT, FS_DDC
    f1, f2 = 34.27 * BIN, (34.27 + 11.8) * BIN
    g = prng(77)
    sigma = math.sqrt(10 ** (-110 / 10))          # bant içi gürültü −110 dBFS
    x = []
    for n in range(N):
        v = cmath.exp(1j * TAU * f1 * n / fs) + 10 ** (-70 / 20) * cmath.exp(1j * TAU * f2 * n / fs)
        v += complex(g(sigma / math.sqrt(2)), g(sigma / math.sqrt(2)))
        x.append(v)
    W, H = 860, 520
    o = svg_bas("g191", W, H, f"Yan lobun zayıf sinyali maskelemesi (hesaplanmış, N = 1024, fs = 300 MSPS). İki ton: 0 dBFS güçlü ton {f1 / 1e6:.2f} MHz'de (bin 34.27) ve −70 dBFS zayıf ton {f2 / 1e6:.2f} MHz'de (11.8 bin ötede). Üstte dikdörtgen pencere: güçlü tonun yan lobları 12 bin ötede hâlâ ≈ −32 dB'dedir ve zayıf ton bu zarfın altında kaybolur. Altta Blackman-Harris: yan loblar −92 dB'nin altına iner, zayıf ton −70 dBFS'te açıkça görünür; bedeli 2 bin genişliğinde ana lob ve gürültü tabanının 3 dB yükselmesi.")
    for i, (tip, ad) in enumerate([("rect", "Dikdörtgen pencere — zayıf ton yan lob zarfının altında"), ("blackman-harris", "Blackman-Harris — zayıf ton görünür")]):
        x0, x1, y1 = 60, 830, 40 + i * 240
        y0 = y1 + 180
        xmin, xmax, ymin, ymax = 5, 20, -130, 5
        sp = spektrum_kompleks(x, tip)
        xs = [(k - N / 2) * BIN / 1e6 for k in range(N)]
        xs, sp = zip(*[(xx, yy) for xx, yy in zip(xs, sp) if xmin <= xx <= xmax])   # panel dışını çizme
        o.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">{ad}</text>')
        o.append(eksen(x0, x1, y0, y1, [5, 7.5, 10, 12.5, 15, 17.5, 20], [0, -40, -80, -120], xmin, xmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:d}"))
        d = path_from(xs, sp, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        o.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-sinyal" opacity=".15"/>')
        o.append(f'<path d="{d}" stroke="var(--accent)" fill="none" stroke-width="1.2"/>')
        # zayıf tonun gerçek konumu ve seviyesi
        px2 = px_of(f2 / 1e6, xmin, xmax, x0, x1)
        py2 = px_of(-70, ymin, ymax, y0, y1)
        o.append(f'<line x1="{px2:.1f}" y1="{y1}" x2="{px2:.1f}" y2="{y0}" class="yol-saat"/>')
        o.append(f'<circle cx="{px2:.1f}" cy="{py2:.1f}" r="4.5" fill="none" stroke="var(--gold)" stroke-width="1.8"/>')
        o.append(f'<text x="{px2 + 8:.1f}" y="{py2 - 8:.1f}" class="s-kucuk s-altin">zayıf ton −70 dBFS (gerçek)</text>')
        sp_tam = spektrum_kompleks(x, tip)
        k2 = int(round(N / 2 + f2 / BIN))
        okunan = max(sp_tam[k2 - 1:k2 + 2])
        if tip == "rect":
            o.append(f'<text x="{px2 + 8:.1f}" y="{py2 + 34:.1f}" class="s-kucuk s-kirmizi">bu bin\'de okunan: {okunan:.0f} dBFS — sızıntı, ton değil</text>')
            o.append(f'<text x="{x1 - 8}" y="{y1 + 16}" text-anchor="end" class="s-kucuk">yan lob zarfı ≈ 20·log10(1/(π·δ)) → δ = 12 bin\'de ≈ −31 dB; −70 dBFS ton 40 dB altında kalır</text>')
        else:
            o.append(f'<text x="{px2 + 8:.1f}" y="{py2 + 34:.1f}" class="s-kucuk s-yesil">bu bin\'de okunan: {okunan:.1f} dBFS ✓</text>')
            o.append(f'<text x="{x1 - 8}" y="{y1 + 16}" text-anchor="end" class="s-kucuk">ana lob 2 bin\'e genişledi; gürültü tabanı 10·log10(2.0) = +3 dB yükseldi</text>')
        o.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">frekans (MHz) · dBFS · bant içi gürültü −110 dBFS</text>')
    o.append(f'<text x="60" y="{H - 14}" class="s-metin2">Aynı veri, aynı N; yalnızca pencere farklı. Dinamik aralık isteyen ölçümde pencere seçimi bit sayısı kadar belirleyicidir.</text>')
    yaz("g-191-yan-lob-maskeleme.svg", o)


# =================================================================== g-200
def g_200():
    """Streaming FFT veri akışı — blok şema (semboller + etiketler)."""
    W, H = 1160, 430
    o = svg_bas("g200", W, H, "FPGA'da streaming FFT veri akışı: DDC çıkışı 300 MSPS 16+16 bit I/Q → overlap tamponu (ping-pong BRAM, her 512 örnekte yeni 1024'lük çerçeve) → pencere çarpımı (Hann katsayı ROM'u, 512 giriş simetrik, tek DSP) → pipelined FFT çekirdeği (N = 1024, radix-2², ölçekleme takvimi register'dan, blok kayan nokta seçeneği) → bin ters çevirme (bit-reversed → doğal sıra) ve fftshift → |X|² = I² + Q² (36 bit → 20 bit dB/log2 LUT) → tepe bul / eşik → FIFO → PS. Kontrol register'ları yeşil: WIN_SEL, FFT_SCALE_SCH, FFT_NFFT, FFT_THR. Zamanlama: çerçeve süresi 3.41 µs, adım 1.71 µs, çekirdek gecikmesi ≈ N + pipeline saat.")
    y = 120
    bloklar = [
        (20, "DDC çıkışı", "I/Q 16+16 bit", "300 MSPS", "blok-aktif", None),
        (150, "overlap tamponu", "ping-pong BRAM", "2 × 1024 × 32 bit", "blok", None),
        (300, "× pencere", "Hann ROM 512×16", "1 DSP, simetri", "blok", "fir"),
        (450, "FFT çekirdeği", "pipelined N=1024", "radix-2², 10 kademe", "blok-aktif", "fft"),
        (600, "sıra + shift", "bit-reversed→doğal", "fftshift (k+N/2)", "blok", None),
        (740, "|X|²", "I²+Q² → 36 bit", "log2 LUT → 20 bit dB", "blok", "zarf"),
        (880, "tepe / eşik", "en büyük bin + komşu", "eşik üstü bin listesi", "blok", "cmp"),
        (1020, "FIFO → PS", "AXI-Stream / DMA", "bin no, dB, çerçeve no", "blok-kontrol", "fifo"),
    ]
    for i, (bx, ad, a1, a2, kls, sym) in enumerate(bloklar):
        if sym:
            o.append(f'<use href="#sym-{sym}" x="{bx + 15}" y="{y - 4}" width="90" height="60"/>')
            o.append(f'<text x="{bx + 60}" y="{y + 68}" text-anchor="middle" class="s-metin">{ad}</text>')
        else:
            o.append(f'<rect x="{bx}" y="{y}" width="120" height="70" rx="7" class="{kls}"/>')
            o.append(f'<text x="{bx + 60}" y="{y + 40}" text-anchor="middle" class="s-metin">{ad}</text>')
        o.append(f'<text x="{bx + 60}" y="{y + 92}" text-anchor="middle" class="s-mono2">{a1}</text>')
        o.append(f'<text x="{bx + 60}" y="{y + 107}" text-anchor="middle" class="s-kucuk">{a2}</text>')
        if i < len(bloklar) - 1:
            nx = bloklar[i + 1][0]
            o.append(f'<path d="M{bx + 120} {y + 35} H{nx - 2}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    # veri genişliği etiketleri (ok üstü)
    etiket = ["32 b", "32 b", "32 b", "2×(16+10) b", "26+26 b", "20 b dB", "16 b × k"]
    for i, et in enumerate(etiket):
        bx = bloklar[i][0] + 120
        nx = bloklar[i + 1][0]
        o.append(f'<text x="{(bx + nx) / 2:.0f}" y="{y + 28}" text-anchor="middle" class="s-kucuk s-vurgu">{et}</text>')
    # register'lar — tek sıra, açıklama kutunun altında
    ry = 250
    regs = [(290, "WIN_SEL", "0 dikd. · 1 Hann · 2 BH · 3 Kaiser", 360), (450, "FFT_SCALE_SCH", "kademe çifti başına 2 bit: 0x2AA", 510),
            (620, "FFT_LOG2N", "log2 N = 10", 510), (860, "FFT_THR", "eşik, dB (Q8.4)", 940)]
    for (rx, ad, acik, hx) in regs:
        o.append(f'<rect x="{rx}" y="{ry}" width="150" height="26" rx="4" class="blok-kontrol"/>')
        o.append(f'<text x="{rx + 75}" y="{ry + 17}" text-anchor="middle" class="s-mono">{ad}</text>')
        o.append(f'<text x="{rx + 75}" y="{ry + 42}" text-anchor="middle" class="s-kucuk s-yesil">{acik}</text>')
        o.append(f'<path d="M{hx} {ry} V{y + 72}" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    o.append(f'<text x="20" y="{ry + 17}" class="s-kucuk">PS (AXI-Lite) register\'ları →</text>')
    # zamanlama şeridi
    ty = 350
    o.append(f'<text x="20" y="{ty}" class="s-baslik">Zamanlama (300 MHz örnek saati, SSR yok)</text>')
    notlar = [
        "çerçeve N = 1024 örnek = 3.41 µs · %50 overlap → her 512 örnek (1.71 µs) yeni çerçeve → 586 k çerçeve/s",
        "pipelined çekirdek: sürekli akış, giriş hızı = çıkış hızı; gecikme ≈ N + ~150 saat ≈ 3.9 µs · burst çekirdek: 1024 giriş + ~N·log₂N/2 hesap saati, %50 overlap\'e yetişemez",
        "çıkış bant genişliği: 586 k × 1024 bin × 20 bit ≈ 12 Gbps → PS\'e ham spektrum değil tepe listesi / eşik üstü bin\'ler gider (Bölüm 23, 26)",
    ]
    for i, n in enumerate(notlar):
        o.append(f'<text x="20" y="{ty + 20 + i * 18}" class="s-metin2">{n}</text>')
    yaz("g-200-streaming-fft-akis.svg", o)


# =================================================================== g-201
def g_201():
    """Darbe–FFT penceresi hizalanma durumları: zaman çizelgeleri (sol) ve hesaplanmış spektrumlar (sağ)."""
    fs = FS_DDC
    L = int(PW * fs)                 # 300 örnek
    snr_s = 10.0                     # örnek başına SNR (dB)
    f0 = 32 * BIN                 # 9.375 MHz: hem N = 1024 (bin 32) hem N = 256 (bin 8) için bin merkezi
    g = prng(5)
    sigma = math.sqrt(10 ** (-snr_s / 10))
    W, H = 900, 560
    o = svg_bas("g201", W, H, "Darbe ile FFT çerçevesinin hizalanması. Sol sütun zaman çizelgeleri: (a) N = 1024 çerçeve (3.41 µs) 1 µs darbeyi içine alır ama doluluk yalnızca %29'dur, gürültü tüm çerçeveden toplanır → 5.3 dB SNR kaybı; (b) overlap'siz ardışık çerçevelerde darbe sınıra denk gelirse ikiye bölünür, %50 overlap'li ara çerçeve darbeyi bütün yakalar; (c) N = 256 çerçeve (0.85 µs) darbenin içinde kalır, SNR kaybı yok ama bin 1.17 MHz. Sağ sütun: aynı gürültülü darbenin hesaplanmış spektrumları — N = 1024'te tepe−taban 29 dB, N = 256'da 34 dB; bin genişliği 4 kat kabalaşır.")
    # --- zaman çizelgeleri
    tx0, tx1 = 50, 440
    tmin, tmax = 0.0, 4.0e-6
    darbe_bas = 1.2e-6
    def tpx(t):
        return px_of(t, tmin, tmax, tx0, tx1)
    def darbe(yb):
        o.append(f'<path d="M{tpx(0)} {yb} H{tpx(darbe_bas):.1f} V{yb - 26} H{tpx(darbe_bas + PW):.1f} V{yb} H{tpx(tmax)}" class="yol-analog" stroke="var(--accent)" stroke-width="2"/>')
        o.append(f'<rect x="{tpx(darbe_bas):.1f}" y="{yb - 26}" width="{tpx(darbe_bas + PW) - tpx(darbe_bas):.1f}" height="26" fill="var(--accent-soft)"/>')
    def cerceve(t0, T, yb, kls="var(--gold)", etiket=None, alpha=.35):
        o.append(f'<rect x="{tpx(t0):.1f}" y="{yb}" width="{tpx(t0 + T) - tpx(t0):.1f}" height="16" fill="{kls}" opacity="{alpha}" stroke="{kls}" stroke-width="1"/>')
        if etiket:
            o.append(f'<text x="{(tpx(t0) + tpx(t0 + T)) / 2:.1f}" y="{yb + 12}" text-anchor="middle" class="s-kucuk">{etiket}</text>')
    T1024, T256 = 1024 / fs, 256 / fs
    # (a)
    ya = 70
    o.append(f'<text x="{tx0}" y="{ya - 30}" class="s-baslik">(a) N = 1024 — çerçeve darbeden uzun</text>')
    darbe(ya)
    cerceve(darbe_bas + PW / 2 - T1024 / 2, T1024, ya + 6, etiket="çerçeve 3.41 µs")
    o.append(f'<text x="{tx0}" y="{ya + 44}" class="s-kucuk">darbe 300 / 1024 örnek = %29 doluluk → SNR kaybı 10·log10(1024/300) = 5.3 dB; bin 293 kHz</text>')
    # (b)
    yb = 205
    o.append(f'<text x="{tx0}" y="{yb - 30}" class="s-baslik">(b) çerçeve sınırı darbeyi böler — overlap kurtarır</text>')
    darbe(yb)
    for k in range(3):
        cerceve(k * T1024 - 1.6e-6, T1024, yb + 6, etiket=f"çerçeve {k}" if k else None, alpha=.25)
    cerceve(T1024 / 2 - 1.6e-6 + T1024, T1024, yb + 26, kls="var(--green)", etiket="%50 overlap çerçevesi: darbe bütün", alpha=.3)
    o.append(f'<text x="{tx0}" y="{yb + 60}" class="s-kucuk">overlap\'siz: 0.4 + 0.6 µs\'lik iki parça, iki çerçevede iki zayıf tepe (−8 ve −4.4 dB). %50 overlap: en kötü durumda bile bir çerçeve darbenin ≥ %75\'ini içerir.</text>')
    # (c)
    yc = 340
    o.append(f'<text x="{tx0}" y="{yc - 30}" class="s-baslik">(c) N = 256 — çerçeve darbenin içinde</text>')
    darbe(yc)
    for k in range(3):
        cerceve(darbe_bas - 0.15e-6 + k * T256 / 2, T256, yc + 6 + (k % 2) * 18, etiket="0.85 µs" if k == 1 else None, alpha=.3)
    o.append(f'<text x="{tx0}" y="{yc + 60}" class="s-kucuk">tam doluluk → SNR kaybı yok; ama bin = 300/256 = 1.17 MHz (4× kaba). Zaman–frekans takası: kısa darbe için ideal N ≈ darbe örnek sayısı (300).</text>')
    o.append(eksen(tx0, tx1, 414, 410, [0, 1e-6, 2e-6, 3e-6, 4e-6], [], tmin, tmax, 0, 1, lambda v: f"{v * 1e6:.0f} µs"))
    # --- spektrumlar (sağ)
    OFS = 600                         # tampon t = −2 µs'den başlar (çerçeve darbeden önce başlayabilsin)
    x_full = []
    for n in range(2048):
        t = (n - OFS) / fs
        v = cmath.exp(1j * TAU * f0 * t) if darbe_bas <= t < darbe_bas + PW else 0j
        x_full.append(v + complex(g(sigma / math.sqrt(2)), g(sigma / math.sqrt(2))))
    merkez = int((darbe_bas + PW / 2) * fs) + OFS
    durumlar = [("N = 1024 (çerçeve darbeyi kapsar)", 1024, merkez - 512),
                ("N = 256 (çerçeve darbenin içinde)", 256, merkez - 128)]
    for i, (ad, N, bas) in enumerate(durumlar):
        x0, x1, y1 = 520, 870, 40 + i * 185
        y0 = y1 + 120
        xmin, xmax, ymin, ymax = 0, 30, -50, 5
        seg = x_full[bas:bas + N]
        sp = spektrum_kompleks(seg, "rect")
        binw = fs / N
        xs = [(k - N / 2) * binw / 1e6 for k in range(N)]
        gor = [(xx, yy) for xx, yy in zip(xs, sp) if xmin <= xx <= xmax]
        gxs, gsp = [g_[0] for g_ in gor], [g_[1] for g_ in gor]
        o.append(f'<text x="{x0}" y="{y1 - 10}" class="s-baslik">{ad}</text>')
        o.append(eksen(x0, x1, y0, y1, [0, 10, 20, 30], [0, -20, -40], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        d = path_from(gxs, gsp, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        o.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-sinyal" opacity=".15"/>')
        o.append(f'<path d="{d}" stroke="var(--accent)" fill="none" stroke-width="1.2"/>')
        tepe = max(sp)
        # taban: tepe çevresi dışındaki bin'lerin güç ortalaması
        pk = sp.index(tepe)
        pn = [10 ** (sp[k] / 10) for k in range(N) if abs(k - pk) * binw > 6e6]   # tepe ±6 MHz dışı
        taban = 10 * math.log10(sum(pn) / len(pn))
        py_t = px_of(taban, ymin, ymax, y0, y1)
        o.append(f'<line x1="{x0}" y1="{py_t:.1f}" x2="{x1}" y2="{py_t:.1f}" class="yol-gurultu"/>')
        o.append(f'<text x="{x1 - 4}" y="{py_t - 4:.1f}" text-anchor="end" class="s-kucuk s-kirmizi">taban ort. {taban:.1f} dB</text>')
        o.append(f'<text x="{x0 + 6}" y="{y1 + 14}" class="s-kucuk">tepe {tepe:.1f} dB · Δ {tepe - taban:.1f} dB (teori {snr_s + 10 * math.log10(min(L, N) ** 2 / N):.1f}) · bin {binw / 1e6:.2f} MHz</text>')
        o.append(f'<text x="{x1}" y="{y0 + 26}" text-anchor="end" class="s-kucuk">frekans (MHz) · dB (tam ölçek CW = 0)</text>')
    o.append(f'<text x="520" y="430" class="s-metin2">Örnek başına SNR 10 dB, aynı gürültü gerçekleşmesi.</text>')
    o.append(f'<text x="520" y="448" class="s-metin2">tepe − taban = SNR_örnek + 10·log10(L²/N), L = çerçevedeki darbe örneği.</text>')
    o.append(f'<text x="520" y="466" class="s-metin2">N = L (300) en iyi: 10 + 24.8 = 34.8 dB. N = 1024: 29.4 dB (−5.3). N = 64: 28.1 dB.</text>')
    o.append(f'<text x="50" y="{H - 60}" class="s-metin2">Kural: çerçeve darbeden uzunsa fazla kısım yalnızca gürültü ekler (kayıp 10·log10(N/L)); kısaysa çözünürlük ve frekans doğruluğu düşer.</text>')
    o.append(f'<text x="50" y="{H - 40}" class="s-metin2">Bilinmeyen PW için pratik: %50 overlap + darbe FSM\'inin (Bölüm 26) verdiği başlangıç/bitiş ile sonradan çerçeve seçimi ya da iki paralel N.</text>')
    yaz("g-201-darbe-pencere-hizalama.svg", o)


# =================================================================== g-202
def g_202():
    """Spektrogram: referans darbe (CW, 1 µs) ve LFM varyantı (10 MHz) — STFT N = 128, adım 32, Hann; hücreler rect + opacity."""
    fs = FS_DDC
    N, hop = 128, 32
    T_top = 2.0e-6
    M = int(T_top * fs)              # 600 örnek
    bas = 0.5e-6
    f0 = 10e6
    g = prng(9)
    sigma = math.sqrt(10 ** (-25 / 10))
    fmin, fmax = -30e6, 30e6
    w = pencere("hann", N)
    s1 = sum(w)
    W, H = 900, 470
    o = svg_bas("g202", W, H, "Referans darbenin (solda, 1 µs CW, +10 MHz) ve LFM varyantının (sağda, 10 MHz süpürme) hesaplanmış spektrogramı: STFT N = 128 (bin 2.34 MHz, çerçeve 0.43 µs), adım 32 örnek (%75 overlap), Hann. Üstte darbe zarfı zaman ekseninde. CW darbe yatay bir çizgi olarak görünür (Hann ana lobu ≈ 2 bin genişliğinde); LFM darbe 10 MHz/µs eğimli çapraz bir çizgi çizer: 5 MHz'den 15 MHz'e. Darbe kenarlarında çerçevenin yalnızca bir kısmı dolu olduğu için çizgi soluklaşır ve genişler; koyuluk dB seviyesini gösterir (−50…0 dB).")
    hucre = 0
    for i, (mop, ad) in enumerate([("yok", "Referans darbe: 1 µs CW, +10 MHz"), ("lfm", "Varyant B: 1 µs LFM, 10 MHz süpürme")]):
        x = []
        for n in range(M):
            t = n / fs
            if bas <= t < bas + PW:
                tt = t - bas
                faz = TAU * f0 * t
                if mop == "lfm":
                    faz += math.pi * (CHIRP / PW) * (tt - PW / 2) ** 2 - math.pi * CHIRP / PW * (PW / 2) ** 2
                v = cmath.exp(1j * faz)
            else:
                v = 0j
            x.append(v + complex(g(sigma / math.sqrt(2)), g(sigma / math.sqrt(2))))
        px0, px1 = 60 + i * 420, 60 + i * 420 + 360
        # zarf şeridi
        zy0, zy1 = 70, 46
        o.append(f'<text x="{px0}" y="30" class="s-baslik">{ad}</text>')
        o.append(f'<rect x="{px0}" y="{zy1}" width="{px1 - px0}" height="{zy0 - zy1}" class="eksen"/>')
        o.append(f'<path d="M{px0} {zy0 - 2} H{px_of(bas, 0, T_top, px0, px1):.1f} V{zy1 + 3} H{px_of(bas + PW, 0, T_top, px0, px1):.1f} V{zy0 - 2} H{px1}" class="yol-sayisal"/>')
        o.append(f'<text x="{px1 - 4}" y="{zy1 + 12}" text-anchor="end" class="s-kucuk">zarf |x(t)|</text>')
        # spektrogram alanı
        sy1, sy0 = 84, 384
        o.append(f'<rect x="{px0}" y="{sy1}" width="{px1 - px0}" height="{sy0 - sy1}" fill="var(--dia-panel)" class="eksen"/>')
        cerceveler = list(range(0, M - N + 1, hop))
        nf = len(cerceveler)
        cw = (px1 - px0) / nf
        kmin = int(math.ceil(fmin / fs * N))
        kmax = int(math.floor(fmax / fs * N))
        ch = (sy0 - sy1) / (kmax - kmin + 1)
        for j, b0 in enumerate(cerceveler):
            X = fft([x[b0 + k] * w[k] for k in range(N)])
            for k in range(kmin, kmax + 1):
                db = 20 * math.log10(max(abs(X[k % N]) / s1, 1e-9))
                if db < -50:
                    continue
                a = min(1.0, (db + 50) / 50)
                cx = px0 + j * cw
                cy = sy0 - (k - kmin + 1) * ch
                o.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw + 0.4:.1f}" height="{ch + 0.4:.1f}" fill="var(--accent)" opacity="{a:.2f}"/>')
                hucre += 1
        # eksenler
        for fv in (-30e6, -20e6, -10e6, 0, 10e6, 20e6, 30e6):
            py = sy0 - (fv / fs * N - kmin + 0.5) * ch
            o.append(f'<line x1="{px0 - 4}" y1="{py:.1f}" x2="{px0}" y2="{py:.1f}" class="eksen"/><text x="{px0 - 7}" y="{py + 4:.1f}" text-anchor="end" class="s-mono2">{fv / 1e6:+.0f}</text>')
        for tv in (0, 0.5e-6, 1e-6, 1.5e-6, 2e-6):
            # çerçeve merkez zamanı → sütun
            px = px0 + ((tv * fs - N / 2) / hop + 0.5) * cw
            px = max(px0, min(px1, px))
            o.append(f'<line x1="{px:.1f}" y1="{sy0}" x2="{px:.1f}" y2="{sy0 + 4}" class="eksen"/><text x="{px:.1f}" y="{sy0 + 16}" text-anchor="middle" class="s-mono2">{tv * 1e6:.1f}</text>')
        o.append(f'<text x="{(px0 + px1) / 2:.0f}" y="{sy0 + 32}" text-anchor="middle" class="s-kucuk">çerçeve merkezi zamanı (µs) · sütun = 32 örnek adım (107 ns)</text>')
        o.append(f'<text x="{px0 - 44}" y="{(sy0 + sy1) / 2:.0f}" text-anchor="middle" class="s-kucuk" transform="rotate(-90 {px0 - 44} {(sy0 + sy1) / 2:.0f})">frekans (MHz) · bin 2.34 MHz</text>')
        if mop == "lfm":
            o.append(f'<text x="{px0 + 8}" y="{sy1 + 16}" class="s-kucuk s-vurgu">eğim = 10 MHz / 1 µs — anlık frekans zamanla artar</text>')
        else:
            o.append(f'<text x="{px0 + 8}" y="{sy1 + 16}" class="s-kucuk s-vurgu">yatay çizgi: frekans sabit, genişlik ≈ Hann ana lobu (2 bin)</text>')
    o.append(f'<text x="60" y="{H - 30}" class="s-metin2">Koyuluk: −50 dB (saydam) … 0 dB (tam mavi), tam ölçek CW\'ye göre. Kenarlarda soluklaşma: çerçeve darbeyi kısmen içeriyor (g-201). Gürültü −25 dB/örnek.</text>')
    o.append(f'<text x="60" y="{H - 12}" class="s-kucuk">Aynı darbeye N = 1024 ile bakılsaydı tek sütun olurdu: zaman bilgisi kaybolur, frekans 293 kHz\'e incelir; N = 32 ile bin 9.4 MHz olur, LFM eğimi seçilemez.</text>')
    yaz("g-202-spektrogram.svg", o)
    print(f"    (g-202 hücre sayısı: {hucre})")


URETICILER = {"g-180": g_180, "g-181": g_181, "g-182": g_182, "g-190": g_190, "g-191": g_191,
              "g-200": g_200, "g-201": g_201, "g-202": g_202}


def main():
    secim = sys.argv[1:] or list(URETICILER)
    for ad in secim:
        if ad not in URETICILER:
            print(f"  ? bilinmeyen: {ad}")
            continue
        URETICILER[ad]()
    return 0



# =================================================================== g-192
def g_192():
    """Overlap'li Hann pencerelerinin toplamı + FPGA pencere çarpımı (simetrik ROM)."""
    W, H = 900, 330
    o = svg_bas("g192", W, H, "Solda %50 overlap ile dizilmiş ardışık Hann pencereleri ve toplamları: toplam zaman boyunca sabit 1'dir; overlap'siz dizilişte çerçeve sınırlarında ağırlık sıfıra düşer. Sağda FPGA pencere çarpımı bloğu: örnek sayacı, N/2'de yön değiştiren simetrik adres üreteci, WIN_SEL ile seçilen katsayı ROM'u (512 × 16 bit), tek DSP çarpıcı; I/Q örnek girer, pencerelenmiş I/Q FFT çekirdeğine gider.")
    N = 256
    x0, x1, y0, y1 = 50, 440, 200, 40
    tmin, tmax = 0, 3 * N
    o.append(f'<text x="{x0}" y="{y1 - 14}" class="s-baslik">Hann + %50 overlap: pencerelerin toplamı sabit</text>')
    o.append(eksen(x0, x1, y0, y1, [0, N, 2 * N, 3 * N], [0, 0.5, 1], tmin, tmax, -0.05, 1.25, lambda v: f"{v // N * 512}", lambda v: f"{v:g}"))
    toplam = [0.0] * (3 * N + 1)
    for s in range(-1, 6):
        bas = s * N // 2
        xs, ys = [], []
        for n in range(N + 1):
            t = bas + n
            if t < tmin or t > tmax:
                continue
            v = 0.5 - 0.5 * math.cos(TAU * n / N)
            xs.append(t)
            ys.append(v)
            toplam[t] += v
        if xs:
            o.append(f'<path d="{path_from(xs, ys, x0, x1, y0, y1, tmin, tmax, -0.05, 1.25)}" stroke="var(--gold)" fill="none" stroke-width="1.4" opacity=".9"/>')
    # overlap'siz: yalnızca çift pencereler (gri kesikli)
    for s in range(0, 3):
        bas = s * N
        xs = list(range(bas, bas + N + 1))
        ys = [0.5 - 0.5 * math.cos(TAU * (t - bas) / N) for t in xs]
        o.append(f'<path d="{path_from(xs, ys, x0, x1, y0, y1, tmin, tmax, -0.05, 1.25)}" class="yol-saat" stroke-width="1"/>')
    xs = list(range(N // 2, 3 * N - N // 2 + 1))
    ys = [toplam[t] for t in xs]
    o.append(f'<path d="{path_from(xs, ys, x0, x1, y0, y1, tmin, tmax, -0.05, 1.25)}" stroke="var(--accent)" fill="none" stroke-width="2.2"/>')
    o.append(f'<text x="{x0 + 8}" y="{y1 + 16}" class="s-kucuk s-vurgu">toplam = 1 (w[n] + w[n + N/2] = 1)</text>')
    o.append(f'<text x="{x0 + 8}" y="{y0 - 8}" class="s-kucuk">gri kesikli: overlap\'siz — sınırda ağırlık 0</text>')
    o.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">örnek (N = 1024, adım 512 = 1.71 µs)</text>')
    o.append(f'<text x="{x0}" y="{y0 + 60}" class="s-metin2">Blackman-Harris gibi dar pencereler için eşdeğer düzlük %75 overlap ister (adım N/4).</text>')
    o.append(f'<text x="{x0}" y="{y0 + 80}" class="s-metin2">Bedel: çerçeve hızı ve FFT iş yükü 2× (%50) ya da 4× (%75).</text>')
    # --- sağ: ROM blok şeması
    bx = 500
    o.append(f'<text x="{bx}" y="{y1 - 14}" class="s-baslik">FPGA: simetrik katsayı ROM\'u ve tek çarpıcı</text>')
    o.append(f'<rect x="{bx}" y="50" width="110" height="44" rx="6" class="blok"/><text x="{bx + 55}" y="68" text-anchor="middle" class="s-metin">örnek sayacı</text><text x="{bx + 55}" y="84" text-anchor="middle" class="s-mono2">n = 0 … N−1</text>')
    o.append(f'<path d="M{bx + 110} 72 H{bx + 150}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<rect x="{bx + 152}" y="50" width="120" height="44" rx="6" class="blok"/><text x="{bx + 212}" y="68" text-anchor="middle" class="s-metin">adres = n &lt; N/2</text><text x="{bx + 212}" y="84" text-anchor="middle" class="s-mono2">? n : N−1−n</text>')
    o.append(f'<path d="M{bx + 212} 94 V128" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<rect x="{bx + 142}" y="130" width="140" height="56" rx="6" class="blok-aktif"/><text x="{bx + 212}" y="150" text-anchor="middle" class="s-metin">katsayı ROM</text><text x="{bx + 212}" y="166" text-anchor="middle" class="s-mono2">4 × 512 × 16 bit</text><text x="{bx + 212}" y="180" text-anchor="middle" class="s-kucuk">dikd. · Hann · BH · Kaiser</text>')
    o.append(f'<rect x="{bx}" y="140" width="100" height="26" rx="4" class="blok-kontrol"/><text x="{bx + 50}" y="157" text-anchor="middle" class="s-mono">WIN_SEL[1:0]</text>')
    o.append(f'<path d="M{bx + 100} 153 H{bx + 140}" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    o.append(f'<text x="{bx + 104}" y="147" class="s-kucuk s-yesil">üst adres</text>')
    o.append(f'<path d="M{bx + 212} 186 V218" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<text x="{bx + 218}" y="208" class="s-kucuk">w[n], Q1.15</text>')
    o.append(f'<circle cx="{bx + 212}" cy="238" r="18" class="blok"/><text x="{bx + 212}" y="243" text-anchor="middle" class="s-metin" style="font-weight:700">×</text>')
    o.append(f'<path d="M{bx} 238 H{bx + 192}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<text x="{bx}" y="230" class="s-kucuk">DDC I/Q 16+16 bit, 300 MSPS</text>')
    o.append(f'<path d="M{bx + 230} 238 H{bx + 300}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    o.append(f'<use href="#sym-fft" x="{bx + 302}" y="218" width="60" height="40"/>')
    o.append(f'<text x="{bx + 332}" y="272" text-anchor="middle" class="s-kucuk">FFT çekirdeği</text>')
    o.append(f'<text x="{bx}" y="292" class="s-kucuk">1 DSP (I/Q zaman paylaşımlı) ya da 2 DSP; gecikme ≈ 5 saat.</text>')
    o.append(f'<text x="{bx}" y="308" class="s-kucuk">CG 0.5 → 1 bit headroom; ∑w = 512 ölçekleme sabiti PS\'e verilir.</text>')
    yaz("g-192-overlap-rom.svg", o)


URETICILER["g-192"] = g_192


if __name__ == "__main__":
    sys.exit(main())
