#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k4.py — Kısım IV/V hesaplanmış şekilleri (Bölüm 12, 15, 16, 17)

gen_figures.py'deki yardımcıları (fft, pencere, spektrum_dbfs, seyrelt,
path_from, eksen, S) yeniden kullanır; yalnızca stdlib.

  python build/gen_figures_k4.py            # hepsi
  python build/gen_figures_k4.py g-150      # yalnızca biri

Üretilenler:
  g-122  wrap vs saturate dalga şekli + spektrum          (Bölüm 12)
  g-132  bit-exact fark desenleri (sentetik)              (Bölüm 13)
  g-152  fs/4 hilesi: x, I, Q örnekleri                    (Bölüm 15)
  g-150  DDC'nin dört karelik spektrum hikâyesi           (Bölüm 15)
  g-162  CIC R=4,N=4 yanıtı + kompanzasyon FIR             (Bölüm 16)
  g-163  çok kademeli decimation zinciri, kademe spektrumları (Bölüm 16)
  g-171  kanal yanıtları: kritik vs 2× aşırı örnekleme     (Bölüm 17)
  g-172  rabbit ear: zaman–kanal görünümü                  (Bölüm 17)

dsp-core.js eşdeğerleri: fir_tasarla ≈ DSP.firTasarla (Kaiser, sum=1),
halfband ≈ DSP.halfband, cic_yanit ≈ DSP.cicYanit, sabit_nokta ≈ DSP.sabitNokta.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_figures import S, SVG, TAU, spektrum_dbfs, path_from, eksen  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FS = S["adc"]["fs_hz"]
F_NCO = S["ddc"]["nco_hz"]
PW = S["sinyal"]["pw_s"]
RISE = S["sinyal"]["rise_time_ns"] * 1e-9


# ------------------------------------------------------------------ DSP eşdeğerleri
def _i0(x):
    s, t, k = 1.0, 1.0, 1
    while True:
        t *= (x / (2 * k)) ** 2
        s += t
        k += 1
        if t < 1e-12 * s or k > 200:
            return s


def kaiser(N, beta):
    i0b = _i0(beta)
    return [_i0(beta * math.sqrt(max(0.0, 1 - (2 * k / (N - 1) - 1) ** 2))) / i0b for k in range(N)]


def fir_tasarla(fc, fs, tap, beta=8.0):
    """Pencereli sinc alçak geçiren (DSP.firTasarla eşdeğeri, Kaiser)."""
    w = kaiser(tap, beta)
    m = (tap - 1) / 2
    f = fc / fs
    h = []
    for k in range(tap):
        x = k - m
        h.append((2 * f if x == 0 else math.sin(TAU * f * x) / (math.pi * x)) * w[k])
    s = sum(h)
    return [v / s for v in h]


def halfband(tap=23, beta=6.0):
    h = fir_tasarla(0.25, 1.0, tap, beta)
    m = (tap - 1) // 2
    h = [0.0 if (k != m and (k - m) % 2 == 0) else v for k, v in enumerate(h)]
    s = sum(h)
    return [v / s for v in h]


def fir_uygula(x, h):
    n, L = len(x), len(h)
    out = [0j] * n
    for k in range(n):
        s = 0
        for j in range(min(L, k + 1)):
            s += h[j] * x[k - j]
        out[k] = s
    return out


def fir_yanit_db(h, f_list, fs):
    out = []
    for f in f_list:
        w = TAU * f / fs
        re = sum(h[k] * math.cos(w * k) for k in range(len(h)))
        im = -sum(h[k] * math.sin(w * k) for k in range(len(h)))
        out.append(20 * math.log10(max(math.hypot(re, im), 1e-15)))
    return out


def cic_yanit_db(R, N, f, fs):
    x = f / fs
    if x == 0:
        return 0.0
    g = abs(math.sin(math.pi * R * x) / math.sin(math.pi * x)) / R
    return 20 * math.log10(max(g, 1e-15) ** N)


def cic_uygula(x, R, N):
    """N integratör → ↓R → N comb (kayan nokta, kazanç R^N geri alınır)."""
    y = list(x)
    for _ in range(N):
        acc = 0
        for k in range(len(y)):
            acc += y[k]
            y[k] = acc
    y = y[::R]
    for _ in range(N):
        prev = 0
        for k in range(len(y)):
            cur = y[k]
            y[k] = cur - prev
            prev = cur
    g = R ** N
    return [v / g for v in y]


def decimate(x, M):
    return x[::M]


def sabit_nokta(x, bit, mod="round", tasma="sat"):
    q = 2 ** (bit - 1)
    out = []
    for v in x:
        c = math.floor(v * q) if mod == "trunc" else math.floor(v * q + 0.5)
        if c > q - 1 or c < -q:
            if tasma == "wrap":
                c = ((c + q) % (2 * q)) - q
            else:
                c = max(-q, min(q - 1, c))
        out.append(c / q)
    return out


class LCG:
    def __init__(self, seed):
        self.s = seed

    def u(self):
        self.s = (self.s * 1103515245 + 12345) % 2 ** 31
        return self.s / 2 ** 31

    def gauss(self, sigma):
        u1 = max(self.u(), 1e-12)
        u2 = self.u()
        return sigma * math.sqrt(-2 * math.log(u1)) * math.cos(TAU * u2)


def darbe_zarfi(n, fs, pw, rise, t0):
    z = []
    for k in range(n):
        t = k / fs - t0
        v = 0.0
        if 0 <= t < pw:
            v = 1.0
            if rise > 0 and t < rise:
                v = 0.5 - 0.5 * math.cos(math.pi * t / rise)
            elif rise > 0 and t > pw - rise:
                v = 0.5 - 0.5 * math.cos(math.pi * (pw - t) / rise)
        z.append(v)
    return z


def guc_db(x):
    return 10 * math.log10(max(sum(abs(v) ** 2 for v in x) / len(x), 1e-30))


def spektrum_kompleks(x):
    return spektrum_dbfs(x, "blackman-harris")


