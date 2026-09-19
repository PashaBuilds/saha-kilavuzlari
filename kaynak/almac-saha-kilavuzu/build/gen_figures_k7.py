#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k7.py — Kısım VII (Bölüm 21–23) hesaplanmış şekil üreticisi

gen_figures.py'deki yardımcıları (eksen, path_from) yeniden kullanır; dsp-core.js'teki
tespit/CFAR modellerinin Python eşdeğerleri buradadır (ca_cfar_alfa, os_cfar_alfa, cfar,
kayan_ortalama, rayleigh_esik). Üretilen dosyalar repoda commit'li durur.

  python build/gen_figures_k7.py            # tüm K7 şekilleri
  python build/gen_figures_k7.py g-232      # yalnızca biri
  python build/gen_figures_k7.py --dogrula  # yalnızca sayısal doğrulama çıktısı

Üretilenler: g-222 (video filtre), g-232 (CFAR ailesi sahnesi).
g-210/211/212/220/221/231 önceki üretimden korunmuştur (değerleri --dogrula ile
yeniden hesaplanıp karşılaştırılır); g-230 ve g-233 elle çizilmiş şemalardır.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_figures import eksen, path_from, S, SVG  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

T = S["tespit"]
PFA = T["pfa"]
N_REF = T["n_ref"]
GUARD = T["guard"]


# ------------------------------------------------------------------ DSP eşdeğerleri
def rayleigh_esik(pfa):
    return math.sqrt(-2 * math.log(pfa))


def ca_cfar_alfa(N, pfa):
    return N * (pfa ** (-1.0 / N) - 1)


def os_cfar_alfa(N, k, pfa):
    def f(a):
        p = 1.0
        for i in range(k):
            p *= (N - i) / (N - i + a)
        return p
    lo, hi = 0.0, 1e4
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > pfa:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def kayan_ortalama(x, L):
    y, s = [], 0.0
    for k, v in enumerate(x):
        s += v
        if k >= L:
            s -= x[k - L]
        y.append(s / min(L, k + 1))
    return y


def cfar(guc, tip, N, G, alfa, k=None):
    """DSP.cfar eşdeğeri: eşik = α × hücre başına gürültü kestirimi."""
    n = len(guc)
    yarim = N // 2
    esik, tespit = [0.0] * n, [0] * n
    for c in range(n):
        sol = [guc[c - G - j] for j in range(1, yarim + 1) if c - G - j >= 0]
        sag = [guc[c + G + j] for j in range(1, yarim + 1) if c + G + j < n]
        if tip == "OS":
            t = sorted(sol + sag)
            kk = k or round(0.75 * N)
            z = t[min(len(t) - 1, max(0, kk - 1))]
        elif tip == "GO":
            z = max(sum(sol) / len(sol) if sol else 0, sum(sag) / len(sag) if sag else 0)
        elif tip == "SO":
            z = min(sum(sol) / len(sol) if sol else 0, sum(sag) / len(sag) if sag else 0)
        else:
            z = (sum(sol) + sum(sag)) / max(1, len(sol) + len(sag))
        esik[c] = alfa * z
        tespit[c] = 1 if guc[c] > esik[c] else 0
    return esik, tespit


def ustel_gurultu(n, ortalama, rnd):
    """Kare-yasa zarfın gürültüsü: kompleks Gauss → güç üstel dağılımlı (ortalama = 2σ²)."""
    return [rnd.expovariate(1.0 / ortalama) for _ in range(n)]


def kompleks_darbe_gucu(n, rnd, gurultu, darbeler):
    """gurultu: hücre başına ortalama gürültü gücü listesi; darbeler: [(bas, uzunluk, snr_db, rise)]
    Kompleks Gauss gürültü + sabit genlikli (rastgele fazlı) darbe → I²+Q²."""
    guc = []
    zarf = [0.0] * n
    for bas, uz, snr_db, rise in darbeler:
        A = math.sqrt(10 ** (snr_db / 10) * gurultu[bas])  # genlik: SNR × yerel gürültü gücü
        for k in range(uz):
            v = 1.0
            if rise and k < rise:
                v = 0.5 - 0.5 * math.cos(math.pi * k / rise)
            elif rise and k >= uz - rise:
                v = 0.5 - 0.5 * math.cos(math.pi * (uz - k) / rise)
            if bas + k < n:
                zarf[bas + k] = A * v
    for k in range(n):
        s = math.sqrt(gurultu[k] / 2)
        i = rnd.gauss(0, s) + zarf[k] * math.cos(0.7 * k)
        q = rnd.gauss(0, s) + zarf[k] * math.sin(0.7 * k)
        guc.append(i * i + q * q)
    return guc


def db(x):
    return 10 * math.log10(max(x, 1e-12))


def fmt_int(v):
    return f"{int(v):d}"


