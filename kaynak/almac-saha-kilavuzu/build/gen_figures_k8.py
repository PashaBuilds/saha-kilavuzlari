#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k8.py — Kısım VIII (PDW Üretimi, Bölüm 24–27) şekil üreticisi

gen_figures.py ile aynı kurallar: yalnızca stdlib, renk yalnızca CSS
değişkeni / hazır sınıf, eğriler hesaplanır (elle uydurulmaz), dosyalar
repoda commit'li durur.

  python build/gen_figures_k8.py          # hepsini yaz
  python build/gen_figures_k8.py g-251    # yalnızca birini

Üretilenler:
  g-240 PDW bit alan haritası (kurgusal 128-bit format)
  g-241 darbeden PDW'ye indirgeme infografiği
  g-242 alan başına bit bütçesi
  g-250 tek darbe üzerinde ölçü noktaları (zaman + anlık frekans)
  g-251 time walk (kenar + eğri)
  g-252 darbe içi anlık frekans profili: sabit / LFM / faz kodlu
  g-260 darbe FSM diyagramı
  g-261 PDW veri yolu PL → PS
  g-262 iki kolun latency hizalaması (zamanlama)
  g-270 karışık PDW akışından emiter izlerine
"""
import html
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
FS = S["ddc"]["cikis_fs_msps"] * 1e6          # 300e6
TS = 1 / FS
PW = S["sinyal"]["pw_s"]
RISE = S["sinyal"]["rise_time_ns"] * 1e-9
CHIRP_BW = S["sinyal"]["varyant_b"]["chirp_bw_hz"]


# ------------------------------------------------------------------ küçük DSP
class LCG:
    """Deterministik basit üreteç (Box-Muller için)."""
    def __init__(self, seed=7):
        self.s = seed

    def u(self):
        self.s = (self.s * 1103515245 + 12345) % 2 ** 31
        return (self.s + 0.5) / 2 ** 31

    def g(self, sigma=1.0):
        u1, u2 = self.u(), self.u()
        return sigma * math.sqrt(-2 * math.log(u1)) * math.cos(TAU * u2)


def zarf(t, pw, rise):
    """dsp-core darbeZarfi eşdeğeri: kosinüs kenar, 0..1."""
    if t < 0 or t >= pw:
        return 0.0
    if rise > 0 and t < rise:
        return 0.5 - 0.5 * math.cos(math.pi * t / rise)
    if rise > 0 and t > pw - rise:
        return 0.5 - 0.5 * math.cos(math.pi * (pw - t) / rise)
    return 1.0


BARKER13 = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]


def darbe(n, fs, pw, rise, f0, mop="yok", bw=0.0, t0=0.0, snr_db=None, seed=7):
    """Kompleks darbe (I,Q) listesi; genlik 1, gürültü rms = 10^(-snr/20)."""
    rnd = LCG(seed)
    sig = 10 ** (-snr_db / 20) / math.sqrt(2) if snr_db is not None else 0
    i, q = [], []
    for k in range(n):
        t = k / fs - t0
        z = zarf(t, pw, rise)
        faz = TAU * f0 * (k / fs)
        if z > 0 and mop == "lfm":
            faz += math.pi * (bw / pw) * (t - pw / 2) ** 2 - math.pi * bw / pw * (pw / 2) ** 2
        elif z > 0 and mop == "barker13":
            cip = min(12, int(t / pw * 13))
            if BARKER13[cip] < 0:
                faz += math.pi
        i.append(z * math.cos(faz) + rnd.g(sig))
        q.append(z * math.sin(faz) + rnd.g(sig))
    return i, q


def guc_db(i, q):
    return [10 * math.log10(max(a * a + b * b, 1e-12)) for a, b in zip(i, q)]


def anlik_frekans(i, q, fs):
    out = [0.0]
    for k in range(1, len(i)):
        d = math.atan2(q[k] * i[k - 1] - i[k] * q[k - 1], i[k] * i[k - 1] + q[k] * q[k - 1])
        out.append(d / TAU * fs)
    out[0] = out[1]
    return out


def time_walk(rise, oran):
    oran = max(0.001, min(0.999, oran))
    return rise / math.pi * math.acos(1 - 2 * oran)


# ------------------------------------------------------------------ SVG yardımcıları
def path_from(xs, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax, adim=1):
    d = []
    n = 0
    for k in range(0, len(xs), adim):
        x, y = xs[k], ys[k]
        px = x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)
        py = y0 - (max(ymin, min(ymax, y)) - ymin) / (ymax - ymin) * (y0 - y1)
        d.append(("M" if n == 0 else "L") + f"{px:.1f} {py:.1f}")
        n += 1
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


def sarmala(gid, W, H, title, govde):
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-{gid}">\n'
            f'<title id="t-{gid}">{title}</title>\n{govde}\n</svg>\n')


def yaz(ad, icerik):
    (SVG / ad).write_text(icerik, encoding="utf-8")
    print("  yazıldı:", ad)


def txt(x, y, s, kls="s-metin", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="{kls}"{extra}>{html.escape(s, quote=False)}</text>'


# ================================================================== g-240
def g240():
    # kurgusal 128-bit format — 4 × 32-bit sözcük, bit 31 solda
    W, H = 900, 372
    x0, hucre, yb, yh, satir = 70, 24.5, 46, 44, 62
    alanlar = {  # sözcük: [(ust_bit, alt_bit, ad, sinif)]
        0: [(31, 0, "TOA[31:0] — zaman damgası, alt 32 bit (LSB = 3.333 ns)", "blok-aktif")],
        1: [(31, 26, "FLAGS", "blok-kontrol"), (25, 16, "PA (10 b, 0.25 dB)", "blok-aktif"), (15, 0, "TOA[47:32] — üst 16 bit", "blok-aktif")],
        2: [(31, 20, "AOA (12 b, 0.1°)", "blok-aktif"), (19, 0, "PW (20 b, LSB = 3.333 ns)", "blok-aktif")],
        3: [(31, 30, "CH", "blok-kontrol"), (29, 28, "MOP", "blok-kontrol"), (27, 20, "SEQ (8 b)", "blok-kontrol"), (19, 0, "RF (20 b, LSB = 10 kHz, mutlak)", "blok-aktif")],
    }
    p = []
    p.append(txt(x0, 22, "Kurgusal, öğretici 128-bit PDW formatı — 4 × 32-bit sözcük, little-endian; bit 31 solda, bit 0 sağda", "s-baslik"))
    # bit numaraları
    for b in range(32):
        px = x0 + (31 - b) * hucre + hucre / 2
        if b % 4 == 0 or b == 31:
            p.append(txt(px, yb - 6, str(b), "s-kucuk", "middle"))
    for w in range(4):
        y = yb + w * satir
        p.append(txt(x0 - 10, y + yh / 2 + 5, f"W{w}", "s-mono", "end"))
        p.append(txt(x0 - 10, y + yh / 2 + 18, f"bit {w * 32}–{w * 32 + 31}", "s-kucuk", "end"))
        for ust, alt, ad, kls in alanlar[w]:
            xa = x0 + (31 - ust) * hucre
            gen = (ust - alt + 1) * hucre
            p.append(f'<rect x="{xa:.1f}" y="{y}" width="{gen:.1f}" height="{yh}" rx="4" class="{kls}"/>')
            kisa = ad if gen > 150 else ad.split(" ")[0]
            p.append(txt(xa + gen / 2, y + yh / 2 + 4.5, kisa, "s-mono" if gen > 60 else "s-mono2", "middle"))
        # hücre çizgileri
        for b in range(33):
            px = x0 + b * hucre
            p.append(f'<line x1="{px:.1f}" y1="{y}" x2="{px:.1f}" y2="{y + yh}" class="izgara"/>')
    # açıklama
    ya = yb + 4 * satir + 6
    p.append(txt(x0, ya, "Ölçüm alanları (mavi): TOA 48 + PW 20 + PA 10 + RF 20 + AOA 12 = 110 bit", "s-metin2"))
    p.append(txt(x0, ya + 17, "Meta alanlar (yeşil) 18 bit: FLAGS[5:0] = SEG · POP · CLIP · SAT · AOA_INV · EXT   ·   SEQ 8 b (mod 256)   ·   MOP 2 b (0 yok, 1 LFM, 2 faz kodlu, 3 bilinmiyor)   ·   CH 2 b", "s-kucuk"))
    p.append(txt(x0, ya + 34, "Bu format bir öğretim aracıdır; hiçbir gerçek sistemin PDW yapısı değildir.", "s-kucuk s-kirmizi"))
    return sarmala("g240", W, H, "Kurgusal 128-bit PDW bit alan haritası: dört 32-bit sözcük; W0 TOA alt 32 bit; W1 TOA üst 16 bit, PA 10 bit, bayraklar 6 bit; W2 PW 20 bit, AOA 12 bit; W3 RF 20 bit, sıra numarası 8 bit, MOP tipi 2 bit, kanal 2 bit", "\n".join(p))


# ================================================================== g-241
def g241():
    W, H = 860, 340
    p = []
    p.append(txt(30, 24, "Ham örnekten PDW'ye: veri hızı basamak basamak düşer (log ölçek)", "s-baslik"))
    # üst: zaman şeridi — 1 ms PRI, 1 µs darbe
    x0, x1, y = 30, 830, 60
    p.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" class="eksen"/>')
    p.append(txt(x1 - 14, y - 8, "PRI = 1 ms  →  t", "s-kucuk", "end"))
    # darbe: 1 µs / 1 ms = %0.1 → 0.8 px; görünür olsun diye 3 px ve açıklama
    p.append(f'<rect x="{x0 + 40}" y="{y - 22}" width="3" height="22" class="spk-sinyal"/>')
    p.append(f'<rect x="{x0 + 40 + 800 * 0.98:.0f}" y="{y - 22}" width="3" height="22" class="spk-sinyal" opacity=".45"/>')
    p.append(txt(x0 + 50, y - 26, "darbe: 1 µs = 300 örnek (PRI'nin binde biri; ölçeksiz çizildi)", "s-kucuk"))
    p.append(f'<path d="M{x0 + 41} {y + 4} V{y + 22}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    p.append(txt(x0 + 48, y + 20, "→ 1 PDW (128 bit)", "s-mono2"))
    # alt: log ölçekli çubuklar
    bx0, bx1, by = 330, 820, 110
    logmin, logmax = 5, 11  # 100 kbps .. 100 Gbps
    satirlar = [
        ("ADC çıkışı: 2400 MSPS × 14 bit", 33.6e9, "blok-analog"),
        ("DDC çıkışı: 300 MSPS × 32 bit (I+Q)", 9.6e9, "blok-aktif"),
        ("yalnız darbe örnekleri: 300 × 32 bit × 1 kHz", 9.6e6, "blok-aktif"),
        ("PDW akışı: 128 bit × 1 kHz PRF", 128e3, "blok-kontrol"),
    ]
    for k, (ad, hiz, kls) in enumerate(satirlar):
        yy = by + k * 46
        px = bx0 + (math.log10(hiz) - logmin) / (logmax - logmin) * (bx1 - bx0)
        p.append(txt(bx0 - 8, yy + 17, ad, "s-metin2", "end"))
        p.append(f'<rect x="{bx0}" y="{yy}" width="{px - bx0:.1f}" height="26" rx="4" class="{kls}"/>')
        etiket = f"{hiz / 1e9:.1f} Gbps" if hiz >= 1e9 else (f"{hiz / 1e6:.1f} Mbps" if hiz >= 1e6 else f"{hiz / 1e3:.0f} kbps")
        p.append(txt(px + 6, yy + 17, etiket, "s-mono"))
    # eksen
    for d in range(logmin, logmax + 1):
        px = bx0 + (d - logmin) / (logmax - logmin) * (bx1 - bx0)
        p.append(f'<line x1="{px:.1f}" y1="{by - 6}" x2="{px:.1f}" y2="{by + 4 * 46}" class="izgara"/>')
        p.append(txt(px, by + 4 * 46 + 14, f"10^{d}", "s-kucuk", "middle"))
    p.append(txt((bx0 + bx1) / 2, by + 4 * 46 + 30, "bit/s (log)", "s-kucuk", "middle"))
    # oranlar
    p.append(txt(30, 318, "9.6 Gbps / 128 kbps = 75 000 : 1   ·   ADC'den itibaren 262 500 : 1   ·   darbe örneklerinden PDW'ye 75 : 1 (9600 bit → 128 bit)", "s-mono2"))
    return sarmala("g241", W, H, "Darbeden PDW'ye veri indirgeme: 1 ms PRI içinde 1 µs darbe; log ölçekli çubuklar ADC çıkışı 33.6 Gbps, DDC çıkışı 9.6 Gbps, yalnız darbe örnekleri 9.6 Mbps ve PDW akışı 128 kbps; oran 75 000:1", "\n".join(p))


# ================================================================== g-242
def g242():
    W, H = 860, 300
    pdw = S["pdw"]
    alanlar = [
        ("TOA", pdw["toa_bit"], "3.333 ns", "2^48 × 3.333 ns ≈ 10.9 gün (sarmadan)", "blok-aktif"),
        ("PW", pdw["pw_bit"], "3.333 ns", "2^20 × 3.333 ns ≈ 3.5 ms", "blok-aktif"),
        ("PA", pdw["pa_bit"], "0.25 dB", "1024 × 0.25 = 256 dB (log ölçek)", "blok-aktif"),
        ("RF", pdw["rf_bit"], "10 kHz", "2^20 × 10 kHz ≈ 10.49 GHz (mutlak)", "blok-aktif"),
        ("AOA", pdw["aoa_bit"], "0.1°", "4096 × 0.1° = 409.6° ≥ 360°", "blok-aktif"),
        ("meta", 18, "—", "FLAGS 6 · SEQ 8 · MOP 2 · CH 2", "blok-kontrol"),
    ]
    p = [txt(30, 24, "bit = ⌈log2(aralık / çözünürlük)⌉ — alan başına bütçe ve 128 bitlik toplam", "s-baslik")]
    x0, y0, olcek = 90, 50, 5.4  # px / bit
    for k, (ad, bit, lsb, aralik, kls) in enumerate(alanlar):
        y = y0 + k * 34
        p.append(txt(x0 - 8, y + 16, ad, "s-mono", "end"))
        p.append(f'<rect x="{x0}" y="{y}" width="{bit * olcek:.1f}" height="22" rx="3" class="{kls}"/>')
        p.append(txt(x0 + bit * olcek / 2, y + 15, f"{bit} bit", "s-mono2", "middle"))
        p.append(txt(x0 + 48 * olcek + 16, y + 10, f"LSB {lsb}", "s-kucuk"))
        p.append(txt(x0 + 48 * olcek + 16, y + 22, aralik, "s-kucuk"))
    # toplam şerit
    y = y0 + 6 * 34 + 8
    xx = x0
    for ad, bit, lsb, aralik, kls in alanlar:
        p.append(f'<rect x="{xx:.1f}" y="{y}" width="{bit * olcek:.1f}" height="18" class="{kls}"/>')
        if bit >= 10:
            p.append(txt(xx + bit * olcek / 2, y + 13, ad, "s-kucuk", "middle"))
        xx += bit * olcek
    p.append(txt(x0, y + 34, "toplam 48 + 20 + 10 + 20 + 12 + 18 = 128 bit = 4 × 32-bit sözcük — kurgusal, öğretici", "s-metin2"))
    return sarmala("g242", W, H, "Alan başına bit bütçesi: TOA 48, PW 20, PA 10, RF 20, AOA 12 ve meta 18 bit; her alanın LSB'si ve dinamik aralığı; toplam 128 bit", "\n".join(p))


# ================================================================== g-250
def g250():
    W, H = 860, 470
    fs = FS
    t0 = 0.3e-6
    n = 600  # 2 µs
    pwGen = PW + RISE  # %50 noktaları arası PW = 1 µs
    i, q = darbe(n, fs, pwGen, RISE, 5e6, t0=t0, snr_db=20, seed=3)
    pdb = guc_db(i, q)
    ts = [k / fs * 1e6 for k in range(n)]
    # eşikler: gürültü ortalama gücü -20 dB → T_on = -20 + 11.4 = -8.6 dB, T_off = T_on - 3
    ton, toff = -8.6, -11.6
    # geçişler
    bas = next(k for k in range(n) if pdb[k] > ton)
    son = next(k for k in range(bas + 50, n) if pdb[k] < toff)
    # üst panel
    x0, x1, y0, y1 = 70, 830, 230, 40
    xmin, xmax, ymin, ymax = 0, 2, -32, 4
    p = [txt(x0, 22, "Bir darbe üzerinde ölçü noktaları (fs = 300 MSPS, SNR = 20 dB, rise = 50 ns, f_bb = +5 MHz)", "s-baslik")]
    p.append(eksen(x0, x1, y0, y1, [0, 0.5, 1.0, 1.5, 2.0], [-30, -20, -10, 0], xmin, xmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    p.append(txt((x0 + x1) / 2, y0 + 30, "zaman (µs)", "s-kucuk", "middle"))
    p.append(txt(14, (y0 + y1) / 2, "güç (dB, tam ölçek = 0)", "s-kucuk", "middle", f' transform="rotate(-90 14 {(y0 + y1) / 2})"'))
    def PX(t): return x0 + (t - xmin) / (xmax - xmin) * (x1 - x0)
    def PY(v): return y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    # PA ölçüm bölgesi (kenarlar hariç %10)
    ka, kb = bas + int((son - bas) * 0.1), son - int((son - bas) * 0.1)
    p.append(f'<rect x="{PX(ts[ka]):.1f}" y="{y1}" width="{PX(ts[kb]) - PX(ts[ka]):.1f}" height="{y0 - y1}" class="spk-sinyal" opacity=".08"/>')
    p.append(f'<path d="{path_from(ts, pdb, x0, x1, y0, y1, xmin, xmax, ymin, ymax)}" class="yol-sayisal"/>')
    p.append(f'<line x1="{x0}" y1="{PY(ton):.1f}" x2="{x1}" y2="{PY(ton):.1f}" class="spk-filtre"/>')
    p.append(txt(x1 - 4, PY(ton) - 4, "T_on (eşik)", "s-kucuk s-altin", "end"))
    p.append(f'<line x1="{x0}" y1="{PY(toff):.1f}" x2="{x1}" y2="{PY(toff):.1f}" class="yol-gurultu"/>')
    p.append(txt(x1 - 4, PY(toff) + 12, "T_off = T_on − 3 dB (histerezis)", "s-kucuk s-kirmizi", "end"))
    p.append(txt(x0 + 6, PY(-1.5), "gürültü ortalaması −20 dB (SNR 20 dB)", "s-kucuk"))
    # TOA / bitiş
    for k, ad in ((bas, "TOA (T_on geçişi)"), (son, "bitiş (T_off geçişi)")):
        p.append(f'<line x1="{PX(ts[k]):.1f}" y1="{y1}" x2="{PX(ts[k]):.1f}" y2="{y0}" class="yol-kontrol"/>')
        p.append(f'<circle cx="{PX(ts[k]):.1f}" cy="{PY(pdb[k]):.1f}" r="4" fill="var(--green)"/>')
    p.append(txt(PX(ts[bas]) - 4, y1 + 14, "TOA", "s-metin s-yesil", "end"))
    p.append(txt(PX(ts[son]) + 4, y1 + 14, "bitiş", "s-metin s-yesil"))
    # PW oku
    yy = PY(-26)
    p.append(f'<path d="M{PX(ts[bas]):.1f} {yy} H{PX(ts[son]):.1f}" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    p.append(txt((PX(ts[bas]) + PX(ts[son])) / 2, yy - 5, f"PW = {(son - bas)} örnek × 3.333 ns = {(son - bas) / fs * 1e9:.0f} ns (eşik tanımıyla)", "s-mono2 s-yesil", "middle"))
    # %50 noktası
    k50 = int((t0 + RISE / 2) * fs)
    p.append(f'<circle cx="{PX(ts[k50]):.1f}" cy="{PY(-6):.1f}" r="3.5" fill="var(--gold)"/>')
    p.append(txt(PX(ts[k50]) + 6, PY(-6) - 6, "%50 genlik (−6 dB) noktası", "s-kucuk s-altin"))
    # PA
    tepe = max(pdb[bas:son])
    ort = sum(pdb[ka:kb]) / (kb - ka)
    p.append(txt(PX(0.83), PY(-17), f"PA: tepe {tepe:.1f} dB · kenarlar hariç ortalama {ort:.1f} dB (taralı bölge)", "s-mono2", "middle"))
    # alt panel — anlık frekans
    af = anlik_frekans(i, q, fs)
    afm = [v / 1e6 for v in af]
    x0b, x1b, y0b, y1b = 70, 830, 430, 280
    ymin2, ymax2 = -15, 25
    p.append(eksen(x0b, x1b, y0b, y1b, [0, 0.5, 1.0, 1.5, 2.0], [-10, 0, 10, 20], xmin, xmax, ymin2, ymax2, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    p.append(txt((x0b + x1b) / 2, y0b + 30, "zaman (µs)", "s-kucuk", "middle"))
    p.append(txt(14, (y0b + y1b) / 2, "anlık frekans (MHz)", "s-kucuk", "middle", f' transform="rotate(-90 14 {(y0b + y1b) / 2})"'))
    def PYb(v): return y0b - (v - ymin2) / (ymax2 - ymin2) * (y0b - y1b)
    p.append(f'<rect x="{PX(ts[ka]):.1f}" y="{y1b}" width="{PX(ts[kb]) - PX(ts[ka]):.1f}" height="{y0b - y1b}" class="spk-sinyal" opacity=".08"/>')
    p.append(f'<path d="{path_from(ts, afm, x0b, x1b, y0b, y1b, xmin, xmax, ymin2, ymax2)}" class="yol-sayisal" opacity=".9"/>')
    fort = sum(af[ka:kb]) / (kb - ka)
    p.append(f'<line x1="{PX(ts[ka]):.1f}" y1="{PYb(fort / 1e6):.1f}" x2="{PX(ts[kb]):.1f}" y2="{PYb(fort / 1e6):.1f}" class="spk-filtre"/>')
    p.append(txt(PX(0.83), y0b - 8, f"ölçüm penceresi ortalaması = {fort / 1e6:.3f} MHz (gerçek 5.000)", "s-mono2 s-altin", "middle"))
    p.append(txt(x0b + 6, y1b + 14, "darbe dışında anlık frekans gürültünün rastgele fazıdır → ±fs/2 saçılır; yalnız darbe içinde, kenarlar dışlanarak ortalanır", "s-kucuk"))
    return sarmala("g250", W, H, "Tek darbe üzerinde ölçü noktaları: üstte güç zarfı dB, T_on eşiği, histerezisli T_off, TOA ve bitiş geçişleri, PW oku, yüzde 50 genlik noktası, kenarları dışlayan PA ölçüm bölgesi; altta aynı darbenin anlık frekansı ve ölçüm penceresi ortalaması", "\n".join(p))


# ================================================================== g-251
def g251():
    W, H = 860, 430
    fs = FS
    # üst: yükselen kenar yakınlaştırma — 0 dB ve -20 dB darbe, sabit eşik -28 dB (güç)
    x0, x1, y0, y1 = 70, 420, 200, 40
    xmin, xmax, ymin, ymax = 0, 100, -40, 4
    p = [txt(x0, 22, "Time walk: aynı eşik, farklı genlik → farklı TOA", "s-baslik")]
    p.append(eksen(x0, x1, y0, y1, [0, 25, 50, 75, 100], [-40, -30, -20, -10, 0], xmin, xmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    p.append(txt((x0 + x1) / 2, y0 + 30, "zaman (ns) — yükselen kenar", "s-kucuk", "middle"))
    p.append(txt(14, (y0 + y1) / 2, "güç (dB)", "s-kucuk", "middle", f' transform="rotate(-90 14 {(y0 + y1) / 2})"'))
    def PX(t): return x0 + (t - xmin) / (xmax - xmin) * (x1 - x0)
    def PY(v): return y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
    esik = -28.0
    tt = [k * 0.5 for k in range(0, 201)]
    for tepe_db, kls, ad in ((0, "yol-sayisal", "güçlü darbe (0 dB)"), (-20, "yol-analog", "zayıf darbe (−20 dB)")):
        ys = []
        for t in tt:
            z = zarf(t * 1e-9, 10e-6, RISE)
            ys.append(tepe_db + 20 * math.log10(max(z, 1e-4)))
        p.append(f'<path d="{path_from(tt, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax)}" class="{kls}"/>')
        oran = 10 ** ((esik - tepe_db) / 20)
        tx = time_walk(RISE, oran) * 1e9
        p.append(f'<line x1="{PX(tx):.1f}" y1="{PY(esik):.1f}" x2="{PX(tx):.1f}" y2="{y0}" class="yol-kontrol"/>')
        p.append(f'<circle cx="{PX(tx):.1f}" cy="{PY(esik):.1f}" r="4" fill="var(--green)"/>')
        p.append(txt(PX(tx) + 3, y0 - 6, f"{tx:.1f} ns", "s-mono2 s-yesil"))
        p.append(txt(x0 + 8, PY(tepe_db) - 5, ad, "s-kucuk"))
    p.append(f'<line x1="{x0}" y1="{PY(esik):.1f}" x2="{x1}" y2="{PY(esik):.1f}" class="spk-filtre"/>')
    p.append(txt(x1 - 4, PY(esik) - 4, "eşik −28 dB", "s-kucuk s-altin", "end"))
    t1 = time_walk(RISE, 10 ** (esik / 20)) * 1e9
    t2 = time_walk(RISE, 10 ** ((esik + 20) / 20)) * 1e9
    p.append(f'<path d="M{PX(t1):.1f} {PY(-34):.1f} H{PX(t2):.1f}" class="yol-gurultu" marker-end="url(#ok-gurultu)"/>')
    p.append(txt((PX(t1) + PX(t2)) / 2, PY(-34) - 5, f"Δ = {t2 - t1:.1f} ns", "s-mono2 s-kirmizi", "middle"))
    # sağ: eğri t_x(eşik/tepe)
    x0b, x1b, y0b, y1b = 500, 830, 200, 40
    xmin2, xmax2, ymin2, ymax2 = -40, 0, 0, 30
    p.append(eksen(x0b, x1b, y0b, y1b, [-40, -30, -20, -10, 0], [0, 10, 20, 30], xmin2, xmax2, ymin2, ymax2, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    p.append(txt((x0b + x1b) / 2, y0b + 30, "eşik / tepe (dB)", "s-kucuk", "middle"))
    p.append(txt(x0b - 40, (y0b + y1b) / 2, "TOA gecikmesi (ns)", "s-kucuk", "middle", f' transform="rotate(-90 {x0b - 40} {(y0b + y1b) / 2})"'))
    xs = [-40 + k * 0.25 for k in range(161)]
    ys = [time_walk(RISE, 10 ** (v / 20)) * 1e9 for v in xs]
    p.append(f'<path d="{path_from(xs, ys, x0b, x1b, y0b, y1b, xmin2, xmax2, ymin2, ymax2)}" class="yol-sayisal"/>')
    def PXb(v): return x0b + (v - xmin2) / (xmax2 - xmin2) * (x1b - x0b)
    def PYb(v): return y0b - (v - ymin2) / (ymax2 - ymin2) * (y0b - y1b)
    for v, ad in ((-28, "−28 dB → 6.4 ns"), (-8, "−8 dB → 21.7 ns"), (-6, "−6 dB (%50) → 25 ns")):
        t = time_walk(RISE, 10 ** (v / 20)) * 1e9
        p.append(f'<circle cx="{PXb(v):.1f}" cy="{PYb(t):.1f}" r="4" fill="var(--gold)"/>')
        p.append(txt(PXb(v) - 6, PYb(t) - 7, ad, "s-kucuk s-altin", "end"))
    p.append(f'<line x1="{x0b}" y1="{PYb(3.333):.1f}" x2="{x1b}" y2="{PYb(3.333):.1f}" class="yol-saat"/>')
    p.append(txt(x0b + 4, PYb(3.333) - 4, "1 örnek = 3.33 ns", "s-kucuk"))
    p.append(txt(x0b + 4, y1b + 14, "t_x = t_r/π · acos(1 − 2a)", "s-mono2"))
    p.append(txt(x0b + 4, y1b + 27, "a = genlik oranı, t_r = 50 ns", "s-kucuk"))
    # alt açıklama
    p.append(txt(70, 250, "Referans senaryo: eşik −68 dBm sabit. −60 dBm'lik darbe eşiği tepesinin −8 dB'sinde keser (21.7 ns), −40 dBm'lik darbe −28 dB'sinde (6.4 ns):", "s-metin2"))
    p.append(txt(70, 270, "aynı anda gelen iki darbenin TOA'sı 15.3 ns ≈ 4.6 örnek farklı okunur. Düzeltme: PA'ya bağlı tablo ya da %50 tepe noktasına göre TOA (kesirli).", "s-metin2"))
    # alt: PW etkisi küçük şerit
    p.append(txt(70, 305, "PW'ye etkisi (simetrik kenarlar): PW_ölçülen = PW_%50 + t_r − 2·t_x. Eşik tepenin −8 dB'sindeyse +6.6 ns, −28 dB'sindeyse +37.2 ns uzun okunur;", "s-metin2"))
    p.append(txt(70, 325, "histerezis düşen kenarı daha da geç kestirir (T_off = T_on − 3 dB → düşen kenarda birkaç ns daha).", "s-metin2"))
    p.append(txt(70, 360, "Sayılar kosinüs kenarlı öğretici darbe modeline aittir; gerçek kenar şekli farklıysa eğri değişir, mekanizma değişmez.", "s-kucuk"))
    return sarmala("g251", W, H, "Time walk: solda yükselen kenar yakınlaştırması, güçlü ve zayıf darbenin aynı sabit eşiği farklı anlarda kesmesi; sağda TOA gecikmesinin eşik/tepe oranına göre eğrisi, −28, −8 ve −6 dB noktaları ve bir örnek süresi çizgisi", "\n".join(p))


# ================================================================== g-252
def g252():
    W, H = 860, 540
    fs = FS
    t0 = 0.2e-6
    n = 420  # 1.4 µs
    pwGen = PW + RISE
    seri = [
        ("sabit taşıyıcı (f_bb = 5 MHz)", "yok", 0.0, "yol-sayisal", 11),
        ("LFM: 10 MHz / 1 µs, merkez 5 MHz", "lfm", CHIRP_BW, "yol-analog", 12),
        ("13-bit Barker (faz kodlu), 5 MHz", "barker13", 0.0, "yol-gurultu", 13),
    ]
    ts = [k / fs * 1e6 for k in range(n)]
    p = [txt(70, 22, "Darbe içi anlık frekans profili — MOP imzası (SNR = 25 dB, fs = 300 MSPS)", "s-baslik")]
    # üst: I(t) LFM ve sabit
    x0, x1, y0, y1 = 70, 830, 190, 40
    xmin, xmax = 0, 1.4
    p.append(eksen(x0, x1, y0, y1, [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4], [-1, 0, 1], xmin, xmax, -1.3, 1.3, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    p.append(txt(14, (y0 + y1) / 2, "I(t)", "s-kucuk", "middle", f' transform="rotate(-90 14 {(y0 + y1) / 2})"'))
    veriler = []
    for ad, mop, bw, kls, seed in seri:
        i, q = darbe(n, fs, pwGen, RISE, 5e6, mop=mop, bw=bw, t0=t0, snr_db=25, seed=seed)
        veriler.append((ad, mop, kls, i, q))
    # I(t): yalnızca LFM ve sabit üst panelde (okunurluk)
    for ad, mop, kls, i, q in veriler[:2]:
        p.append(f'<path d="{path_from(ts, i, x0, x1, y0, y1, xmin, xmax, -1.3, 1.3)}" class="{kls}" opacity=".85"/>')
    p.append(txt(x0 + 6, y1 + 14, "mavi: sabit taşıyıcı · altın: LFM (kenarlara doğru sıklaşan salınım)", "s-kucuk"))
    # alt: anlık frekans
    x0b, x1b, y0b, y1b = 70, 830, 420, 230
    ymin, ymax = -5, 15
    p.append(eksen(x0b, x1b, y0b, y1b, [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4], [-5, 0, 5, 10, 15], xmin, xmax, ymin, ymax, lambda v: f"{v:g}", lambda v: f"{v:g}"))
    p.append(txt((x0b + x1b) / 2, y0b + 30, "zaman (µs)", "s-kucuk", "middle"))
    p.append(txt(14, (y0b + y1b) / 2, "anlık frekans (MHz)", "s-kucuk", "middle", f' transform="rotate(-90 14 {(y0b + y1b) / 2})"'))
    bas, son = int(t0 * fs) + 1, int((t0 + pwGen) * fs) - 1
    ka, kb = bas + (son - bas) // 10, son - (son - bas) // 10
    def PX(t): return x0b + (t - xmin) / (xmax - xmin) * (x1b - x0b)
    def PY(v): return y0b - (v - ymin) / (ymax - ymin) * (y0b - y1b)
    p.append(f'<rect x="{PX(ts[ka]):.1f}" y="{y1b}" width="{PX(ts[kb]) - PX(ts[ka]):.1f}" height="{y0b - y1b}" class="spk-sinyal" opacity=".07"/>')
    sonuc = []
    for ad, mop, kls, i, q in veriler:
        af = anlik_frekans(i, q, fs)
        afm = [v / 1e6 for v in af]
        # darbe dışını çizme
        xs = ts[bas:son]
        ys = afm[bas:son]
        p.append(f'<path d="{path_from(xs, ys, x0b, x1b, y0b, y1b, xmin, xmax, ymin, ymax)}" class="{kls}" opacity=".9"/>')
        # ölçümler: ortalama ve eğim (kenarlar hariç)
        xs2 = [k / fs for k in range(ka, kb)]
        ys2 = af[ka:kb]
        nn = len(xs2)
        sx, sy = sum(xs2), sum(ys2)
        sxx = sum(x * x for x in xs2)
        sxy = sum(x * y for x, y in zip(xs2, ys2))
        egim = (nn * sxy - sx * sy) / (nn * sxx - sx * sx)
        sonuc.append((ad, sy / nn, egim))
    yy = y0b + 46
    for k, (ad, ort, egim) in enumerate(sonuc):
        renk = ("s-vurgu", "s-altin", "s-kirmizi")[k]
        p.append(txt(x0b, yy + k * 15, f"{ad}: pencere ortalaması {ort / 1e6:.2f} MHz · uydurulan eğim {egim / 1e12:+.2f} MHz/µs", f"s-kucuk {renk}"))
    p.append(txt(x0b, yy + 50, "LFM: doğrusal rampa 0 → 10 MHz, eğim = BW/PW = 10 MHz/µs (kenar dışlama rampanın uçlarını kırpar); ortalama yine 5 MHz.", "s-kucuk"))
    p.append(txt(x0b, yy + 64, "Faz kodlu: 180° atlama anlık frekansta ±fs/2'ye varan tek örneklik sivri uç üretir → 'faz atlaması' sayacı / bayrağı.", "s-kucuk"))
    return sarmala("g252", W, H, "Darbe içi anlık frekans profili: üstte sabit taşıyıcılı ve LFM darbenin I(t) dalga şekli; altta üç MOP tipinin anlık frekansı — sabit düz çizgi 5 MHz, LFM 0'dan 10 MHz'e doğrusal rampa, 13-bit Barker faz atlamalarında sivri uçlar; ölçüm penceresi ortalamaları ve eğimler", "\n".join(p))


# ================================================================== g-260
def g260():
    W, H = 940, 400
    p = [txt(30, 24, "Darbe durum makinesi (FSM) — her saatte bir güç örneği p[n], eşik T_on, T_off = T_on − histerezis", "s-baslik")]
    durumlar = [("IDLE", 90, 200), ("RISING", 280, 200), ("IN_PULSE", 470, 200), ("FALLING", 660, 200), ("EMIT", 850, 200)]
    r = 52
    for ad, cx, cy in durumlar:
        kls = "blok-aktif" if ad == "IN_PULSE" else ("blok-kontrol" if ad == "EMIT" else "blok")
        p.append(f'<rect x="{cx - r}" y="{cy - 26}" width="{2 * r}" height="52" rx="26" class="{kls}"/>')
        p.append(txt(cx, cy + 5, ad, "s-mono", "middle"))
    def ok(x1, y1, x2, y2, kls="yol-sayisal", m="ok-sayisal", d=None):
        d = d or f"M{x1} {y1} L{x2} {y2}"
        return f'<path d="{d}" class="{kls}" marker-end="url(#{m})"/>'
    # ileri geçişler
    p.append(ok(142, 200, 226, 200))
    p.append(txt(184, 190, "p > T_on", "s-mono2", "middle"))
    p.append(txt(184, 226, "TOA ← sayaç", "s-kucuk s-yesil", "middle"))
    p.append(ok(332, 200, 416, 200))
    p.append(txt(374, 190, "k_r örnek üstte", "s-mono2", "middle"))
    p.append(txt(374, 226, "tepe/faz biriktir", "s-kucuk s-yesil", "middle"))
    p.append(ok(522, 200, 606, 200))
    p.append(txt(564, 190, "p < T_off", "s-mono2", "middle"))
    p.append(txt(564, 226, "bitiş adayı ← sayaç", "s-kucuk s-yesil", "middle"))
    p.append(ok(712, 200, 796, 200))
    p.append(txt(754, 190, "k_f örnek altta", "s-mono2", "middle"))
    p.append(txt(754, 226, "PW = bitiş − TOA", "s-kucuk s-yesil", "middle"))
    # EMIT -> IDLE (alt yay)
    p.append(ok(0, 0, 0, 0, "yol-kontrol", "ok-kontrol", "M850 226 V300 H90 V232"))
    p.append(txt(470, 292, "PDW'yi paketle → FIFO'ya yaz (1 saat); SEQ++; PW < min PW ise at (çentik)", "s-kucuk s-yesil", "middle"))
    # IN_PULSE kendi döngüsü
    p.append(f'<path d="M450 174 C430 120, 510 120, 490 174" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    p.append(txt(470, 122, "p ≥ T_off: tepe = max, PA toplamı, Δfaz toplamı, örnek sayacı++", "s-kucuk", "middle"))
    # RISING -> IDLE (çentik) kırmızı
    p.append(ok(0, 0, 0, 0, "yol-gurultu", "ok-gurultu", "M262 174 C230 130, 150 130, 120 174"))
    p.append(txt(190, 150, "p < T_off (k_r dolmadan): gürültü sivrisi → at", "s-kucuk s-kirmizi", "middle"))
    # FALLING -> IN_PULSE (kenar çentiği)
    p.append(ok(0, 0, 0, 0, "yol-gurultu", "ok-gurultu", "M640 174 C610 130, 530 130, 500 174"))
    p.append(txt(568, 150, "p > T_on (k_f dolmadan): kenar çentiği → darbe sürüyor", "s-kucuk s-kirmizi", "middle"))
    # zaman aşımı: IN_PULSE -> EMIT (üst yay, uzun)
    p.append(ok(0, 0, 0, 0, "yol-kontrol", "ok-kontrol", "M470 174 V70 H850 V174"))
    p.append(txt(660, 62, "örnek sayacı ≥ MAX_PW: zaman aşımı → SEG bayraklı parça PDW yay, IN_PULSE'ta kal (CW / uzun darbe)", "s-kucuk s-yesil", "middle"))
    p.append(f'<path d="M870 174 V90 H500 V172" class="yol-kontrol" stroke-dasharray="4 3" marker-end="url(#ok-kontrol)"/>')
    # alt notlar
    p.append(txt(30, 336, "Register'lar: T_on (sabit eşik ya da CFAR eşiği) · DET_HYST (T_off) · DET_MIN_PW (çentik reddi) · DET_MAX_PW (zaman aşımı) · k_r / k_f (kenar doğrulama, 1–4 örnek)", "s-kucuk"))
    p.append(txt(30, 352, "Pulse-on-pulse: IN_PULSE içinde tepe ≥ 6 dB sıçrarsa ya da anlık frekans pencere ortalamasından koparsa POP bayrağı kalkar; ayrıştırma yazılımda.", "s-kucuk"))
    p.append(txt(30, 368, "Öğretici şema; gerçek tasarımlarda durum sayısı ve koşullar farklı olabilir. Yeşil: PDW'ye yazılan büyüklükler, kırmızı: reddedilen yollar.", "s-kucuk"))
    return sarmala("g260", W, H, "Darbe durum makinesi diyagramı: IDLE, RISING, IN_PULSE, FALLING, EMIT durumları; eşik geçişleri ve doğrulama sayaçlarıyla ileri geçişler; gürültü sivrisi ve kenar çentiği için geri dönüş yolları; MAX_PW zaman aşımında SEG bayraklı parça PDW yayımı; EMIT'ten IDLE'a PDW FIFO yazımı", "\n".join(p))


# ================================================================== g-261
def g261():
    W, H = 1120, 420
    p = [txt(20, 24, "PDW veri yolu — PL'de üretim, AXI-Stream + DMA ile PS'e taşıma (kurgusal register adları Bölüm 30 ile aynı)", "s-baslik")]
    def sym(ad, x, y, et, et2=None):
        s = f'<use href="#sym-{ad}" x="{x}" y="{y}" width="60" height="40"/>' + txt(x + 30, y + 54, et, "s-kucuk", "middle")
        if et2:
            s += txt(x + 30, y + 66, et2, "s-kucuk", "middle")
        return s
    def blok(x, y, w, h, et, kls="blok", et2=None):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" class="{kls}"/>' + txt(x + w / 2, y + h / 2 + (0 if et2 else 4), et, "s-metin", "middle")
        if et2:
            s += txt(x + w / 2, y + h / 2 + 14, et2, "s-mono2", "middle")
        return s
    def ok(d, kls="yol-sayisal", m="ok-sayisal"):
        return f'<path d="{d}" class="{kls}" marker-end="url(#{m})"/>'
    # giriş
    p.append(txt(20, 118, "DDC çıkışı", "s-kucuk"))
    p.append(txt(20, 130, "I/Q 300 MSPS", "s-kucuk"))
    # zaman kolu
    p.append(sym("zarf", 90, 100, "I²+Q²", "+ MA(4)"))
    p.append(ok("M150 120 H180"))
    p.append(sym("cmp", 180, 100, "eşik", "CFAR / sabit"))
    p.append(ok("M240 120 H270"))
    p.append(blok(270, 96, 96, 48, "darbe FSM", "blok-aktif", "TOA·PW·PA"))
    p.append(ok("M366 120 H396"))
    p.append(blok(396, 96, 96, 48, "ölçüm", "blok", "faz→f, eğim"))
    # frekans kolu
    p.append(sym("fft", 180, 230, "FFT 1024", "Hann, %50"))
    p.append(ok("M240 250 H270"))
    p.append(blok(270, 226, 96, 48, "tepe bulma", "blok", "bin → f_bb, BW"))
    p.append(ok("M366 250 H396"))
    p.append(blok(396, 226, 96, 48, "gecikme /", "blok", "TOA eşleme"))
    # DDC dalları
    p.append(ok("M60 120 H90"))
    p.append(f'<path d="M75 120 V250 H180" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    p.append(f'<path d="M75 250 V340 H180" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    # birleştirme
    p.append(ok("M492 120 H530 V170"))
    p.append(ok("M492 250 H530 V200"))
    p.append(blok(500, 170, 120, 30, "PDW birleştir", "blok-aktif"))
    p.append(ok("M620 185 H650"))
    p.append(blok(650, 165, 100, 40, "paketleyici", "blok", "4 × 32 bit"))
    p.append(ok("M750 185 H780"))
    p.append(sym("fifo", 780, 165, "PDW FIFO", "1024 × 128 b"))
    p.append(ok("M840 185 H880"))
    p.append(txt(860, 178, "AXI-Stream", "s-kucuk", "middle"))
    p.append(sym("dma", 880, 165, "DMA", "S2MM"))
    p.append(ok("M940 185 H990"))
    p.append(sym("cpu", 990, 165, "PS", "halka tampon"))
    # snapshot
    p.append(sym("gecikme", 180, 320, "ön-tetik", "SNAP_PRETRIG"))
    p.append(ok("M240 340 H270"))
    p.append(blok(270, 316, 130, 48, "snapshot RAM", "blok", "SNAP_LEN × 32 b"))
    p.append(f'<path d="M318 144 V316" class="yol-kontrol" stroke-dasharray="4 3" marker-end="url(#ok-kontrol)"/>')
    p.append(txt(326, 300, "ilk tespit → tetik", "s-kucuk s-yesil"))
    p.append(ok("M400 340 H910 V205"))
    p.append(txt(650, 334, "snapshot okuma (ikinci DMA kanalı)", "s-kucuk"))
    # PL / PS sınırı
    p.append(f'<line x1="965" y1="50" x2="965" y2="400" class="yol-saat"/>')
    p.append(txt(958, 62, "PL", "s-mono", "end"))
    p.append(txt(972, 62, "PS", "s-mono"))
    # register'lar (yeşil)
    p.append(sym("reg", 780, 60, "PDW_FIFO_LEVEL", "PDW_FIFO_CTRL"))
    p.append(f'<path d="M810 100 V165" class="yol-kontrol"/>')
    p.append(sym("reg", 660, 60, "PDW_DROP_CNT", "PDW_COUNT"))
    p.append(f'<path d="M690 100 V165" class="yol-kontrol"/>')
    p.append(sym("reg", 880, 60, "IRQ_STATUS", "IRQ_MASK"))
    p.append(ok("M940 80 H990", "yol-kontrol", "ok-kontrol"))
    p.append(txt(996, 64, "IRQ: FIFO yarım,", "s-kucuk s-yesil"))
    p.append(txt(996, 76, "taşma, snap hazır", "s-kucuk s-yesil"))
    p.append(f'<path d="M1020 160 V100" class="yol-kontrol" marker-end="url(#ok-kontrol)"/>')
    p.append(txt(1030, 130, "AXI-Lite", "s-kucuk s-yesil"))
    p.append(txt(1030, 142, "okuma/yazma", "s-kucuk s-yesil"))
    # taşma yolu
    p.append(f'<path d="M810 205 V236" class="yol-gurultu" marker-end="url(#ok-gurultu)"/>')
    p.append(txt(810, 252, "FIFO dolu → PDW at, DROP_CNT++, IRQ bit1", "s-kucuk s-kirmizi", "middle"))
    # notlar
    p.append(txt(20, 392, "Mavi: örnek/PDW verisi · yeşil: kontrol ve durum · kesikli: PL/PS sınırı. FIFO 128-bit sözcük başına bir PDW; DMA 4 KB'lik tanımlayıcılarla (32 PDW / tanımlayıcı) halka tampona yazar.", "s-kucuk"))
    p.append(txt(20, 408, "Zaman kolu (üst) ve frekans kolu (orta) farklı gecikmelerle çalışır; 'PDW birleştir' ikisini TOA ile eşler (Şekil g-262).", "s-kucuk"))
    return sarmala("g261", W, H, "PDW veri yolu PL'den PS'e: DDC çıkışı zaman koluna (güç zarfı, eşik karşılaştırıcı, darbe FSM, ölçüm) ve frekans koluna (FFT, tepe bulma, TOA eşleme) ayrılır; PDW birleştirici, paketleyici, 1024 derinlikli PDW FIFO, AXI-Stream, DMA ve PS halka tamponu; tetiklemeli snapshot RAM ikinci DMA kanalıyla; yeşil register'lar FIFO seviye, kontrol, drop sayacı, PDW sayacı ve kesme durumunu taşır", "\n".join(p))


# ================================================================== g-262
def g262():
    W, H = 900, 418
    p = [txt(30, 24, "İki kolun gecikmesi ve PDW birleştirme — referans darbe (1 µs), fs = 300 MSPS, FFT 1024 (3.41 µs çerçeve)", "s-baslik")]
    x0, x1 = 200, 860
    tmin, tmax = 0, 8.0
    def PX(t): return x0 + (t - tmin) / (tmax - tmin) * (x1 - x0)
    satirlar = ["giriş darbesi", "zarf + eşik", "FSM durumu", "faz → frekans", "FFT çerçeveleri", "FFT tepe hazır", "PDW birleştir", "FIFO'ya yaz"]
    y0 = 60
    dy = 38
    for k, ad in enumerate(satirlar):
        y = y0 + k * dy
        p.append(txt(x0 - 10, y + 18, ad, "s-metin2", "end"))
        p.append(f'<line x1="{x0}" y1="{y + 30}" x2="{x1}" y2="{y + 30}" class="izgara"/>')
    # eksen
    for t in range(0, 9):
        p.append(f'<line x1="{PX(t):.1f}" y1="{y0 - 6}" x2="{PX(t):.1f}" y2="{y0 + 8 * dy}" class="izgara"/>')
        p.append(txt(PX(t), y0 + 8 * dy + 14, f"{t}", "s-mono2", "middle"))
    p.append(txt((x0 + x1) / 2, y0 + 8 * dy + 30, "zaman (µs) — darbe t = 1.0 µs'de başlar", "s-kucuk", "middle"))
    tb, te = 1.0, 2.0
    lat_zaman = 0.1   # zarf + MA + CFAR penceresi ≈ 30 örnek
    def bant(satir, ta, tb_, kls, et=None, etkls="s-kucuk", sag=None):
        y = y0 + satir * dy + 4
        s = f'<rect x="{PX(ta):.1f}" y="{y}" width="{max(2, PX(tb_) - PX(ta)):.1f}" height="22" rx="3" class="{kls}"/>'
        if et:
            s += txt((PX(ta) + PX(tb_)) / 2, y + 15, et, etkls, "middle")
        if sag:
            s += txt(PX(tb_) + 8, y + 15, sag, etkls)
        return s
    p.append(bant(0, tb, te, "blok-aktif", "1 µs"))
    p.append(bant(1, tb + lat_zaman, te + lat_zaman, "blok-aktif", None, "s-kucuk", "gecikme ≈ 0.1 µs (≈ 30 örnek: zarf + MA + CFAR penceresi)"))
    p.append(bant(2, tb + lat_zaman, tb + lat_zaman + 0.05, "blok"))
    p.append(bant(2, tb + lat_zaman + 0.05, te + lat_zaman, "blok-aktif", "IN_PULSE"))
    p.append(bant(2, te + lat_zaman, te + lat_zaman + 0.06, "blok"))
    p.append(bant(2, te + lat_zaman + 0.06, te + lat_zaman + 0.1, "blok-kontrol"))
    p.append(txt(PX(te + lat_zaman + 0.14), y0 + 2 * dy + 19, "EMIT (t ≈ 2.2 µs): TOA, PW, PA hazır", "s-kucuk s-yesil"))
    p.append(bant(3, tb + lat_zaman, te + lat_zaman, "blok-analog", "Δφ biriktir", "s-kucuk", "→ darbe bitince f hazır (t ≈ 2.1 µs)"))
    # FFT çerçeveleri %50 overlap: 3.41 µs, adım 1.71
    frame = 1024 / FS * 1e6
    k = 0
    while k * frame / 2 < tmax:
        ta = k * frame / 2
        y = y0 + 4 * dy + 4 + (0 if k % 2 == 0 else 11)
        kapsar = ta <= tb and ta + frame >= te
        p.append(f'<rect x="{PX(ta):.1f}" y="{y}" width="{PX(min(tmax, ta + frame)) - PX(ta):.1f}" height="10" rx="2" class="{"blok-aktif" if kapsar else "blok"}"/>')
        k += 1
    p.append(txt(PX(0.05), y0 + 4 * dy - 2, "çerçeve 3.41 µs, adım 1.71 µs; darbeyi tam kapsayan çerçeve mavi", "s-kucuk"))
    # FFT tepe hazır: kapsayan çerçeve bitişi + pipeline (~1024 + 100 saat ≈ 3.7 µs)
    kaps_bitis = frame  # çerçeve 0 (0–3.41) darbeyi kapsar
    fft_hazir = kaps_bitis + (1024 + 100) / FS * 1e6
    p.append(bant(5, fft_hazir, fft_hazir + 0.08, "blok-analog"))
    p.append(txt(PX(fft_hazir) - 8, y0 + 5 * dy + 19, f"f_bb, BW hazır: kapsayan çerçevenin bitişi + ~1124 saat boru hattı → t ≈ {fft_hazir:.1f} µs", "s-kucuk s-altin", "end"))
    # birleştir: bekleme
    p.append(bant(6, te + lat_zaman + 0.1, fft_hazir, "blok", "zaman kolu PDW'si bekleme kuyruğunda (TOA anahtarıyla)"))
    p.append(bant(6, fft_hazir, fft_hazir + 0.08, "blok-kontrol"))
    p.append(bant(7, fft_hazir + 0.08, fft_hazir + 0.16, "blok-kontrol"))
    p.append(txt(PX(fft_hazir) - 8, y0 + 7 * dy + 19, f"PDW FIFO'da: darbe bitiminden ≈ {fft_hazir - te:.1f} µs sonra", "s-kucuk s-yesil", "end"))
    # açıklama
    p.append(txt(30, 408, "Frekans kolu kullanılmıyorsa PDW t ≈ 2.2 µs'de çıkar; FFT kolu eklenince gecikme çerçeve + boru hattı kadar uzar, eşleştirme penceresi gerekir.", "s-kucuk"))
    return sarmala("g262", W, H, "İki kolun latency hizalaması: giriş darbesi 1–2 µs; zarf ve eşik yaklaşık 0.1 µs gecikmeyle; FSM IN_PULSE ve EMIT; faz tabanlı frekans darbe bitiminde hazır; yüzde 50 örtüşen 3.41 µs FFT çerçeveleri; FFT tepesi kapsayan çerçeve bitişi ve boru hattı sonrası hazır; PDW birleştirici zaman kolu sonucunu bekletip TOA ile eşler ve FIFO'ya yazar", "\n".join(p))


# ================================================================== g-270
def g270():
    W, H = 900, 460
    rnd = LCG(5)
    # üç kurgusal emiter: (RF GHz, PRI ms, PW µs, stagger listesi)
    emit = [
        ("A", 9.40, [1.00], 1.0, "spk-sinyal"),
        ("B", 9.12, [0.62, 0.78], 2.5, "spk-image"),
        ("C", 9.66, [0.31], 0.4, "spk-filtre"),
    ]
    T = 10.0  # ms
    pdwler = []
    for ad, rf, pri, pw, kls in emit:
        t = rnd.u() * pri[0]
        k = 0
        while t < T:
            pdwler.append((t, rf + rnd.g(0.004), ad))
            t += pri[k % len(pri)]
            k += 1
    # birkaç sahte / kayıp
    pdwler = [x for x in pdwler if rnd.u() > 0.05]
    pdwler.sort()
    p = [txt(30, 22, "PDW'den sonrası: karışık akış → PRI histogramı → emiter izleri (üç kurgusal emiter, 10 ms)", "s-baslik")]
    # üst: TOA – RF saçılımı (hepsi aynı renk: almaç bilmez)
    x0, x1, y0, y1 = 70, 860, 170, 40
    p.append(eksen(x0, x1, y0, y1, [0, 2, 4, 6, 8, 10], [9.0, 9.2, 9.4, 9.6, 9.8], 0, T, 8.95, 9.85, lambda v: f"{v:g}", lambda v: f"{v:.1f}"))
    p.append(txt(14, (y0 + y1) / 2, "RF (GHz)", "s-kucuk", "middle", f' transform="rotate(-90 14 {(y0 + y1) / 2})"'))
    p.append(txt((x0 + x1) / 2, y0 + 28, "TOA (ms) — almaçtan çıkan haliyle: kimin darbesi olduğu bilinmiyor", "s-kucuk", "middle"))
    def PX(t): return x0 + t / T * (x1 - x0)
    def PY(f): return y0 - (f - 8.95) / (9.85 - 8.95) * (y0 - y1)
    for t, f, ad in pdwler:
        p.append(f'<circle cx="{PX(t):.1f}" cy="{PY(f):.1f}" r="2.6" class="spk-sinyal"/>')
    p.append(txt(x1 - 6, y1 + 14, f"{len(pdwler)} PDW", "s-mono2", "end"))
    # alt sol: ΔTOA histogramı (ardışık farklar + 2. mertebe farklar — SDIF fikri)
    x0b, x1b, y0b, y1b = 70, 420, 400, 230
    dmax = 1.2
    kova = [0] * 60
    toas = [t for t, _, _ in pdwler]
    for a in range(len(toas)):
        for b in range(a + 1, min(a + 4, len(toas))):  # 1., 2., 3. mertebe farklar
            d = toas[b] - toas[a]
            if d < dmax:
                kova[int(d / dmax * 60)] += 1
    mx = max(kova)
    p.append(eksen(x0b, x1b, y0b, y1b, [0, 0.3, 0.6, 0.9, 1.2], [], 0, dmax, 0, mx * 1.15, lambda v: f"{v:g}"))
    p.append(txt((x0b + x1b) / 2, y0b + 28, "ΔTOA (ms) — 1.–3. mertebe farkların histogramı", "s-kucuk", "middle"))
    p.append(txt(x0b - 40, (y0b + y1b) / 2, "sayı", "s-kucuk", "middle", f' transform="rotate(-90 {x0b - 40} {(y0b + y1b) / 2})"'))
    bw = (x1b - x0b) / 60
    for k, c in enumerate(kova):
        if c:
            h = c / (mx * 1.15) * (y0b - y1b)
            p.append(f'<rect x="{x0b + k * bw:.1f}" y="{y0b - h:.1f}" width="{bw - 1:.1f}" height="{h:.1f}" class="spk-sinyal" opacity=".8"/>')
    for d, et in ((0.31, "C: 0.31"), (0.62, "B: 0.62 / 0.78"), (1.0, "A: 1.00")):
        p.append(txt(x0b + d / dmax * (x1b - x0b), y1b + 12 + (0 if d != 0.62 else 12), et, "s-kucuk s-altin", "middle"))
    p.append(txt(x0b + 4, y0b - 6, "tepeler aday PRI'ler; alt harmonikler (2·PRI…) elenir", "s-kucuk"))
    # alt sağ: emiter izleri
    x0c, x1c, y0c, y1c = 500, 860, 400, 230
    p.append(f'<rect x="{x0c}" y="{y1c}" width="{x1c - x0c}" height="{y0c - y1c}" class="eksen"/>')
    p.append(txt((x0c + x1c) / 2, y0c + 28, "TOA (ms) — emiter izlerine ayrılmış", "s-kucuk", "middle"))
    for k, (ad, rf, pri, pw, kls) in enumerate(emit):
        yy = y1c + 30 + k * 52
        p.append(txt(x0c + 6, yy - 12, f"Emiter {ad} (kurgusal): RF {rf:.2f} GHz · PRI {' / '.join(f'{v:.2f}' for v in pri)} ms{' (stagger)' if len(pri) > 1 else ''} · PW {pw:.1f} µs", "s-kucuk"))
        p.append(f'<line x1="{x0c}" y1="{yy}" x2="{x1c}" y2="{yy}" class="izgara"/>')
        for t, f, a in pdwler:
            if a == ad:
                px = x0c + t / T * (x1c - x0c)
                p.append(f'<rect x="{px - 1.5:.1f}" y="{yy - 8}" width="3" height="16" class="{kls}"/>')
    p.append(txt(30, 436, "Süreç yazılımdadır: PDW'ler (RF, PW, AOA) kümelenir; küme içinde ΔTOA histogramı PRI adaylarını verir; aday PRI ile darbe dizisi çıkarılır,", "s-kucuk"))
    p.append(txt(30, 450, "kalanlarla işlem yinelenir; iz güncellenir ve kütüphaneyle eşlenir.", "s-kucuk"))
    return sarmala("g270", W, H, "Karışık PDW akışından emiter izlerine: üstte 10 ms boyunca TOA–RF saçılımı olarak karışık PDW akışı; sol altta ardışık TOA farklarının histogramı ve PRI adayı tepeleri; sağ altta üç kurgusal emiterin ayrılmış darbe dizileri", "\n".join(p))


URETICILER = {
    "g-240-pdw-bit-haritasi.svg": g240,
    "g-241-indirgeme.svg": g241,
    "g-242-alan-bit-butcesi.svg": g242,
    "g-250-olcu-noktalari.svg": g250,
    "g-251-time-walk.svg": g251,
    "g-252-anlik-frekans-profili.svg": g252,
    "g-260-darbe-fsm.svg": g260,
    "g-261-pdw-veri-yolu.svg": g261,
    "g-262-latency-hizalama.svg": g262,
    "g-270-pdw-sonrasi.svg": g270,
}


def main():
    sec = sys.argv[1] if len(sys.argv) > 1 else None
    for ad, fn in URETICILER.items():
        if sec and not ad.startswith(sec):
            continue
        yaz(ad, fn())


if __name__ == "__main__":
    main()