def gurultu_tabani_db(sp, disla=()):
    """Spektrumun medyanı (dBFS/bin) — tepe ve verilen aralıklar dışlanır."""
    vals = sorted(v for k, v in enumerate(sp) if not any(a <= k <= b for a, b in disla))
    return vals[len(vals) // 2]


def ortak_sinyal(n=8192, seed=17, noise_sigma=1e-3, genlik=0.5):
    """Referans senaryo: 600 MHz'e katlanmış 1 µs darbe (−6 dBFS) + gürültü, reel, 2400 MSPS."""
    rnd = LCG(seed)
    z = darbe_zarfi(n, FS, PW, RISE, 0.9e-6)
    x = []
    for k in range(n):
        x.append(genlik * z[k] * math.cos(TAU * S["adc"]["alias_hz"] * k / FS + 0.3) + rnd.gauss(noise_sigma))
    return x


def mix(x, f, fs, isaret=-1):
    return [x[k] * complex(math.cos(isaret * TAU * f * k / fs), math.sin(isaret * TAU * f * k / fs)) for k in range(len(x))]


# ------------------------------------------------------------------ SVG yardımcıları
def svg_bas(gid, W, H, title):
    return [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-{gid}">',
            f'<title id="t-{gid}">{title}</title>']


def spektrum_paneli(out, sp, fs_hz, x0, x1, y0, y1, ymin, ymax, xt, yt, baslik, alt="", ek=None):
    n = len(sp)
    xs = [(k - n / 2) * fs_hz / n / 1e6 for k in range(n)]
    xmin, xmax = -fs_hz / 2e6, fs_hz / 2e6
    out.append(f'<text x="{x0}" y="{y1 - 8}" class="s-baslik">{baslik}</text>')
    out.append(eksen(x0, x1, y0, y1, xt, yt, xmin, xmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:d}"))
    d = path_from(xs, sp, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-gurultu" opacity=".35"/>')
    out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.1"/>')
    if alt:
        out.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">{alt}</text>')
    if ek:
        ek(xmin, xmax, ymin, ymax)


def px_of(v, x0, x1, xmin, xmax):
    return x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)


def py_of(v, y0, y1, ymin, ymax):
    return y0 - (max(ymin, min(ymax, v)) - ymin) / (ymax - ymin) * (y0 - y1)


def yaz(path, out, ad):
    (SVG / path).write_text("\n".join(out) + "\n</svg>", encoding="utf-8")
    print(f"  ✓ {path}  {ad}")


# ------------------------------------------------------------------ g-122
def g_122():
    """Wrap vs saturate: +2.5 dBFS ton, 16 bit Q1.15. Zaman + spektrum."""
    bit = 16
    fs = S["ddc"]["cikis_fs_msps"] * 1e6
    n = 4096
    kbin = 203
    A = 10 ** (2.5 / 20)
    x = [A * math.cos(TAU * kbin * k / n) for k in range(n)]
    sat = sabit_nokta(x, bit, "round", "sat")
    wrp = sabit_nokta(x, bit, "round", "wrap")
    sp_x = spektrum_kompleks([complex(v, 0) for v in x])
    sp_s = spektrum_kompleks([complex(v, 0) for v in sat])
    sp_w = spektrum_kompleks([complex(v, 0) for v in wrp])
    # metrikler
    def metrik(sp):
        pk = max(range(n // 2, n), key=lambda k: sp[k])
        spur = max(sp[k] for k in range(n // 2 + 3, n) if abs(k - pk) > 6)
        taban = sorted(sp[k] for k in range(n // 2 + 3, n) if abs(k - pk) > 6)
        return pk, spur, taban[len(taban) // 2]
    ms, mw = metrik(sp_s), metrik(sp_w)
    print(f"    g-122: sat en büyük spur {ms[1]:.1f} dBFS (tepe {sp_s[ms[0]]:.1f}), medyan taban {ms[2]:.1f}; "
          f"wrap spur {mw[1]:.1f}, medyan taban {mw[2]:.1f}")
    W, H = 900, 330
    out = svg_bas("g122", W, H, "Wrap ve saturation karşılaştırması (hesaplanmış): +2.5 dBFS'lik bir tonun 16 bit Q1.15'e sığdırılması. "
                  "Solda zaman: saturation tepeleri düz keser, wrap tepeleri tam ölçek negatife fırlatır. Sağda spektrum: saturation tek "
                  "harmonikler üretir, wrap tüm bandı geniş bantlı bozulma ile doldurur ve tespit eşiğini her yerde aşar.")
    # --- zaman paneli
    x0, x1, y0, y1 = 50, 430, 270, 40
    n_t = 90
    per = n / kbin
    xs = list(range(n_t))
    xmin, xmax, ymin, ymax = 0, n_t - 1, -1.6, 1.6
    out.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">Zaman: +2.5 dBFS ton (tepe {A:.2f}), 16 bit</text>')
    out.append(eksen(x0, x1, y0, y1, [0, 20, 40, 60, 80], [-1.5, -1, -0.5, 0, 0.5, 1, 1.5], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:g}"))
    for lv, cls in ((1.0, "s-kirmizi"), (-1.0, "s-kirmizi")):
        py = py_of(lv, y0, y1, ymin, ymax)
        out.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="var(--red)" stroke-dasharray="4 4" opacity=".7"/>')
    out.append(f'<text x="{x1 - 4}" y="{py_of(1.0, y0, y1, ymin, ymax) - 4:.1f}" text-anchor="end" class="s-kucuk s-kirmizi">tam ölçek ±1</text>')
    d = path_from(xs, x[:n_t], x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.2" stroke-dasharray="2 3"/>')
    d = path_from(xs, sat[:n_t], x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    out.append(f'<path d="{d}" fill="none" stroke="var(--gold)" stroke-width="2"/>')
    d = path_from(xs, wrp[:n_t], x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    out.append(f'<path d="{d}" fill="none" stroke="var(--red)" stroke-width="1.6"/>')
    out.append(f'<text x="{x0 + 6}" y="{y0 - 8}" class="s-kucuk"><tspan class="s-vurgu">ideal (kesikli)</tspan> · <tspan class="s-altin">saturation</tspan> · <tspan class="s-kirmizi">wrap</tspan></text>')
    out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">örnek n</text>')
    # --- spektrum paneli (reel: sağ yarı)
    x0, x1 = 500, 880
    xmin, xmax, ymin, ymax = 0, fs / 2e6, -120, 10
    out.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">Spektrum (dBFS, N = 4096, Blackman-Harris)</text>')
    out.append(eksen(x0, x1, y0, y1, [0, 30, 60, 90, 120, 150], [0, -30, -60, -90, -120], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    xs_f = [(k - n / 2) * fs / n / 1e6 for k in range(n // 2, n)]
    for sp, cls, w in ((sp_w, "var(--red)", 1.0), (sp_s, "var(--gold)", 1.2), (sp_x, "var(--accent)", 1.2)):
        d = path_from(xs_f, sp[n // 2:], x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        if sp is sp_w:
            out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" fill="var(--red)" opacity=".15"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{cls}" stroke-width="{w}"/>')
    esik = -70
    py = py_of(esik, y0, y1, ymin, ymax)
    out.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="var(--ink-2)" stroke-dasharray="5 4"/>')
    out.append(f'<text x="{x1 - 4}" y="{py - 4:.1f}" text-anchor="end" class="s-kucuk">tespit eşiği (örnek) {esik} dBFS</text>')
    out.append(f'<text x="{x0 + 6}" y="{y1 + 14}" class="s-kucuk s-altin">saturation: tek harmonikler, en büyük {ms[1]:.0f} dBFS</text>')
    out.append(f'<text x="{x0 + 6}" y="{y1 + 28}" class="s-kucuk s-kirmizi">wrap: geniş bant, taban ≈ {mw[2]:.0f} dBFS</text>')
    out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">frekans (MHz) · fs = {fs / 1e6:g} MSPS</text>')
    yaz("g-122-wrap-vs-saturate.svg", out, "wrap vs saturate")


# ------------------------------------------------------------------ g-150
def g_150():
    """DDC dört kare: ADC çıkışı → mixing → filtre → decimation."""
    n = 8192
    x = ortak_sinyal(n)
    y = mix(x, F_NCO, FS, -1)
    h = fir_tasarla(150e6, FS, 127, 8.0)
    f = fir_uygula(y, h)
    d = decimate(f, 8)
    sp1 = spektrum_kompleks([complex(v, 0) for v in x])
    sp2 = spektrum_kompleks(y)
    sp3 = spektrum_kompleks(f)
    sp4 = spektrum_kompleks(d)
    # güç metrikleri (gürültü: sinyal olmayan pencerede zaman domeninden)
    def gur(x_, fs_, bant):
        # sinyalsiz kısım: t < 0.8 µs
        m = int(0.8e-6 * fs_)
        return guc_db(x_[:m])
    g1, g2, g3, g4 = gur(x, FS, 1200), gur(y, FS, 2400), gur(f, FS, 300), gur(d, FS / 8, 300)
    # sinyal tepe (darbe ortası)
    def sig(x_, fs_):
        a, b = int(1.2e-6 * fs_), int(1.6e-6 * fs_)
        return guc_db(x_[a:b])
    s1, s3 = sig(x, FS), sig(f, FS)
    print(f"    g-150: gürültü gücü: ADC {g1:.1f}, mix {g2:.1f}, filtre {g3:.1f}, dec {g4:.1f} dBFS; sinyal {s1:.1f} → {s3:.1f} dBFS; SNR kazancı {(s3 - g3) - (s1 - g1):.1f} dB")
    W = 900
    ph, gap, top = 130, 52, 40
    H = top + 4 * (ph + gap) + 10
    out = svg_bas("g150", W, H, "DDC'nin dört karelik spektrum hikâyesi (hesaplanmış, referans senaryo): (1) ADC çıkışı reel, ±600 MHz'de simetrik darbe spektrumu ve gürültü; "
                  "(2) NCO −600 MHz ile çarpım sonrası istenen kopya 0 Hz'de, toplam frekans kopyası −1200 MHz'de; (3) ±150 MHz alçak geçiren filtre sonrası image ve bant dışı gürültü atılmış; "
                  "(4) 8'e decimation sonrası fs = 300 MSPS, eksen ±150 MHz, aynı spektrum.")
    x0, x1 = 60, W - 20
    ymin, ymax = -130, 0
    yt = [0, -40, -80, -120]
    paneller = [
        (sp1, FS, "(1) ADC çıkışı — reel, fs = 2400 MSPS", [-1200, -800, -400, 0, 400, 800, 1200], f"gürültü gücü {g1:.0f} dBFS · sinyal ±600 MHz"),
        (sp2, FS, "(2) × e^(−j2π·600 MHz·n/fs) — kompleks, 2400 MSPS", [-1200, -800, -400, 0, 400, 800, 1200], f"gürültü gücü {g2:.0f} dBFS (değişmedi) · sinyal 0 MHz · image −1200 MHz"),
        (sp3, FS, "(3) ±150 MHz alçak geçiren filtre sonrası — 2400 MSPS", [-1200, -800, -400, 0, 400, 800, 1200], f"gürültü gücü {g3:.0f} dBFS (−{g2 - g3:.0f} dB) · sinyal {s3 - s1:+.0f} dB (image yarısı gitti)"),
        (sp4, FS / 8, "(4) ↓8 sonrası — kompleks, fs = 300 MSPS", [-150, -100, -50, 0, 50, 100, 150], f"gürültü gücü {g4:.0f} dBFS · yeni Nyquist ±150 MHz · SNR kazancı {(s3 - g3) - (s1 - g1):.0f} dB"),
    ]
    for i, (sp, fs_, bas, xt, alt) in enumerate(paneller):
        y1 = top + i * (ph + gap)
        y0 = y1 + ph
        def ek(xmin, xmax, ymin_, ymax_, i=i, y0=y0, y1=y1):
            if i == 1:
                px = px_of(-1200 + 8, x0, x1, xmin, xmax)
                out.append(f'<path d="M{px + 30:.1f} {y1 + 30} L{px + 6:.1f} {y1 + 14}" class="yol-gurultu" marker-end="url(#ok-gurultu)"/>')
                out.append(f'<text x="{px + 34:.1f}" y="{y1 + 40}" class="s-kucuk s-kirmizi">image (toplam frekans)</text>')
                px = px_of(0, x0, x1, xmin, xmax)
                out.append(f'<text x="{px + 8:.1f}" y="{y1 + 16}" class="s-kucuk s-vurgu">istenen (fark frekansı)</text>')
            if i == 2:
                # filtre yanıtı altın kesikli
                fl = [(k - 400) * fs_ / 800 for k in range(801)]
                hr = fir_yanit_db(h, [abs(v) for v in fl], fs_)
                d_ = path_from([v / 1e6 for v in fl], hr, x0, x1, y0, y1, xmin, xmax, ymin_, ymax_)
                out.append(f'<path d="{d_}" class="spk-filtre"/>')
                out.append(f'<text x="{px_of(300, x0, x1, xmin, xmax):.1f}" y="{y1 + 16}" class="s-kucuk s-altin">filtre yanıtı ±150 MHz</text>')
            if i == 0:
                px = px_of(600, x0, x1, xmin, xmax)
                out.append(f'<text x="{px + 8:.1f}" y="{y1 + 16}" class="s-kucuk s-vurgu">+600 MHz</text>')
                px = px_of(-600, x0, x1, xmin, xmax)
                out.append(f'<text x="{px - 8:.1f}" y="{y1 + 16}" text-anchor="end" class="s-kucuk s-vurgu">−600 MHz (ayna)</text>')
        spektrum_paneli(out, sp, fs_, x0, x1, y0, y1, ymin, ymax, xt, yt, bas, "", ek)
        out.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">{alt}</text>')
        out.append(f'<text x="{x0}" y="{y0 + 28}" class="s-kucuk">MHz · dBFS</text>')
    yaz("g-150-ddc-dort-kare.svg", out, "DDC dört kare")


# ------------------------------------------------------------------ kompanzasyon FIR (LS)
def komp_fir_tasarla(tap=31, fs=600e6, R=4, N=4, fs_in=2400e6, fp=150e6, fst=210e6, w_pass=10.0):
    """En küçük kareler: geçirme bandında 1/CIC, durdurma bandında 0; simetrik, lineer faz."""
    m = (tap - 1) // 2
    # H(f) = a0 + 2 Σ a_k cos(2π f k / fs)  (k = 1..m); a_k = h[m±k]
    grid = []
    for i in range(0, 601):
        f = i / 600 * fs / 2
        if f <= fp:
            grid.append((f, 10 ** (-cic_yanit_db(R, N, f, fs_in) / 20), w_pass))
        elif f >= fst:
            grid.append((f, 0.0, 1.0))
    n = m + 1
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for f, d, w in grid:
        row = [1.0] + [2 * math.cos(TAU * f * k / fs) for k in range(1, n)]
        for i in range(n):
            b[i] += w * row[i] * d
            for j in range(n):
                A[i][j] += w * row[i] * row[j]
    # Gauss eliminasyonu
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(A[r][i]))
        A[i], A[p] = A[p], A[i]
        b[i], b[p] = b[p], b[i]
        for r in range(i + 1, n):
            fct = A[r][i] / A[i][i]
            for c in range(i, n):
                A[r][c] -= fct * A[i][c]
            b[r] -= fct * b[i]
    a = [0.0] * n
    for i in range(n - 1, -1, -1):
        a[i] = (b[i] - sum(A[i][j] * a[j] for j in range(i + 1, n))) / A[i][i]
    h = [0.0] * tap
    h[m] = a[0]
    for k in range(1, n):
        h[m + k] = a[k]
        h[m - k] = a[k]
    return h


# ------------------------------------------------------------------ g-162
def g_162():
    R, N = 4, 4
    fs_in = FS
    fs_out = fs_in / R
    hk = komp_fir_tasarla()
    print("    g-162: komp FIR ∑|h| = %.3f, ∑h = %.3f" % (sum(abs(v) for v in hk), sum(hk)))
    # sol panel
    W, H = 900, 340
    out = svg_bas("g162", W, H, "CIC R=4, N=4 frekans yanıtı (hesaplanmış, fs_in = 2400 MSPS): solda 0–1200 MHz sinc⁴ yanıtı, 600 ve 1200 MHz'de sıfırlar, "
                  "↓4 sonrası ±150 MHz'e katlanacak alias bantları 450–750 ve 1050–1200 MHz kırmızı taralı, en zayıf bastırma 450 MHz'de −40 dB; "
                  "sağda 0–150 MHz geçirme bandı büyüteci: CIC droop'u 150 MHz'de −3.4 dB, 31 tap kompanzasyon FIR'ının ters-sinc yanıtı ve toplamın ±0.1 dB düzlüğü.")
    x0, x1, y0, y1 = 50, 520, 280, 40
    xmin, xmax, ymin, ymax = 0, 1200, -110, 5
    out.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">CIC R = 4, N = 4 — 0 … fs/2 (2400 MSPS)</text>')
    out.append(eksen(x0, x1, y0, y1, [0, 150, 300, 450, 600, 750, 900, 1050, 1200], [0, -20, -40, -60, -80, -100], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    for a, b in ((450, 750), (1050, 1200)):
        out.append(f'<rect x="{px_of(a, x0, x1, xmin, xmax):.1f}" y="{y1}" width="{px_of(b, x0, x1, xmin, xmax) - px_of(a, x0, x1, xmin, xmax):.1f}" height="{y0 - y1}" fill="var(--red)" opacity=".13"/>')
    out.append(f'<rect x="{px_of(0, x0, x1, xmin, xmax):.1f}" y="{y1}" width="{px_of(150, x0, x1, xmin, xmax) - x0:.1f}" height="{y0 - y1}" fill="var(--accent)" opacity=".10"/>')
    fl = [k * 1200 / 800 for k in range(801)]
    cic = [cic_yanit_db(R, N, f * 1e6, fs_in) for f in fl]
    d = path_from(fl, cic, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
    out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.6"/>')
    v450 = cic_yanit_db(R, N, 450e6, fs_in)
    out.append(f'<circle cx="{px_of(450, x0, x1, xmin, xmax):.1f}" cy="{py_of(v450, y0, y1, ymin, ymax):.1f}" r="4" fill="var(--gold)"/>')
    out.append(f'<text x="{px_of(450, x0, x1, xmin, xmax) + 6:.1f}" y="{py_of(v450, y0, y1, ymin, ymax) - 8:.1f}" class="s-kucuk s-altin">450 MHz: {v450:.0f} dB (en zayıf alias bastırma)</text>')
    out.append(f'<text x="{px_of(600, x0, x1, xmin, xmax):.1f}" y="{y1 + 14}" text-anchor="middle" class="s-kucuk s-kirmizi">alias bandı 450–750</text>')
    out.append(f'<text x="{px_of(1125, x0, x1, xmin, xmax):.1f}" y="{y1 + 14}" text-anchor="middle" class="s-kucuk s-kirmizi">1050–1200</text>')
    out.append(f'<text x="{px_of(75, x0, x1, xmin, xmax):.1f}" y="{y1 + 14}" text-anchor="middle" class="s-kucuk s-vurgu">geçirme ±150</text>')
    out.append(f'<text x="{px_of(600, x0, x1, xmin, xmax):.1f}" y="{y0 - 6}" text-anchor="middle" class="s-kucuk">sıfır: 600 MHz (= fs_out)</text>')
    out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">frekans (MHz) · dB</text>')
    # sağ panel: 0..150 MHz
    x0, x1 = 600, 880
    xmin, xmax, ymin, ymax = 0, 150, -4, 4
    out.append(f'<text x="{x0}" y="{y1 - 12}" class="s-baslik">Geçirme bandı büyüteci 0–150 MHz</text>')
    out.append(eksen(x0, x1, y0, y1, [0, 50, 100, 150], [-4, -3, -2, -1, 0, 1, 2, 3, 4], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:+d}"))
    fl = [k * 150 / 300 for k in range(301)]
    cic_p = [cic_yanit_db(R, N, f * 1e6, fs_in) for f in fl]
    komp = fir_yanit_db(hk, [f * 1e6 for f in fl], fs_out)
    top = [a + b for a, b in zip(cic_p, komp)]
    print("    g-162: droop 150 MHz %.2f dB; toplam düzlük min %.2f max %.2f dB (0–150)" % (cic_p[-1], min(top), max(top)))
    stop = fir_yanit_db(hk, [f * 1e6 for f in (210e-6 * 1e6 * 0 + 210, 250, 300)], fs_out)
    print("    g-162: komp FIR stopband 210/250/300 MHz: %s dB" % ", ".join(f"{v:.0f}" for v in stop))
    for ys, cls, w in ((cic_p, "var(--accent)", 1.6), (komp, "var(--gold)", 1.6), (top, "var(--green)", 2.0)):
        d = path_from(fl, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}" fill="none" stroke="{cls}" stroke-width="{w}"/>')
    out.append(f'<text x="{x0 + 6}" y="{y1 + 14}" class="s-kucuk s-altin">kompanzasyon FIR (31 tap, 600 MSPS)</text>')
    out.append(f'<text x="{x0 + 6}" y="{y1 + 28}" class="s-kucuk s-yesil">CIC + kompanzasyon: ±{max(abs(min(top)), abs(max(top))):.2f} dB</text>')
    out.append(f'<text x="{x1 - 4}" y="{py_of(cic_p[-1], y0, y1, ymin, ymax) + 14:.1f}" text-anchor="end" class="s-kucuk s-vurgu">CIC droop {cic_p[-1]:.1f} dB @150</text>')
    out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">frekans (MHz) · dB</text>')
    yaz("g-162-cic-yanit.svg", out, "CIC yanıtı + kompanzasyon")
    return hk


# ------------------------------------------------------------------ g-163
def g_163():
    n = 8192
    x = ortak_sinyal(n)
    y = mix(x, F_NCO, FS, -1)
    c = cic_uygula(y, 4, 4)                      # 600 MSPS
    hk = komp_fir_tasarla()
    k = fir_uygula(c, hk)                         # 600 MSPS
    hb = halfband(23)
    hbo = fir_uygula(k, hb)
    d = decimate(hbo, 2)                          # 300 MSPS
    sp = [spektrum_kompleks(y), spektrum_kompleks(c[:2048]), spektrum_kompleks(k[:2048]), spektrum_kompleks(d[:1024])]
    fss = [FS, FS / 4, FS / 4, FS / 8]
    def gur(x_, fs_):
        return guc_db(x_[:int(0.8e-6 * fs_)])
    g = [gur(y, FS), gur(c, FS / 4), gur(k, FS / 4), gur(d, FS / 8)]
    print("    g-163: gürültü gücü kademeler: " + ", ".join(f"{v:.1f}" for v in g) + " dBFS")
    W = 900
    top = 150
    ph, gap = 120, 56
    H = top + 4 * (ph + gap)
    out = svg_bas("g163", W, H, "Referans senaryonun çok kademeli decimation zinciri (hesaplanmış): mixer çıkışı 2400 MSPS → CIC R=4,N=4 → 600 MSPS → 31 tap kompanzasyon FIR → "
                  "23 tap halfband ↓2 → 300 MSPS; alt panellerde her kademe çıkışının spektrumu ve gürültü gücü.")
    # blok şeridi
    bx = [40, 200, 380, 560, 740]
    by = 30
    out.append(f'<text x="{bx[0]}" y="{by - 10}" class="s-kucuk">mixer çıkışı</text>')
    out.append(f'<text x="{bx[0]}" y="{by + 26}" class="s-mono2">2400 MSPS</text><text x="{bx[0]}" y="{by + 40}" class="s-mono2">kompleks 16+16</text>')
    def blok(x, ad, alt, cls="blok"):
        out.append(f'<rect x="{x}" y="{by}" width="130" height="50" rx="6" class="{cls}"/>')
        out.append(f'<text x="{x + 65}" y="{by + 21}" text-anchor="middle" class="s-metin" style="font-weight:700">{ad}</text>')
        out.append(f'<text x="{x + 65}" y="{by + 38}" text-anchor="middle" class="s-kucuk">{alt}</text>')
    blok(bx[1], "CIC ↓4", "R = 4, N = 4 · çarpıcısız · +8 bit")
    blok(bx[2], "komp. FIR", "31 tap · 600 MSPS · droop düzeltme")
    blok(bx[3], "halfband ↓2", "23 tap · 7 çarpıcı · fc = 150 MHz")
    for i in range(4):
        xa = bx[i] + (130 if i else 110)
        out.append(f'<path d="M{xa} {by + 25} H{bx[i + 1] - 4}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    for i, t in ((1, "2400 → 600 MSPS"), (2, "600 MSPS"), (3, "600 → 300 MSPS")):
        out.append(f'<text x="{(bx[i] + 130 + bx[i + 1]) / 2:.0f}" y="{by + 18}" text-anchor="middle" class="s-kucuk">{t}</text>')
    out.append(f'<text x="{bx[4]}" y="{by + 12}" class="s-kucuk">DDC çıkışı</text><text x="{bx[4]}" y="{by + 28}" class="s-mono2">300 MSPS</text><text x="{bx[4]}" y="{by + 42}" class="s-mono2">16+16 bit, ±150 MHz</text>')
    out.append(f'<text x="{bx[1]}" y="{by + 72}" class="s-kucuk">akümülatör 24 bit (wrap) → 16 bit</text>')
    out.append(f'<text x="{bx[3]}" y="{by + 72}" class="s-kucuk">polyphase: iki yol, biri yalnız gecikme</text>')
    # paneller
    x0, x1 = 60, W - 20
    ymin, ymax = -130, 0
    yt = [0, -40, -80, -120]
    basliklar = ["(a) mixer çıkışı — 2400 MSPS, ±1200 MHz", "(b) CIC ↓4 çıkışı — 600 MSPS, ±300 MHz",
                 "(c) kompanzasyon FIR çıkışı — 600 MSPS, ±300 MHz", "(d) halfband ↓2 çıkışı — 300 MSPS, ±150 MHz"]
    xts = [[-1200, -800, -400, 0, 400, 800, 1200], [-300, -200, -100, 0, 100, 200, 300], [-300, -200, -100, 0, 100, 200, 300], [-150, -100, -50, 0, 50, 100, 150]]
    notlar = [f"gürültü gücü {g[0]:.0f} dBFS · image −1200 MHz", f"gürültü {g[1]:.0f} dBFS · kenarlarda droop, ±150 dışı alias kalıntısı < −40 dB",
              f"gürültü {g[2]:.0f} dBFS · geçirme bandı düz", f"gürültü {g[3]:.0f} dBFS · toplam düşüş {g[0] - g[3]:.0f} dB · işlem kazancı 6 dB"]
    for i in range(4):
        y1 = top + i * (ph + gap)
        y0 = y1 + ph
        def ek(xmin, xmax, ymin_, ymax_, i=i, y0=y0, y1=y1):
            if i == 1:
                fl = [(kk - 400) * 600 / 800 for kk in range(801)]
                cr = [cic_yanit_db(4, 4, abs(f) * 1e6, FS) for f in fl]
                d_ = path_from(fl, cr, x0, x1, y0, y1, xmin, xmax, ymin_, ymax_)
                out.append(f'<path d="{d_}" class="spk-filtre"/>')
                out.append(f'<text x="{px_of(160, x0, x1, xmin, xmax):.1f}" y="{y1 + 16}" class="s-kucuk s-altin">CIC yanıtı (katlanmış)</text>')
            if i == 2:
                fl = [(kk - 400) * 600 / 800 for kk in range(801)]
                hr = fir_yanit_db(hb, [abs(f) * 1e6 for f in fl], FS / 4)
                d_ = path_from(fl, hr, x0, x1, y0, y1, xmin, xmax, ymin_, ymax_)
                out.append(f'<path d="{d_}" class="spk-filtre"/>')
                out.append(f'<text x="{px_of(160, x0, x1, xmin, xmax):.1f}" y="{y1 + 16}" class="s-kucuk s-altin">halfband yanıtı (−6 dB @150)</text>')
        spektrum_paneli(out, sp[i], fss[i], x0, x1, y0, y1, ymin, ymax, xts[i], yt, basliklar[i], "", ek)
        out.append(f'<text x="{x1}" y="{y0 + 28}" text-anchor="end" class="s-kucuk">{notlar[i]}</text>')
        out.append(f'<text x="{x0}" y="{y0 + 28}" class="s-kucuk">MHz · dBFS</text>')
    yaz("g-163-cok-kademeli-zincir.svg", out, "çok kademeli zincir")


# ------------------------------------------------------------------ g-171
def g_171():
    K = 16
    Np = 128
    hp = fir_tasarla(82e6, FS, Np, 9.0)
    fl = [375 + k * 600 / 800 for k in range(801)]
    merkezler = [450, 600, 750, 900]
    # −3 dB noktası ve stopband
    r0 = fir_yanit_db(hp, [k * 1e6 for k in range(0, 301)], FS)
    f3 = next(k for k in range(301) if r0[k] < -3)
    f6 = next(k for k in range(301) if r0[k] < -6)
    stop = max(r0[150:])
    print(f"    g-171: prototip −3 dB @{f3} MHz, −6 dB @{f6} MHz, stopband (>150 MHz) {stop:.0f} dB")
    W, H = 900, 520
    out = svg_bas("g171", W, H, "Kanal yanıtları ve bindirme (hesaplanmış, 128 tap Kaiser prototip, kanal aralığı 150 MHz): üstte kritik örnekleme, kanalın Nyquist sınırı ±75 MHz "
                  "geçiş bandının içinden geçer ve geçiş bandı kanala katlanır; altta iki kat aşırı örnekleme, Nyquist ±150 MHz stopband'de, katlanma yok, komşular −3 dB'de kesişir; "
                  "güçlü emiterin komşu kanala sızıntısı stopband seviyesinde, kanal kenarındaki sinyal iki kanalda eşit.")
    x0, x1 = 60, W - 20
    xmin, xmax, ymin, ymax = 375, 975, -100, 5
    for p, (bas, fs_k) in enumerate((("Kritik örnekleme: M = K = 16 → kanal fs = 150 MSPS, Nyquist ±75 MHz", 150), ("İki kat aşırı örnekleme: M = 8 → kanal fs = 300 MSPS, Nyquist ±150 MHz", 300))):
        y1 = 40 + p * 250
        y0 = y1 + 180
        out.append(f'<text x="{x0}" y="{y1 - 10}" class="s-baslik">{bas}</text>')
        out.append(eksen(x0, x1, y0, y1, [450, 525, 600, 675, 750, 825, 900], [0, -20, -40, -60, -80, -100], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        ny = fs_k / 2
        # katlanma bölgesi (kritik): 600 kanalında ±75 dışı geçiş bandı
        if p == 0:
            for a, b in ((600 - 150 + 75, 600 - 75), (600 + 75, 600 + 150 - 75)):
                pass
            # geçiş bandı: |f-600| 60..100 MHz → 75 dışında kalan 75..100 katlanır
            for a, b in ((600 - 100, 600 - 75), (600 + 75, 600 + 100)):
                out.append(f'<rect x="{px_of(a, x0, x1, xmin, xmax):.1f}" y="{y1}" width="{px_of(b, x0, x1, xmin, xmax) - px_of(a, x0, x1, xmin, xmax):.1f}" height="{y0 - y1}" fill="var(--red)" opacity=".18"/>')
            out.append(f'<text x="{px_of(690, x0, x1, xmin, xmax):.1f}" y="{y0 - 12}" class="s-kucuk s-kirmizi">geçiş bandı kanala katlanır</text>')
        for m in merkezler:
            ys = [fir_yanit_db(hp, [abs(f - m) * 1e6], FS)[0] for f in fl]
            d = path_from(fl, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
            if m == 600:
                out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" fill="var(--accent)" opacity=".10"/>')
                out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.8"/>')
            else:
                out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.1" opacity=".45"/>')
            out.append(f'<text x="{px_of(m, x0, x1, xmin, xmax):.1f}" y="{y1 + 14}" text-anchor="middle" class="s-kucuk s-vurgu">k = {merkezler.index(m) + 3} · {m} MHz</text>')
        for sgn in (-1, 1):
            px = px_of(600 + sgn * ny, x0, x1, xmin, xmax)
            out.append(f'<line x1="{px:.1f}" y1="{y1}" x2="{px:.1f}" y2="{y0}" stroke="var(--ink-2)" stroke-dasharray="5 4"/>')
        out.append(f'<text x="{px_of(600 + ny, x0, x1, xmin, xmax) + 4:.1f}" y="{y1 + 30}" class="s-kucuk">kanal 4 Nyquist ±{ny:.0f}</text>')
        # kesişim noktası
        kes = fir_yanit_db(hp, [75e6], FS)[0]
        out.append(f'<circle cx="{px_of(675, x0, x1, xmin, xmax):.1f}" cy="{py_of(kes, y0, y1, ymin, ymax):.1f}" r="4" fill="var(--gold)"/>')
        out.append(f'<text x="{px_of(675, x0, x1, xmin, xmax) + 6:.1f}" y="{py_of(kes, y0, y1, ymin, ymax) - 6:.1f}" class="s-kucuk s-altin">kesişim {kes:.1f} dB @675 (kenar sinyali iki kanalda eşit)</text>')
        if p == 1:
            # güçlü emiter 600 → komşu sızıntısı
            px = px_of(600, x0, x1, xmin, xmax)
            out.append(f'<path d="M{px:.1f} {y0 - 4} V{y1 + 44}" class="yol-sayisal" stroke-width="2.4" marker-end="url(#ok-sayisal)"/>')
            out.append(f'<text x="{px + 6:.1f}" y="{y1 + 58}" class="s-kucuk s-vurgu">güçlü emiter</text>')
            for m in (450, 750):
                lv = fir_yanit_db(hp, [150e6], FS)[0]
                pxm = px_of(600, x0, x1, xmin, xmax)
                out.append(f'<path d="M{px_of(600 + (m - 600) * 0.15, x0, x1, xmin, xmax):.1f} {py_of(lv, y0, y1, ymin, ymax) - 26:.1f} L{px_of(m + (600 - m) * 0.12, x0, x1, xmin, xmax):.1f} {py_of(lv, y0, y1, ymin, ymax) - 4:.1f}" class="yol-gurultu" marker-end="url(#ok-gurultu)"/>')
            out.append(f'<text x="{px_of(750, x0, x1, xmin, xmax) + 10:.1f}" y="{py_of(lv, y0, y1, ymin, ymax) - 10:.1f}" class="s-kucuk s-kirmizi">komşuya sızıntı ≈ {lv:.0f} dB (stopband)</text>')
        out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">frekans (MHz) · dB</text>')
    yaz("g-171-kanal-yanitlari.svg", out, "kanal yanıtları")
    return hp


# ------------------------------------------------------------------ g-172
def g_172():
    n = 6144                        # 2.56 µs @2400
    fs = FS
    Np = 128
    hp = fir_tasarla(82e6, fs, Np, 9.0)
    rnd = LCG(5)
    rise = 10e-9
    f_c = 620e6
    t0 = 0.6e-6
    z = darbe_zarfi(n, fs, PW, rise, t0)
    x = [0.7 * z[k] * math.cos(TAU * f_c * k / fs) + rnd.gauss(1e-4) for k in range(n)]
    kanallar = [2, 3, 4, 5, 6]
    guc = {}
    for kk in kanallar:
        y = mix(x, kk * fs / 16, fs, -1)
        fy = fir_uygula(y, hp)
        d = decimate(fy, 8)
        guc[kk] = [10 * math.log10(max(abs(v) ** 2, 1e-30)) for v in d]
    fs_o = fs / 8
    t = [k / fs_o * 1e6 for k in range(len(guc[4]))]
    # metrikler: komşu kanalda darbe içi seviye ve kulak tepe seviyesi
    ref = max(guc[4])
    def kulak(kk):
        a, b = int((t0 + 0.2e-6) * fs_o), int((t0 + 0.8e-6) * fs_o)
        ici = max(guc[kk][a:b])
        tepe = max(guc[kk][int((t0 - 0.1e-6) * fs_o):int((t0 + 0.15e-6) * fs_o)])
        # kulak süresi: tepe − 10 dB üstünde kalan süre
        seg = guc[kk][int((t0 - 0.1e-6) * fs_o):int((t0 + 0.2e-6) * fs_o)]
        sure = sum(1 for v in seg if v > tepe - 10) / fs_o * 1e9
        return ici - ref, tepe - ref, sure
    for kk in (3, 5, 2):
        ici, tepe, sure = kulak(kk)
        print(f"    g-172: kanal {kk}: darbe içi {ici:.0f} dBc, kulak tepesi {tepe:.0f} dBc, süre(−10 dB) ≈ {sure:.0f} ns")
    W, H = 900, 440
    out = svg_bas("g172", W, H, "Rabbit ear etkisi (hesaplanmış): 16 kanallı kanallaştırıcıda 1 µs, 10 ns kenarlı, 620 MHz'lik darbe. Kanal 4 temiz zarf; komşu kanallar 3 ve 5 darbe süresince "
                  "yalnızca stopband sızıntısı görür ama darbenin başında ve sonunda filtre geçici rejimi kadar süren, tespit eşiğini aşabilen iki çıkıntı üretir. Sağda kanal–zaman ısı haritası.")
    x0, x1 = 60, 600
    xmin, xmax, ymin, ymax = 0, 2.5, -100, 5
    esik = -62
    for i, kk in enumerate((4, 3, 5)):
        y1 = 36 + i * 130
        y0 = y1 + 100
        out.append(f'<text x="{x0}" y="{y1 - 8}" class="s-baslik">kanal {kk} — {kk * 150} MHz {"(darbenin kanalı)" if kk == 4 else "(komşu)"}</text>')
        out.append(eksen(x0, x1, y0, y1, [0, 0.5, 1, 1.5, 2, 2.5], [0, -40, -80], xmin, xmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:d}"))
        ys = [v - ref for v in guc[kk]]
        d = path_from(t, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-sinyal" opacity=".18"/>')
        out.append(f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="1.3"/>')
        py = py_of(esik, y0, y1, ymin, ymax)
        out.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="var(--red)" stroke-dasharray="5 4" opacity=".8"/>')
        if kk != 4:
            ici, tepe, sure = kulak(kk)
            for tt in (t0, t0 + PW):
                px = px_of(tt * 1e6, x0, x1, xmin, xmax)
                out.append(f'<circle cx="{px:.1f}" cy="{py_of(tepe, y0, y1, ymin, ymax):.1f}" r="4" fill="none" stroke="var(--red)" stroke-width="1.5"/>')
            out.append(f'<text x="{px_of(t0 * 1e6, x0, x1, xmin, xmax) + 8:.1f}" y="{py_of(tepe, y0, y1, ymin, ymax) - 6:.1f}" class="s-kucuk s-kirmizi">kulak {tepe:.0f} dBc, ≈ {sure:.0f} ns</text>')
            out.append(f'<text x="{px_of(1.25, x0, x1, xmin, xmax):.1f}" y="{py_of(ici, y0, y1, ymin, ymax) - 6:.1f}" text-anchor="middle" class="s-kucuk">darbe içi sızıntı {ici:.0f} dBc</text>')
        else:
            out.append(f'<text x="{px_of(1.1, x0, x1, xmin, xmax):.1f}" y="{y1 + 14}" text-anchor="middle" class="s-kucuk s-vurgu">1 µs darbe, 0 dBc</text>')
        out.append(f'<text x="{x1 - 4}" y="{py - 4:.1f}" text-anchor="end" class="s-kucuk s-kirmizi">CFAR eşiği (örnek) {esik} dBc</text>')
    out.append(f'<text x="{(x0 + x1) / 2}" y="{H - 8}" text-anchor="middle" class="s-kucuk">zaman (µs) · dBc (kanal 4 tepesine göre)</text>')
    # ısı haritası
    hx0, hx1, hy0, hy1 = 660, 880, 366, 36
    out.append(f'<text x="{hx0}" y="{hy1 - 8}" class="s-baslik">kanal–zaman</text>')
    out.append(f'<rect x="{hx0}" y="{hy1}" width="{hx1 - hx0}" height="{hy0 - hy1}" class="eksen"/>')
    nb = 64
    L = len(guc[4])
    rh = (hy0 - hy1) / len(kanallar)
    for r, kk in enumerate(reversed(kanallar)):
        for bidx in range(nb):
            a, b = bidx * L // nb, (bidx + 1) * L // nb
            v = max(guc[kk][a:b]) - ref
            op = max(0.0, min(1.0, (v + 90) / 90))
            if op < 0.05:
                continue
            out.append(f'<rect x="{hx0 + bidx * (hx1 - hx0) / nb:.1f}" y="{hy1 + r * rh:.1f}" width="{(hx1 - hx0) / nb + 0.5:.1f}" height="{rh:.1f}" fill="var(--accent)" opacity="{op:.2f}"/>')
        out.append(f'<text x="{hx0 - 6}" y="{hy1 + r * rh + rh / 2 + 4:.1f}" text-anchor="end" class="s-mono2">k{kk}</text>')
    out.append(f'<text x="{hx0}" y="{hy0 + 14}" class="s-mono2">0</text><text x="{hx1}" y="{hy0 + 14}" text-anchor="end" class="s-mono2">2.5 µs</text>')
    out.append(f'<text x="{(hx0 + hx1) / 2}" y="{hy0 + 30}" text-anchor="middle" class="s-kucuk">parlaklık ∝ dBc</text>')
    out.append(f'<text x="{hx0}" y="{hy0 + 50}" class="s-kucuk">kulaklar: kanal 3 ve 5’te darbenin</text><text x="{hx0}" y="{hy0 + 64}" class="s-kucuk">başında ve sonunda iki nokta</text>')
    yaz("g-172-rabbit-ear.svg", out, "rabbit ear")


# ------------------------------------------------------------------ g-132
def g_132():
    """Bit-exact karşılaştırma fark desenleri (öğretici, sentetik): dört tipik e[n] görüntüsü."""
    n = 400
    rnd = LCG(3)
    ref = [round(3000 * math.sin(TAU * 7 * k / n) + rnd.gauss(50)) for k in range(n)]

    def hw_yuvarlama():
        return [v + (1 if (rnd.u() < 0.04 and v < 0) else 0) for v in ref]

    def hw_hizalama():
        return [ref[max(0, k - 3)] for k in range(n)]

    def hw_tasma():
        return [v if (k < 260 or abs(v) < 2200) else (2200 if v > 0 else -2200) for k, v in enumerate(ref)]

    def hw_baslangic():
        return [round(rnd.u() * 6000 - 3000) if k < 60 else v for k, v in enumerate(ref)]

    paneller = [
        ("(a) ±1 LSB, seyrek, yalnızca negatif değerlerde → yuvarlama kuralı (half-up / away-from-zero) uyuşmazlığı", hw_yuvarlama(), 4),
        ("(b) büyük, sinyal biçimli fark → hizalama (L) hatası: 3 örnek kaydır, sıfırlanır", hw_hizalama(), 1200),
        ("(c) belirli bir örnekten sonra, yalnızca tepelerde → taşma / doyurma farkı (model doyuruyor, RTL doyurmuyor ya da tersi)", hw_tasma(), 1200),
        ("(d) yalnızca ilk N örnek → başlangıç durumu (gecikme hatları, reset); ısınmayı atla", hw_baslangic(), 4000),
    ]
    W, H = 900, 4 * 118 + 30
    out = svg_bas("g132", W, H, "Bit-exact karşılaştırmada dört tipik fark deseni (öğretici, sentetik veri): (a) seyrek ±1 LSB fark yuvarlama kuralı uyuşmazlığı; "
                  "(b) sinyal biçimli büyük fark hizalama hatası; (c) belirli bir örnekten sonra tepelerde başlayan fark taşma/doyurma; (d) yalnızca ilk örneklerde fark başlangıç durumu.")
    x0, x1 = 60, W - 20
    for i, (bas, hw, lim) in enumerate(paneller):
        y1 = 26 + i * 118
        y0 = y1 + 80
        e = [hw[k] - ref[k] for k in range(n)]
        out.append(f'<text x="{x0}" y="{y1 - 8}" class="s-baslik">{bas}</text>')
        out.append(eksen(x0, x1, y0, y1, [0, 100, 200, 300, 400], [-lim, 0, lim], 0, n, -lim * 1.1, lim * 1.1, lambda v: f"{v:d}", lambda v: f"{v:d}"))
        for k in range(n):
            if e[k] == 0:
                continue
            px = px_of(k, x0, x1, 0, n)
            py0 = py_of(0, y0, y1, -lim * 1.1, lim * 1.1)
            py1 = py_of(e[k], y0, y1, -lim * 1.1, lim * 1.1)
            out.append(f'<line x1="{px:.1f}" y1="{py0:.1f}" x2="{px:.1f}" y2="{py1:.1f}" stroke="var(--red)" stroke-width="1.2"/>')
        maxe = max(abs(v) for v in e)
        ilk = next((k for k in range(n) if e[k] != 0), None)
        out.append(f'<text x="{x1}" y="{y0 + 26}" text-anchor="end" class="s-kucuk">e[n] = hw − ref (LSB) · max |e| = {maxe} · ilk fark örneği: {ilk} · fark sayısı: {sum(1 for v in e if v)}/{n}</text>')
    yaz("g-132-fark-desenleri.svg", out, "fark desenleri")


# ------------------------------------------------------------------ g-152
def g_152():
    """fs/4 hilesi: x[n], 1,0,−1,0 ve 0,−1,0,1 dizileri, I ve Q örnekleri (660 MHz ton, 2400 MSPS)."""
    n = 24
    f = F_NCO + 60e6
    x = [math.cos(TAU * f * k / FS + 0.4) for k in range(n)]
    c = [1, 0, -1, 0]
    s = [0, -1, 0, 1]
    I = [x[k] * c[k % 4] for k in range(n)]
    Q = [x[k] * s[k % 4] for k in range(n)]
    W, H = 900, 400
    out = svg_bas("g152", W, H, "fs/4 hilesi (hesaplanmış): ADC örnekleri x[n], cos dizisi 1,0,−1,0 ve −sin dizisi 0,−1,0,1; çarpım yalnızca işaret çevirme ve sıfırlamadır; "
                  "I çıkışı çift indisli, Q çıkışı tek indisli örneklerden oluşur; NCO tam fs/4'te olduğundan çarpıcı gerekmez.")
    x0, x1 = 70, W - 30
    satirlar = [("x[n] — ADC çıkışı (660 MHz ton, 2400 MSPS)", x, "var(--accent)"),
                ("cos(πn/2) = 1, 0, −1, 0 …   ·   −sin(πn/2) = 0, −1, 0, 1 …", None, None),
                ("I[n] = x[n]·{1,0,−1,0}: yalnızca çift n, işaret her ikide bir ters", I, "var(--accent)"),
                ("Q[n] = x[n]·{0,−1,0,1}: yalnızca tek n", Q, "var(--purple)")]
    for i, (bas, ys, renk) in enumerate(satirlar):
        y1 = 30 + i * 92
        y0 = y1 + 60
        out.append(f'<text x="{x0}" y="{y1 - 8}" class="s-baslik">{bas}</text>')
        if ys is None:
            for k in range(n):
                px = px_of(k, x0, x1, -0.5, n - 0.5)
                cv, sv = c[k % 4], s[k % 4]
                out.append(f'<rect x="{px - 14:.1f}" y="{y1 + 2}" width="28" height="22" rx="3" fill="{"var(--accent-soft)" if cv else "var(--dia-blok)"}" stroke="var(--line-2)"/>')
                out.append(f'<text x="{px:.1f}" y="{y1 + 17}" text-anchor="middle" class="s-mono2">{cv:+d}</text>'.replace("+0", "0"))
                out.append(f'<rect x="{px - 14:.1f}" y="{y1 + 30}" width="28" height="22" rx="3" fill="{"var(--purple-soft)" if sv else "var(--dia-blok)"}" stroke="var(--line-2)"/>')
                out.append(f'<text x="{px:.1f}" y="{y1 + 45}" text-anchor="middle" class="s-mono2">{sv:+d}</text>'.replace("+0", "0"))
            out.append(f'<text x="{x0 - 6}" y="{y1 + 17}" text-anchor="end" class="s-kucuk">cos</text>')
            out.append(f'<text x="{x0 - 6}" y="{y1 + 45}" text-anchor="end" class="s-kucuk">−sin</text>')
            continue
        pym = (y0 + y1) / 2
        out.append(f'<line x1="{x0}" y1="{pym}" x2="{x1}" y2="{pym}" class="eksen"/>')
        for k in range(n):
            px = px_of(k, x0, x1, -0.5, n - 0.5)
            py = pym - ys[k] * 28
            if abs(ys[k]) < 1e-9 and i > 0:
                out.append(f'<circle cx="{px:.1f}" cy="{pym:.1f}" r="2.5" fill="none" stroke="var(--ink-3)"/>')
                continue
            out.append(f'<line x1="{px:.1f}" y1="{pym:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{renk}" stroke-width="2"/>')
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{renk}"/>')
        if i == 0:
            pts = []
            for m in range(0, 231):
                t = -0.5 + m * n / 230
                pts.append(f"{px_of(t, x0, x1, -0.5, n - 0.5):.1f},{pym - math.cos(TAU * f * t / FS + 0.4) * 28:.1f}")
            out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="var(--accent)" stroke-width="1" opacity=".35"/>')
        out.append(f'<text x="{x0 - 6}" y="{pym + 4}" text-anchor="end" class="s-kucuk">0</text>')
    for k in range(0, n, 4):
        out.append(f'<text x="{px_of(k, x0, x1, -0.5, n - 0.5):.1f}" y="{H - 8}" text-anchor="middle" class="s-mono2">n = {k}</text>')
    out.append(f'<text x="{x1}" y="{H - 8}" text-anchor="end" class="s-kucuk">DSP slice: 0 · yalnızca işaret çevirme + çoklayıcı · sonra LPF ve ↓M</text>')
    yaz("g-152-fs4-hilesi.svg", out, "fs/4 hilesi")


URETICILER = {"g-122": g_122, "g-132": g_132, "g-150": g_150, "g-152": g_152, "g-162": g_162, "g-163": g_163, "g-171": g_171, "g-172": g_172}


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