# ------------------------------------------------------------------ g-222
def g_222():
    """Video filtre (kayan ortalama) uzunluğunun darbe kenarına ve gürültüye etkisi."""
    rnd = random.Random(222)
    n_on = 4096          # yalnız gürültü: std ölçümü için uzun parça
    bas, pw, rise = 200, S["ddc"]["darbe_ornek_sayisi"], 15
    snr_db = T["tespit_snr_db"]
    n = 700
    gur = [1.0] * max(n, n_on)
    guc_uzun = kompleks_darbe_gucu(n_on, rnd, gur, [])             # std ölçümü
    guc = kompleks_darbe_gucu(n, random.Random(2222), gur, [(bas, pw, snr_db, rise)])
    Ls = [1, 4, 16, 64]
    esik = -math.log(PFA)  # kare-yasa, L = 1 için eşik / ortalama gürültü gücü = 13.8
    W, H = 860, 345
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-g222">',
           '<title id="t-g222">Video filtre (kayan ortalama) uzunluğunun darbe kenarına etkisi: solda 300 örneklik, '
           '15 örnek yükselişli, 15 dB SNR\'lı darbenin ön kenarı L = 1, 4, 16, 64 için; sağda bütün darbe L = 1 ve 16; '
           'gürültü standart sapması 1/√L ile düşerken kenar L−1 örnek yayılır ve gecikir</title>']
    # sol panel: ön kenar
    x0, x1, y0, y1 = 60, 440, 270, 40
    xmin, xmax, ymin, ymax = 170, 300, 0, 25
    out.append(eksen(x0, x1, y0, y1, [180, 200, 220, 240, 260, 280, 300], [0, 5, 10, 15, 20, 25], xmin, xmax, ymin, ymax, fmt_int, fmt_int))
    out.append(f'<text x="{x0}" y="{y1 - 10}" class="s-baslik">Ön kenar: filtre uzadıkça kenar yayılır ve gecikir</text>')
    out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">örnek (3.33 ns)</text>')
    out.append(f'<text x="{x0 - 44}" y="{(y0 + y1) / 2}" transform="rotate(-90 {x0 - 44} {(y0 + y1) / 2})" text-anchor="middle" class="s-kucuk">güç (gürültü ort. = 1)</text>')
    # gerçek TOA
    px = x0 + (bas - xmin) / (xmax - xmin) * (x1 - x0)
    out.append(f'<line x1="{px:.1f}" y1="{y1}" x2="{px:.1f}" y2="{y0}" class="yol-saat"/>'
               f'<text x="{px + 4:.1f}" y="{y1 + 14}" class="s-kucuk">gerçek TOA</text>')
    # eşik
    py = y0 - (esik - ymin) / (ymax - ymin) * (y0 - y1)
    out.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" class="spk-filtre"/>'
               f'<text x="{x1 - 4}" y="{py - 5:.1f}" text-anchor="end" class="s-kucuk s-altin">eşik {esik:.1f} (Pfa 10⁻⁶, L = 1 için)</text>')
    stiller = [("var(--ink-3)", 1.0, ".7"), ("var(--accent)", 1.4, "1"), ("var(--purple)", 1.6, "1"), ("var(--red)", 1.6, "1")]
    xs = list(range(n))
    stdler = {}
    for L, (renk, kal, op) in zip(Ls, stiller):
        y = kayan_ortalama(guc, L)
        yu = kayan_ortalama(guc_uzun, L)
        parca = yu[256:]
        m = sum(parca) / len(parca)
        stdler[L] = math.sqrt(sum((v - m) ** 2 for v in parca) / len(parca))
        d = path_from(xs, y, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}" fill="none" stroke="{renk}" stroke-width="{kal}" opacity="{op}"/>')
    # sağ panel: bütün darbe, L=1 ve L=16
    x0b, x1b = 500, 840
    xminb, xmaxb = 0, 700
    out.append(eksen(x0b, x1b, y0, y1, [0, 200, 400, 600], [0, 5, 10, 15, 20, 25], xminb, xmaxb, ymin, ymax, fmt_int, fmt_int))
    out.append(f'<text x="{x0b}" y="{y1 - 10}" class="s-baslik">Bütün darbe (300 örnek): gürültü platoda ve tabanda sakinleşir</text>')
    out.append(f'<text x="{(x0b + x1b) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">örnek</text>')
    for L, renk, kal, op in ((1, "var(--ink-3)", 1.0, ".7"), (16, "var(--purple)", 1.5, "1")):
        y = kayan_ortalama(guc, L)
        d = path_from(xs, y, x0b, x1b, y0, y1, xminb, xmaxb, ymin, ymax)
        out.append(f'<path d="{d}" fill="none" stroke="{renk}" stroke-width="{kal}" opacity="{op}"/>')
    # lejant
    ly = 290
    for i, (L, (renk, kal, op)) in enumerate(zip(Ls, stiller)):
        lx = 60 + i * 200
        out.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 22}" y2="{ly}" stroke="{renk}" stroke-width="2"/>'
                   f'<text x="{lx + 28}" y="{ly + 4}" class="s-kucuk">L = {L} · std ölç. {stdler[L]:.2f} (teori 1/√L = {1 / math.sqrt(L):.2f}) · kenar +{L - 1}</text>')
    out.append(f'<text x="60" y="318" class="s-metin2">Kayan ortalama gürültü varyansını L kat düşürür (std: 1 → 1/√L) ama L−1 örneklik kenar yayılması ve (L−1)/2 örnek gecikme ekler;</text>')
    out.append(f'<text x="60" y="334" class="s-metin2">L = 64, 15 örneklik gerçek yükselişi ≈ 79 örneğe (≈ 260 ns) uzatır. Referans senaryo L = {T["video_filtre_uzunluk"]}: std yarıya iner, kenar 3 örnek (10 ns) yayılır.</text>')
    out.append("</svg>")
    (SVG / "g-222-video-filtre.svg").write_text("\n".join(out), encoding="utf-8")
    print("  ✓ g-222-video-filtre.svg  std:", {L: round(v, 3) for L, v in stdler.items()})


# ------------------------------------------------------------------ g-232
def g_232():
    """CA / GO / SO / OS-CFAR aynı sahnede: iki yakın darbe, yalnız darbe, +8 dB gürültü basamağı ve basamak içinde darbe."""
    n = 720
    basamak = 420
    gur = [1.0 if k < basamak else 10 ** 0.8 for k in range(n)]
    darbeler = [(150, 3, 20, 0), (159, 3, 20, 0), (300, 3, 20, 0), (600, 3, 20, 0)]
    guc = kompleks_darbe_gucu(n, random.Random(232), gur, darbeler)
    alfa_ca = ca_cfar_alfa(N_REF, PFA)
    k_os = 12
    alfa_os = os_cfar_alfa(N_REF, k_os, PFA)
    paneller = [("CA", "CA — ortalama: yakın komşu eşiği şişirir (maskeleme)", alfa_ca),
                ("GO", "GO — büyük yarı: basamak kenarında temiz, maskeleme en kötü", alfa_ca),
                ("SO", "SO — küçük yarı: maskelemeyi çözer, basamak kenarında yanlış alarm", alfa_ca),
                ("OS", f"OS — {k_os}. sıra istatistiği: ikisini de büyük ölçüde çözer", alfa_os)]
    W, H = 860, 470
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-g232">',
           '<title id="t-g232">CA, GO, SO ve OS-CFAR\'ın aynı sahnedeki davranışı: iki yakın 3 hücrelik darbe (6 hücre ara, 20 dB), '
           'yalnız bir darbe, 420. hücrede +8 dB gürültü basamağı ve basamağın içinde bir darbe; her panelde güç gri, eşik altın kesikli, '
           'tespit mavi, yanlış alarm kırmızı; CA ve GO yakın çifti maskeler, SO basamak kenarında yanlış alarm verir, OS ikisini de büyük ölçüde çözer</title>']
    xmin, xmax, ymin, ymax = 0, n, -10, 30
    xs = list(range(n))
    gdb = [db(v) for v in guc]
    darbe_hucre = set()
    for bas, uz, _, _ in darbeler:
        darbe_hucre.update(range(bas, bas + uz))
    ozet = {}
    for i, (tip, ad, alfa) in enumerate(paneller):
        col, row = i % 2, i // 2
        x0 = 60 + col * 420
        x1 = x0 + 360
        y1 = 36 + row * 200
        y0 = y1 + 140
        esik, tespit = cfar(guc, tip, N_REF, GUARD, alfa, k_os)
        xt = [0, 200, 400, 600] if row == 1 else []
        out.append(eksen(x0, x1, y0, y1, xt, [-10, 0, 10, 20, 30], xmin, xmax, ymin, ymax, fmt_int, fmt_int))
        out.append(f'<text x="{x0}" y="{y1 - 8}" class="s-baslik">{ad}</text>')
        if row == 1:
            out.append(f'<text x="{(x0 + x1) / 2}" y="{y0 + 30}" text-anchor="middle" class="s-kucuk">hücre</text>')
        if col == 0:
            out.append(f'<text x="{x0 - 40}" y="{(y0 + y1) / 2}" transform="rotate(-90 {x0 - 40} {(y0 + y1) / 2})" text-anchor="middle" class="s-kucuk">dB</text>')
        # basamak bandı
        bx = x0 + basamak / n * (x1 - x0)
        out.append(f'<rect x="{bx:.1f}" y="{y1}" width="{x1 - bx:.1f}" height="{y0 - y1}" fill="var(--red)" opacity=".06"/>')
        # güç (gri dolgu)
        d = path_from(xs, gdb, x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{d}L{x1} {y0}L{x0} {y0}Z" class="spk-gurultu"/>')
        # eşik (altın kesikli)
        de = path_from(xs, [db(v) for v in esik], x0, x1, y0, y1, xmin, xmax, ymin, ymax)
        out.append(f'<path d="{de}" class="spk-filtre" fill="none"/>')
        # tespit / yanlış alarm işaretleri
        d_say = {bas: 0 for bas, _, _, _ in darbeler}
        ya = 0
        for c in range(n):
            if not tespit[c]:
                continue
            px = x0 + c / n * (x1 - x0)
            py = y0 - (max(ymin, min(ymax, gdb[c])) - ymin) / (ymax - ymin) * (y0 - y1)
            if c in darbe_hucre:
                for bas, uz, _, _ in darbeler:
                    if bas <= c < bas + uz:
                        d_say[bas] += 1
                out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="var(--accent)"/>')
            else:
                ya += 1
                out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="var(--red)"/>')
        ozet[tip] = (d_say, ya)
        say_txt = " · ".join(f"{d_say[b]}/3" for b, _, _, _ in darbeler)
        out.append(f'<text x="{x0 + 4}" y="{y0 - 6}" class="s-kucuk">α = {alfa:.1f} · darbe hücreleri (çift-1, çift-2, yalnız, basamakta): {say_txt}</text>')
        out.append(f'<text x="{x1 - 4}" y="{y1 + 14}" text-anchor="end" class="s-kucuk {"s-kirmizi" if ya else "s-yesil"}">yanlış alarm: {ya}</text>')
        if i == 0:
            px = x0 + 155 / n * (x1 - x0)
            out.append(f'<text x="{px:.1f}" y="{y1 + 30}" text-anchor="middle" class="s-kucuk s-vurgu">iki yakın darbe (6 hücre ara)</text>')
            out.append(f'<text x="{bx + 4:.1f}" y="{y0 - 20}" class="s-kucuk s-kirmizi">+8 dB basamak</text>')
    out.append(f'<text x="60" y="{H - 24}" class="s-metin2">Aynı sahne, aynı N = {N_REF}, G = {GUARD}, Pfa = 10⁻⁶. Mavi nokta = darbe hücresinde tespit, kırmızı = gürültü hücresinde yanlış alarm.</text>')
    out.append(f'<text x="60" y="{H - 8}" class="s-metin2">Yakın çift CA/GO\'da birbirini maskeler; SO basamağın hemen sağında "küçük yarı"yı seçip alarm üretir; OS her ikisine de dayanıklıdır (bedeli sıralama ağı).</text>')
    out.append("</svg>")
    (SVG / "g-232-cfar-ailesi-sahne.svg").write_text("\n".join(out), encoding="utf-8")
    print("  ✓ g-232-cfar-ailesi-sahne.svg ", {k: (list(v[0].values()), v[1]) for k, v in ozet.items()})


# ------------------------------------------------------------------ doğrulama
def dogrula():
    print("  Rayleigh eşik (Pfa=1e-6):", round(rayleigh_esik(PFA), 3), "σ  beklenen", T["esik_rayleigh_sigma"])
    print("  CA-CFAR α (N=16):", round(ca_cfar_alfa(N_REF, PFA), 2), " beklenen", T["alfa_ca"])
    print("  OS-CFAR α (N=16, k=12):", round(os_cfar_alfa(N_REF, 12, PFA), 2))
    print("  kare-yasa eşik / ort. gürültü gücü (L=1): −ln Pfa =", round(-math.log(PFA), 2), "→", round(db(-math.log(PFA)), 1), "dB")
    print("  CFAR kaybı N=16:", round(db(ca_cfar_alfa(N_REF, PFA) / -math.log(PFA)), 2), "dB")
    for N in (8, 16, 32, 64):
        print(f"    N={N:3d}: α={ca_cfar_alfa(N, PFA):6.2f}  kayıp={db(ca_cfar_alfa(N, PFA) / -math.log(PFA)):.2f} dB")
    print("  FAR = Pfa × karar/s =", PFA * S["ddc"]["cikis_fs_msps"] * 1e6, "/s")
    print("  Rician tepe (13.2 dB): A/σ = √(2·SNR) =", round(math.sqrt(2 * 10 ** 1.32), 2))


URETICILER = {"g-222": g_222, "g-232": g_232}


def main():
    args = sys.argv[1:]
    if "--dogrula" in args:
        dogrula()
        return 0
    secim = args or list(URETICILER)
    for ad in secim:
        if ad not in URETICILER:
            print(f"  ? bilinmeyen: {ad}")
            continue
        URETICILER[ad]()
    dogrula()
    return 0


if __name__ == "__main__":
    sys.exit(main())
