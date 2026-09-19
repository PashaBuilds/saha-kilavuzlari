#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures_k2.py — Kısım II (Bölüm 5, 6, 7) şekil üreticisi (yalnızca stdlib)

Blok şemalar ortak sembol kütüphanesinden (`<use href="#sym-…">`) kurulur;
spektrum ve eğri verileri scenario.json'dan beslenen kısa hesaplarla üretilir
(Friis kaskadı, IP3 kaskadı, mixer çarpım/spur haritası). Renkler yalnızca
CSS değişkeni; ok uçları belgede gömülü ortak marker'lar.

  python build/gen_figures_k2.py            # hepsini yaz
  python build/gen_figures_k2.py g-52 g-62  # seçilenleri yaz

Üretilenler: g-50, g-51, g-52 (B5) · g-60, g-61, g-62 (B6) ·
             g-70 … g-79, g-7a, g-7b (B7)
"""
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

# ------------------------------------------------------------------ kurgusal doğrusallık bütçesi
# scenario.json'da yalnızca kazanç/NF var; P1dB ve OIP3 değerleri öğretici (kurgusal) bütçedir.
OIP3 = {"LNA": 25.0, "Mixer": 15.0, "IF yükselteç": 38.0, "AAF + sürücü": 36.0}
OP1DB = {"LNA": 15.0, "Mixer": 5.0, "IF yükselteç": 28.0, "AAF + sürücü": 26.0}


def lin(db):
    return 10 ** (db / 10)


def db(x):
    return 10 * math.log10(x)


def friis(bloklar):
    F, G, adim = 0.0, 1.0, []
    for i, b in enumerate(bloklar):
        f, g = lin(b["nf_db"]), lin(b["kazanc_db"])
        F = f if i == 0 else F + (f - 1) / G
        G *= g
        adim.append((db(F), db(G)))
    return adim


def ip3_kaskad(bloklar):
    """Giriş referanslı toplam IIP3 (dBm) ve blok başına giriş referanslı IIP3 listesi."""
    inv, Gb, liste = 0.0, 0.0, []
    for b in bloklar:
        o = OIP3.get(b["ad"])
        if o is not None:
            r = o - b["kazanc_db"] - Gb
            inv += 1 / lin(r)
            liste.append((b["ad"], r))
        Gb += b["kazanc_db"]
    return db(1 / inv), liste


# ------------------------------------------------------------------ SVG yardımcıları
def svg(fid, W, H, title, body):
    tid = "t-" + fid.replace("-", "")
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{tid}">\n'
            f'<title id="{tid}">{title}</title>\n{body}\n</svg>')


def yaz(fid, ad, W, H, title, parcalar):
    (SVG / f"{fid}-{ad}.svg").write_text(svg(fid, W, H, title, "\n".join(parcalar)), encoding="utf-8")
    print(f"  ✓ {fid}-{ad}.svg")


def metin(x, y, t, cls="s-kucuk", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="{cls}"{extra}>{t}</text>'


def kutu(x, y, w, h, cls="blok", rx=5, extra=""):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" class="{cls}"{extra}/>'


def sym(ad, x, y, etiket=None, alt=None, w=60, h=40):
    out = [f'<use href="#sym-{ad}" x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}"/>']
    if etiket:
        out.append(metin(x + w / 2, y + h + 13, etiket, "s-kucuk", "middle"))
    if alt:
        out.append(metin(x + w / 2, y + h + 25, alt, "s-mono2", "middle"))
    return "\n".join(out)


def ok(x1, y1, x2, y2, tur="analog", uc=True, d=None):
    path = d or f"M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}"
    m = f' marker-end="url(#ok-{tur})"' if uc else ""
    return f'<path d="{path}" class="yol-{tur}" fill="none"{m}/>'


def zincir(parcalar, x0, y, adim=100):
    """Yatay blok zinciri. parca: dict(sym, ad, alt, alan='analog|sayisal', cikis=alan). Döner (svg, son_x)."""
    out, x = [], x0
    for i, p in enumerate(parcalar):
        out.append(sym(p["sym"], x, y, p.get("ad"), p.get("alt")))
        if i < len(parcalar) - 1:
            tur = p.get("cikis", p.get("alan", "analog"))
            out.append(ok(x + 60, y + 20, x + adim, y + 20, tur))
        x += adim
    return "\n".join(out), x - adim + 60


def eksen_x(x0, x1, y, xmin, xmax, tikler, fmt=lambda v: f"{v:g}", ad=None):
    out = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="var(--ink-3)" stroke-width="1"/>']
    for v in tikler:
        px = x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)
        out.append(f'<line x1="{px:.1f}" y1="{y}" x2="{px:.1f}" y2="{y + 5}" stroke="var(--ink-3)" stroke-width="1"/>')
        out.append(metin(px, y + 17, fmt(v), "s-mono2", "middle"))
    if ad:
        out.append(metin(x1, y + 30, ad, "s-kucuk", "end"))
    return "\n".join(out)


def izgara(x0, x1, y0, y1, xt, yt, xmin, xmax, ymin, ymax, xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}"):
    parts = []
    for v in xt:
        px = x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)
        parts.append(f'<line x1="{px:.1f}" y1="{y1}" x2="{px:.1f}" y2="{y0}" class="izgara"/>' + metin(px, y0 + 14, xfmt(v), "s-mono2", "middle"))
    for v in yt:
        py = y0 - (v - ymin) / (ymax - ymin) * (y0 - y1)
        parts.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" class="izgara"/>' + metin(x0 - 6, py + 4, yfmt(v), "s-mono2", "end"))
    parts.append(f'<rect x="{x0}" y="{y1}" width="{x1 - x0}" height="{y0 - y1}" class="eksen"/>')
    return "\n".join(parts)


def cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, f, seviye, cls, w=3, etiket=None, ust=True):
    """Spektrum çizgisi (dikey çubuk) + isteğe bağlı etiket."""
    px = x0 + (f - xmin) / (xmax - xmin) * (x1 - x0)
    py = y0 - (max(ymin, min(ymax, seviye)) - ymin) / (ymax - ymin) * (y0 - y1)
    out = [f'<rect x="{px - w / 2:.1f}" y="{py:.1f}" width="{w}" height="{y0 - py:.1f}" class="{cls}"/>']
    if etiket:
        out.append(metin(px, py - 5 if ust else y0 + 26, etiket, "s-kucuk", "middle"))
    return "\n".join(out)


def path(xs, ys, x0, x1, y0, y1, xmin, xmax, ymin, ymax):
    d = []
    for k, (x, y) in enumerate(zip(xs, ys)):
        px = x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)
        py = y0 - (max(ymin, min(ymax, y)) - ymin) / (ymax - ymin) * (y0 - y1)
        d.append(("M" if k == 0 else "L") + f"{px:.1f} {py:.1f}")
    return "".join(d)


# ================================================================== BÖLÜM 5
def g_50():
    """Her RF bloğunun sembolü + tek satır işlev kartı (5 × 2 ızgara)."""
    kartlar = [
        ("anten", "Anten", "Havadaki alanı gerilime çevirir", "kazanç (dBi) · VSWR · bant"),
        ("limiter", "Limiter", "Güçlü girişte LNA'yı korur", "eşik · düz kayıp · toparlanma"),
        ("amp", "LNA", "Zayıf sinyali gürültü eklemeden büyütür", "NF · kazanç · P1dB · IP3"),
        ("bpf", "Preselector", "Bant dışını ve image'ı bastırır", "bant · ekleme kaybı · seçicilik"),
        ("att", "Zayıflatıcı / AGC / STC", "Seviyeyi ADC penceresine oturtur", "adım (dB) · aralık · hız"),
        ("mixer", "Mixer", "RF'i LO ile çarpar → IF", "dönüşüm kaybı · IIP3 · izolasyon"),
        ("lo", "LO / PLL", "Dönüşüm için temiz referans", "faz gürültüsü · spur · kilitlenme"),
        ("bpf", "IF filtre + yükselteç", "İstenen kanalı seçer, kazancı tamamlar", "BW · şekil faktörü · kazanç"),
        ("lpf", "Anti-alias filtre", "fs/2 üstünü ADC'den önce keser", "kesim · durdurma bandı · grup gecikmesi"),
        ("blok", "Balun / ADC sürücü", "Tek uçludan diferansiyele, FS'e ölçekler", "dengesizlik · OIP3 · gürültü"),
    ]
    W, H = 860, 470
    out = []
    kw, kh = 164, 200
    for i, (s, ad, islev, param) in enumerate(kartlar):
        c, r = i % 5, i // 5
        x, y = 8 + c * (kw + 6), 12 + r * (kh + 24)
        out.append(kutu(x, y, kw, kh, "blok", 8, ' opacity=".9"'))
        out.append(sym(s, x + kw / 2 - 30, y + 14))
        if s == "blok":
            out.append(metin(x + kw / 2, y + 38, "balun", "s-kucuk", "middle"))
        out.append(metin(x + kw / 2, y + 74, ad, "s-metin", "middle", ' style="font-weight:700"'))
        # işlev satırı: iki satıra kır
        soz = islev.split()
        yarim = len(soz) // 2 + (len(soz) % 2)
        out.append(metin(x + kw / 2, y + 96, " ".join(soz[:yarim]), "s-kucuk", "middle"))
        out.append(metin(x + kw / 2, y + 110, " ".join(soz[yarim:]), "s-kucuk", "middle"))
        out.append(f'<line x1="{x + 14}" y1="{y + 124}" x2="{x + kw - 14}" y2="{y + 124}" stroke="var(--line-2)"/>')
        out.append(metin(x + kw / 2, y + 142, "kilit parametreler", "s-kucuk s-altin", "middle"))
        ps = param.split(" · ")
        for j, p in enumerate(ps):
            out.append(metin(x + kw / 2, y + 158 + j * 13, p, "s-mono2", "middle"))
    # altta sıra oku
    yy = 2 * (kh + 24) + 8
    out.append(ok(20, yy, 840, yy, "analog"))
    out.append(metin(430, yy + 14, "zincirdeki sıra: anten → limiter → LNA → preselector → att/AGC → mixer (+LO) → IF filtre/amp → AAF → balun → ADC", "s-kucuk", "middle"))
    yaz("g-50", "rf-bloklar", W, H,
        "RF zincirinin yapıtaşları: on blok için sembol, tek satır işlev ve kilit parametreler — anten, limiter, LNA, preselector, zayıflatıcı/AGC/STC, mixer, LO/PLL, IF filtre ve yükselteç, anti-alias filtre, balun/ADC sürücü. Altta zincirdeki sıra.", out)


def g_51():
    """Çift ton testi: geniş spektrum (harmonikler), yakınlaştırılmış IMD3 ve IP3 çizgi grafiği (hesaplanmış)."""
    G, oip3, op1 = 20.0, 25.0, 15.0            # örnek yükselteç (kurgusal): LNA benzeri
    iip3, ip1 = oip3 - G, op1 - G
    f1, f2 = 1795.0, 1805.0                    # MHz — IF etrafında iki ton
    pout = -10.0                                # dBm / ton
    imd3 = 3 * pout - 2 * oip3                  # dBm
    W, H = 900, 760
    out = []
    # --- panel 1: geniş spektrum 0–6 GHz
    x0, x1, y0, y1 = 60, W - 20, 200, 40
    xmin, xmax, ymin, ymax = 0, 6000, -110, 10
    out.append(metin(x0, y1 - 12, "1 · Geniş bakış: iki ton ve harmonikleri (yükselteç çıkışı, dBm)", "s-baslik"))
    out.append(izgara(x0, x1, y0, y1, [0, 1000, 2000, 3000, 4000, 5000, 6000], [0, -40, -80], xmin, xmax, ymin, ymax, lambda v: f"{v / 1000:g}", lambda v: f"{v:d}"))
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, 1800, pout, "spk-sinyal", 4, "f₁, f₂ ≈ 1.8 GHz"))
    hd2, hd3 = 2 * pout - oip3 - 6, 3 * pout - 2 * oip3 - 9.5   # kaba: HD2 ≈ IMD2 − 6 dB, HD3 ≈ IMD3 − 9.5 dB
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, 3600, hd2, "spk-image", 4, f"2f ≈ {hd2:.0f} dBm"))
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, 5400, hd3, "spk-image", 4, f"3f ≈ {hd3:.0f} dBm"))
    out.append(metin(x1, y0 + 28, "frekans (GHz)", "s-kucuk", "end"))
    out.append(kutu(x0 + (1750 - xmin) / (xmax - xmin) * (x1 - x0), y1, (100) / (xmax - xmin) * (x1 - x0), y0 - y1, "spk-filtre", 0, ' fill="none"'))
    out.append(metin(x0 + (1800 - xmin) / (xmax - xmin) * (x1 - x0) + 12, y1 + 14, "→ panel 2", "s-kucuk s-altin"))
    # --- panel 2: yakın spektrum 1.77–1.83 GHz
    y0, y1 = 420, 260
    xmin, xmax = 1770, 1830
    out.append(metin(x0, y1 - 12, "2 · Yakınlaştır: IMD3 ürünleri 2f₁−f₂ ve 2f₂−f₁ tonların hemen yanında — filtreyle atılamaz", "s-baslik"))
    out.append(izgara(x0, x1, y0, y1, [1770, 1780, 1790, 1800, 1810, 1820, 1830], [0, -40, -80], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    # gürültü tabanı (B = 300 MHz, NF 6 → −83 dBm giriş; çıkışta +G)
    taban = -174 + db(300e6) + 6 + G
    py = y0 - (taban - ymin) / (ymax - ymin) * (y0 - y1)
    out.append(f'<rect x="{x0}" y="{py:.1f}" width="{x1 - x0}" height="{y0 - py:.1f}" class="spk-gurultu" opacity=".35"/>')
    out.append(metin(x0 + 6, py - 4, f"gürültü tabanı (B = 300 MHz) ≈ {taban:.0f} dBm", "s-kucuk"))
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, f1, pout, "spk-sinyal", 5, f"f₁ · {pout:.0f} dBm"))
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, f2, pout, "spk-sinyal", 5, f"f₂ · {pout:.0f} dBm"))
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, 2 * f1 - f2, imd3, "spk-image", 5, f"2f₁−f₂ · {imd3:.0f} dBm"))
    out.append(cubuk(x0, x1, y0, y1, xmin, xmax, ymin, ymax, 2 * f2 - f1, imd3, "spk-image", 5, f"2f₂−f₁ · {imd3:.0f} dBm"))
    # dBc oku
    pxa = x0 + (f2 + 3 - xmin) / (xmax - xmin) * (x1 - x0)
    pya = y0 - (pout - ymin) / (ymax - ymin) * (y0 - y1)
    pyb = y0 - (imd3 - ymin) / (ymax - ymin) * (y0 - y1)
    out.append(f'<path d="M{pxa:.1f} {pya:.1f} V{pyb:.1f}" class="yol-gurultu" marker-end="url(#ok-gurultu)" marker-start="url(#ok-gurultu)"/>')
    out.append(metin(pxa + 6, (pya + pyb) / 2, f"IMD3 = {imd3 - pout:.0f} dBc = 2·(P_out − OIP3)", "s-kucuk s-kirmizi"))
    out.append(metin(x1, y0 + 28, "frekans (MHz)", "s-kucuk", "end"))
    # --- panel 3: IP3 çizgi grafiği
    y0, y1 = 720, 480
    xl0, xl1 = 60, 560
    xmin, xmax, ymin, ymax = -50, 20, -100, 40
    out.append(metin(xl0, y1 - 12, "3 · Kesişim noktası: temel bileşen eğim 1, IMD3 eğim 3; uzantıları IP3'te kesişir (kurgusal yükselteç, G = 20 dB)", "s-baslik"))
    out.append(izgara(xl0, xl1, y0, y1, [-50, -40, -30, -20, -10, 0, 10, 20], [-100, -80, -60, -40, -20, 0, 20, 40], xmin, xmax, ymin, ymax, lambda v: f"{v:d}", lambda v: f"{v:d}"))
    xs = [xmin + k * 0.5 for k in range(int((xmax - xmin) / 0.5) + 1)]
    pc = ip1 + 5.87                               # 1 dB sıkışma noktasını tutturan yumuşak model
    temel = [x + G - 10 * math.log10(1 + 10 ** ((x - pc) / 10)) for x in xs]
    imd = [3 * x - 2 * iip3 - 3 * 10 * math.log10(1 + 10 ** ((x - pc) / 10)) for x in xs]
    out.append(f'<path d="{path(xs, [x + G for x in xs], xl0, xl1, y0, y1, xmin, xmax, ymin, ymax)}" fill="none" stroke="var(--accent)" stroke-width="1" stroke-dasharray="4 4"/>')
    out.append(f'<path d="{path(xs, [3 * x - 2 * iip3 for x in xs], xl0, xl1, y0, y1, xmin, xmax, ymin, ymax)}" fill="none" stroke="var(--red)" stroke-width="1" stroke-dasharray="4 4"/>')
    out.append(f'<path d="{path(xs, temel, xl0, xl1, y0, y1, xmin, xmax, ymin, ymax)}" fill="none" stroke="var(--accent)" stroke-width="2.2"/>')
    out.append(f'<path d="{path(xs, imd, xl0, xl1, y0, y1, xmin, xmax, ymin, ymax)}" fill="none" stroke="var(--red)" stroke-width="2.2"/>')

    def P(x, y):
        return (xl0 + (x - xmin) / (xmax - xmin) * (xl1 - xl0), y0 - (y - ymin) / (ymax - ymin) * (y0 - y1))
    px, py = P(iip3, oip3)
    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="var(--gold)"/>')
    out.append(metin(px + 8, py - 6, f"IP3 (IIP3 {iip3:+.0f} dBm, OIP3 {oip3:+.0f} dBm)", "s-kucuk s-altin"))
    px, py = P(ip1, op1)
    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="var(--gold)"/>')
    out.append(metin(px + 8, py + 14, f"P1dB (giriş {ip1:+.0f}, çıkış {op1:+.0f} dBm)", "s-kucuk s-altin"))
    out.append(metin(xl1, y0 + 28, "giriş gücü / ton (dBm)", "s-kucuk", "end"))
    out.append(metin(24, (y0 + y1) / 2, "çıkış (dBm)", "s-kucuk", "middle", f' transform="rotate(-90 24 {(y0 + y1) / 2})"'))
    # sağ: SFDR açıklaması
    tx = 590
    out.append(kutu(tx, 480, 290, 240, "blok", 8, ' opacity=".9"'))
    satirlar = ["Çift ton SFDR (giriş referanslı):",
                "SFDR = ⅔ · (IIP3 − MDS)",
                "",
                "Okuma: iki ton MDS'nin SFDR dB",
                "üstündeyse IMD3 ürünü tam gürültü",
                "tabanına değer. Daha güçlü ton →",
                "IMD3 tespit eşiğini aşar, 'hayalet'",
                "darbe üretir.",
                "",
                "Kural: IIP3 ≈ IP1dB + 10 dB",
                "(cihazdan cihaza 8–15 dB oynar).",
                "",
                "Eğim 3 → giriş 1 dB artınca IMD3",
                "3 dB, dBc cinsinden 2 dB büyür."]
    for j, sline in enumerate(satirlar):
        cls = "s-metin" if j in (0, 1, 9) else "s-kucuk"
        out.append(metin(tx + 12, 500 + j * 16, sline, cls))
    yaz("g-51", "cift-ton-imd3", W, H,
        "Çift ton testi ve IP3: (1) geniş spektrumda iki ton ve 2f, 3f harmonikleri; (2) yakınlaştırılmış spektrumda IMD3 ürünleri 2f1−f2 ve 2f2−f1 tonların 10 MHz yanında, gürültü tabanı gri; (3) giriş–çıkış grafiğinde temel bileşen eğim 1, IMD3 eğim 3, uzantıları IP3'te kesişir, P1dB noktası işaretli; sağda çift ton SFDR formülü.", out)


def g_52():
    """Seviye planı: scenario.json on_uc.kaskad için sinyal / gürültü / P1dB tavanı, blok blok (hesaplanmış)."""
    K = S["on_uc"]["kaskad"]
    B = S["ddc"]["cikis_bant_mhz"] * 1e6
    sig0 = S["sinyal"]["seviye_dbm_giris"]
    guclu0 = -20.0                                           # kurgusal güçlü emiter
    fs_dbm = S["adc"]["tam_olcek_dbm"]
    adim = friis(K)
    ktb = -174 + db(B)
    adlar = ["giriş"] + [b["ad"] for b in K]
    sig, guclu, gur, gkum = [sig0], [guclu0], [ktb], [0.0]
    g = 0.0
    for i, b in enumerate(K):
        g += b["kazanc_db"]
        sig.append(sig0 + g); guclu.append(guclu0 + g); gur.append(ktb + adim[i][0] + adim[i][1]); gkum.append(g)
    W, H = 900, 560
    x0, x1, y0, y1 = 70, W - 30, 400, 40
    n = len(adlar)
    xmin, xmax, ymin, ymax = -0.5, n - 0.5, -110, 30
    out = [metin(x0, 22, "Seviye planı (referans senaryo, kurgusal P1dB bütçesi) — B = 300 MHz", "s-baslik")]
    out.append(izgara(x0, x1, y0, y1, [], [20, 0, -20, -40, -60, -80, -100], xmin, xmax, ymin, ymax, yfmt=lambda v: f"{v:d}"))

    def P(i, v):
        return (x0 + (i - xmin) / (xmax - xmin) * (x1 - x0), y0 - (max(ymin, min(ymax, v)) - ymin) / (ymax - ymin) * (y0 - y1))
    # sütun etiketleri
    for i, ad in enumerate(adlar):
        px, _ = P(i, 0)
        out.append(metin(px, y0 + 16, ad, "s-kucuk", "middle"))
        if i > 0:
            b = K[i - 1]
            out.append(metin(px, y0 + 30, f"G {b['kazanc_db']:+g} · NF {b['nf_db']:g}", "s-mono2", "middle"))
            out.append(metin(px, y0 + 44, f"NF_kum {adim[i - 1][0]:.2f} dB", "s-mono2 s-altin", "middle"))
            out.append(metin(px, y0 + 58, f"G_kum {gkum[i]:+.1f} dB", "s-mono2", "middle"))
    # gürültü alanı
    gx = [P(i, v)[0] for i, v in enumerate(gur)]
    gy = [P(i, v)[1] for i, v in enumerate(gur)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in zip(gx, gy))
    out.append(f'<path d="{d} L{gx[-1]:.1f} {y0} L{gx[0]:.1f} {y0} Z" class="spk-gurultu" opacity=".35"/>')
    out.append(f'<path d="{d}" fill="none" stroke="var(--ink-3)" stroke-width="1.6"/>')
    # sinyal çizgileri
    for seri, cls, ad in ((sig, "var(--accent)", f"referans darbe ({sig0:g} dBm giriş)"), (guclu, "var(--gold)", f"güçlü emiter ({guclu0:g} dBm giriş)")):
        pts = [P(i, v) for i, v in enumerate(seri)]
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{cls}" stroke-width="2.2"/>')
        for (x, y) in pts:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{cls}"/>')
        out.append(metin(pts[-1][0] - 6, pts[-1][1] - 8, f"{seri[-1]:+.0f} dBm", "s-kucuk", "end"))
        out.append(metin(pts[0][0] + 6, pts[0][1] - 8, ad, "s-kucuk"))
    # gürültü etiketleri
    out.append(metin(gx[0] + 6, gy[0] + 14, f"kTB = {ktb:.1f} dBm", "s-kucuk"))
    out.append(metin(gx[-1] - 6, gy[-1] + 14, f"{gur[-1]:.1f} dBm (NF {adim[-1][0]:.2f} + G {gkum[-1]:.0f})", "s-kucuk", "end"))
    # P1dB tavanları (çıkış) kırmızı kısa çizgi
    for i, b in enumerate(K):
        if b["ad"] in OP1DB:
            px, py = P(i + 1, OP1DB[b["ad"]])
            out.append(f'<line x1="{px - 18:.1f}" y1="{py:.1f}" x2="{px + 18:.1f}" y2="{py:.1f}" stroke="var(--red)" stroke-width="2.4"/>')
            out.append(metin(px + 22, py + 4, f"OP1dB {OP1DB[b['ad']]:+.0f}", "s-kucuk s-kirmizi"))
    # ADC tam ölçek
    px, py = P(n - 1, fs_dbm)
    out.append(f'<line x1="{px - 30:.1f}" y1="{py:.1f}" x2="{px + 26:.1f}" y2="{py:.1f}" stroke="var(--red)" stroke-width="2.4" stroke-dasharray="5 3"/>')
    out.append(metin(px - 34, py + 4, f"ADC FS {fs_dbm:+g} dBm", "s-kucuk s-kirmizi", "end"))
    # SNR oku
    pa, pb = P(n - 1, sig[-1]), P(n - 1, gur[-1])
    out.append(f'<path d="M{pa[0] + 10:.1f} {pa[1]:.1f} V{pb[1]:.1f}" class="yol-sayisal" marker-end="url(#ok-sayisal)" marker-start="url(#ok-sayisal)"/>')
    out.append(metin(pa[0] + 14, (pa[1] + pb[1]) / 2 + 4, f"SNR {sig[-1] - gur[-1]:.1f} dB", "s-kucuk s-vurgu"))
    # taşma oku
    pg = P(n - 1, guclu[-1])
    out.append(f'<path d="M{pg[0] - 46:.1f} {py:.1f} V{pg[1]:.1f}" class="yol-gurultu" marker-end="url(#ok-gurultu)"/>')
    out.append(metin(pg[0] - 50, (pg[1] + py) / 2 + 4, f"{guclu[-1] - fs_dbm:.0f} dB taşma → zayıflatıcı", "s-kucuk s-kirmizi", "end"))
    out.append(metin(24, (y0 + y1) / 2, "seviye (dBm)", "s-kucuk", "middle", f' transform="rotate(-90 24 {(y0 + y1) / 2})"'))
    # alt not
    iip3, _ = ip3_kaskad(K)
    out.append(metin(x0, 480, f"Friis ile zincir NF = {adim[-1][0]:.2f} dB (bütçe: 6 dB, {{{{bolum:4}}}}). Kurgusal IP3 bütçesiyle zincir IIP3 ≈ {iip3:.1f} dBm; tavan ADC tam ölçeği: giriş {fs_dbm - gkum[-1]:+.0f} dBm.".replace("{{{{bolum:4}}}}", "Bölüm 4"), "s-kucuk"))
    out.append(metin(x0, 498, "Gri: gürültü tabanı (kTB + NF_kum + G_kum). Mavi: −60 dBm referans darbe. Altın: −20 dBm güçlü emiter — son katlar sıkışmadan ADC dolar.", "s-kucuk"))
    out.append(metin(x0, 516, "Kırmızı çizgiler: blokların çıkış P1dB'si; sinyal bu çizgiye 3 dB'den fazla yaklaşınca IMD3 hızla büyür (eğim 3).", "s-kucuk"))
    out.append(metin(x0, 534, "Anlık dinamik aralık ≈ ADC FS girişi (−36 dBm) − MDS (−83 dBm) ≈ 47 dB; zayıflatıcı adımlarıyla 'toplam' dinamik aralık 30 dB daha genişler.", "s-kucuk"))
    yaz("g-52", "seviye-plani", W, H,
        "Seviye planı: referans senaryonun yedi bloklu RF zinciri boyunca sinyal (mavi, −60 dBm giriş), güçlü emiter (altın, −20 dBm) ve gürültü tabanı (gri, kTB + kümülatif NF + kümülatif kazanç, B = 300 MHz); her blok altında kazanç, NF, kümülatif NF ve kümülatif kazanç; kırmızı çizgiler blok çıkış P1dB'leri ve ADC tam ölçeği; çıkışta SNR oku ve güçlü sinyalin ADC'yi taşırma miktarı.", out)


# ================================================================== BÖLÜM 6
def g_60():
    """Mixer = çarpım: zaman panelinde cos·cos, spektrumda adım adım toplam/fark ürünleri ve IF filtresi."""
    RF, LO = S["sinyal"]["rf_ghz"], S["on_uc"]["lo_ghz"]
    IF = abs(RF - LO)
    W, H = 900, 700
    out = []
    # zaman paneli (normalize: 1 birim zaman = 1 ns)
    x0, x1 = 60, W - 20
    n = 700
    ts = [k / (n - 1) * 1.6 for k in range(n)]            # ns
    a = [math.cos(TAU * RF * t) for t in ts]
    b = [math.cos(TAU * LO * t) for t in ts]
    c = [u * v for u, v in zip(a, b)]
    zarf = [0.5 * math.cos(TAU * IF * t) for t in ts]
    for i, (ad, ys, cls, ymx) in enumerate((("RF 9.4 GHz", a, "var(--gold)", 1.2), ("LO 7.6 GHz", b, "var(--ink-3)", 1.2), ("çarpım = ½cos(2π·1.8t) + ½cos(2π·17t)", c, "var(--accent)", 1.2))):
        yt, yb = 34 + i * 62, 34 + i * 62 + 50
        out.append(metin(x0, yt - 6, ad, "s-kucuk"))
        out.append(f'<path d="{path(ts, ys, x0, x1, yb, yt, 0, 1.6, -ymx, ymx)}" fill="none" stroke="{cls}" stroke-width="1.2"/>')
        if i == 2:
            out.append(f'<path d="{path(ts, zarf, x0, x1, yb, yt, 0, 1.6, -ymx, ymx)}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 3"/>')
            out.append(f'<path d="{path(ts, [-z for z in zarf], x0, x1, yb, yt, 0, 1.6, -ymx, ymx)}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 3"/>')
            out.append(metin(x1, yb + 14, "zaman (ns) · 0 … 1.6 — kesikli: yavaş bileşen (IF)", "s-kucuk", "end"))
    # spektrum panelleri
    xmin, xmax, ymin, ymax = 0, 18, 0, 1
    py0 = 250
    paneller = [
        ("① Girişler: RF ve LO (frekans ekseninde iki çizgi)", [(RF, 1.0, "spk-sinyal", "RF 9.4"), (LO, 0.9, "spk-gurultu", "LO 7.6")], None),
        ("② Çarpım: fark (RF−LO) ve toplam (RF+LO) — her biri ½ genlik; gerçek mixer'da LO ve RF sızıntısı da çıkışta görünür", [(RF - LO, 0.5, "spk-sinyal", "IF = 1.8"), (RF + LO, 0.5, "spk-sinyal", "17.0"), (LO, 0.25, "spk-image", "LO sızıntısı"), (RF, 0.12, "spk-image", "RF sızıntısı")], None),
        ("③ IF filtresi fark ürününü seçer; toplam ürünü, LO ve RF sızıntısı bastırılır", [(RF - LO, 0.5, "spk-sinyal", "IF 1.8"), (RF + LO, 0.06, "spk-image", ""), (LO, 0.04, "spk-image", ""), (RF, 0.03, "spk-image", "")], (IF - 0.3, IF + 0.3)),
    ]
    for i, (baslik, cizgiler, filt) in enumerate(paneller):
        y1p, y0p = py0 + i * 150, py0 + i * 150 + 100
        out.append(metin(x0, y1p - 8, baslik, "s-baslik"))
        out.append(izgara(x0, x1, y0p, y1p, list(range(0, 19, 2)), [], xmin, xmax, ymin, ymax, lambda v: f"{v:d}"))
        if filt:
            fa, fb = filt
            pa = x0 + (fa - xmin) / (xmax - xmin) * (x1 - x0)
            pb = x0 + (fb - xmin) / (xmax - xmin) * (x1 - x0)
            out.append(f'<path d="M{pa - 30:.1f} {y0p} L{pa:.1f} {y1p + 8} H{pb:.1f} L{pb + 30:.1f} {y0p}" class="spk-filtre" fill="none"/>')
            out.append(metin(pb + 34, y1p + 20, "IF filtre (altın kesikli)", "s-kucuk s-altin"))
        for f, gen, cls, et in cizgiler:
            out.append(cubuk(x0, x1, y0p, y1p, xmin, xmax, ymin, ymax, f, gen, cls, 5, et))
        out.append(metin(x1, y0p + 28, "frekans (GHz)", "s-kucuk", "end"))
    yaz("g-60", "mixer-carpim", W, H,
        "Mixer çarpımı adım adım: üstte zaman domaininde RF (9.4 GHz), LO (7.6 GHz) ve çarpımları — hızlı bileşen üzerinde yavaş 1.8 GHz zarf; altta üç spektrum paneli: girişler, çarpım ürünleri (fark 1.8 GHz ve toplam 17.0 GHz, LO/RF sızıntısı kırmızı) ve IF filtresinin fark ürününü seçmesi.", out)


def g_61():
    """Image problemi: RF ekseninde RF, LO, image ve preselector; IF ekseninde üst üste binme; high-side seçenek ve evrilme."""
    RF, LO, IF = S["sinyal"]["rf_ghz"], S["on_uc"]["lo_ghz"], S["on_uc"]["if_ghz"]
    IMG = S["on_uc"]["image_ghz"]
    LOh, IMGh = RF + IF, RF + 2 * IF
    W, H = 900, 620
    x0, x1 = 60, W - 20
    xmin, xmax, ymin, ymax = 0, 14, 0, 1
    out = []

    def asim_sekil(fc, yon, x0_, x1_, y0_, y1_, xmin_, xmax_, gen, cls):
        """Asimetrik (rampa) spektrum şekli: evrilmeyi görünür kılmak için."""
        w = 0.35
        pa = x0_ + (fc - w / 2 - xmin_) / (xmax_ - xmin_) * (x1_ - x0_)
        pb = x0_ + (fc + w / 2 - xmin_) / (xmax_ - xmin_) * (x1_ - x0_)
        hy = y0_ - gen * (y0_ - y1_)
        if yon > 0:
            d = f"M{pa:.1f} {y0_} L{pb:.1f} {hy:.1f} V{y0_} Z"
        else:
            d = f"M{pa:.1f} {hy:.1f} L{pb:.1f} {y0_} H{pa:.1f} Z"
        return f'<path d="{d}" class="{cls}" opacity=".85"/>'

    # panel 1: RF ekseni low-side
    y1p, y0p = 40, 150
    out.append(metin(x0, y1p - 10, "① Low-side LO (referans): image, LO'nun öbür yanında, IF kadar uzakta — preselector onu bastırmalı", "s-baslik"))
    out.append(izgara(x0, x1, y0p, y1p, list(range(0, 15, 2)), [], xmin, xmax, ymin, ymax, lambda v: f"{v:d}"))
    pa = x0 + (8.0 - xmin) / (xmax - xmin) * (x1 - x0)
    pb = x0 + (11.0 - xmin) / (xmax - xmin) * (x1 - x0)
    out.append(f'<path d="M{pa - 40:.1f} {y0p} L{pa:.1f} {y1p + 10} H{pb:.1f} L{pb + 40:.1f} {y0p}" class="spk-filtre" fill="none"/>')
    out.append(metin(pb + 6, y1p + 22, "preselector 8–11 GHz", "s-kucuk s-altin"))
    out.append(asim_sekil(RF, +1, x0, x1, y0p, y1p, xmin, xmax, 0.8, "spk-sinyal"))
    out.append(asim_sekil(IMG, +1, x0, x1, y0p, y1p, xmin, xmax, 0.8, "spk-image"))
    out.append(cubuk(x0, x1, y0p, y1p, xmin, xmax, ymin, ymax, LO, 0.95, "spk-gurultu", 4, f"LO {LO:g}"))
    out.append(metin(x0 + (RF - xmin) / (xmax - xmin) * (x1 - x0), y1p + 22, f"RF {RF:g}", "s-kucuk s-vurgu", "middle"))
    out.append(metin(x0 + (IMG - xmin) / (xmax - xmin) * (x1 - x0), y1p + 22, f"image {IMG:g}", "s-kucuk s-kirmizi", "middle"))
    for fa, fb in ((LO, RF), (IMG, LO)):
        pxa = x0 + (fa - xmin) / (xmax - xmin) * (x1 - x0)
        pxb = x0 + (fb - xmin) / (xmax - xmin) * (x1 - x0)
        out.append(f'<path d="M{pxa:.1f} {y0p - 12} H{pxb:.1f}" class="yol-saat" marker-end="url(#ok-saat)" marker-start="url(#ok-saat)"/>')
        out.append(metin((pxa + pxb) / 2, y0p - 16, f"IF = {IF:g} GHz", "s-mono2", "middle"))
    out.append(metin(x1, y0p + 28, "RF ekseni (GHz)", "s-kucuk", "end"))
    # panel 2: IF ekseni
    y1p, y0p = 220, 320
    ximin, ximax = 0, 4
    out.append(metin(x0, y1p - 10, "② IF ekseninde ikisi de 1.8 GHz'e düşer — mixer'dan sonra ayırt edilemezler; image düz kalır, sinyal düz kalır (low-side: evrilme yok)", "s-baslik"))
    out.append(izgara(x0, x1, y0p, y1p, [0, 1, 2, 3, 4], [], ximin, ximax, ymin, ymax, lambda v: f"{v:d}"))
    out.append(asim_sekil(IF, +1, x0, x1, y0p, y1p, ximin, ximax, 0.8, "spk-sinyal"))
    out.append(asim_sekil(IF + 0.02, +1, x0, x1, y0p, y1p, ximin, ximax, 0.25, "spk-image"))
    pif = x0 + (IF - ximin) / (ximax - ximin) * (x1 - x0)
    out.append(metin(pif + 60, y1p + 30, "mavi: RF − LO = 1.8 (düz)", "s-kucuk s-vurgu"))
    out.append(metin(pif + 60, y1p + 46, "kırmızı: LO − image = 1.8 (preselector'dan artakalan)", "s-kucuk s-kirmizi"))
    out.append(metin(x1, y0p + 28, "IF ekseni (GHz)", "s-kucuk", "end"))
    # panel 3: high-side
    y1p, y0p = 390, 500
    out.append(metin(x0, y1p - 10, f"③ High-side seçenek: LO = {LOh:g} GHz → image {IMGh:g} GHz; IF'e inen spektrum evrilir (rampa ters döner)", "s-baslik"))
    out.append(izgara(x0, x1, y0p, y1p, list(range(0, 15, 2)), [], xmin, xmax, ymin, ymax, lambda v: f"{v:d}"))
    out.append(f'<path d="M{pa - 40:.1f} {y0p} L{pa:.1f} {y1p + 10} H{pb:.1f} L{pb + 40:.1f} {y0p}" class="spk-filtre" fill="none"/>')
    out.append(asim_sekil(RF, +1, x0, x1, y0p, y1p, xmin, xmax, 0.8, "spk-sinyal"))
    out.append(asim_sekil(IMGh, +1, x0, x1, y0p, y1p, xmin, xmax, 0.8, "spk-image"))
    out.append(cubuk(x0, x1, y0p, y1p, xmin, xmax, ymin, ymax, LOh, 0.95, "spk-gurultu", 4, f"LO {LOh:g}"))
    out.append(metin(x0 + (RF - xmin) / (xmax - xmin) * (x1 - x0), y1p + 22, f"RF {RF:g}", "s-kucuk s-vurgu", "middle"))
    out.append(metin(x0 + (IMGh - xmin) / (xmax - xmin) * (x1 - x0), y1p + 22, f"image {IMGh:g}", "s-kucuk s-kirmizi", "middle"))
    out.append(metin(x1, y0p + 28, "RF ekseni (GHz)", "s-kucuk", "end"))
    # panel 3b: IF ekseni evrik
    y1p, y0p = 530, 600
    out.append(izgara(x0, x1, y0p, y1p, [0, 1, 2, 3, 4], [], ximin, ximax, ymin, ymax, lambda v: f"{v:d}"))
    out.append(asim_sekil(IF, -1, x0, x1, y0p, y1p, ximin, ximax, 0.8, "spk-sinyal"))
    out.append(metin(pif + 60, y1p + 20, "LO − RF = 1.8: rampa ters → spektrum evrik; LFM'in yönü, I/Q işareti tersine döner (INV biti)", "s-kucuk s-vurgu"))
    out.append(metin(x1, y0p + 28, "IF ekseni (GHz)", "s-kucuk", "end"))
    yaz("g-61", "image-problemi", W, H,
        "Image problemi: (1) low-side LO 7.6 GHz ile RF 9.4 GHz ve image 5.8 GHz LO'nun iki yanında eşit uzaklıkta, preselector bandı 8–11 GHz altın kesikli; (2) IF ekseninde ikisi de 1.8 GHz'e düşer; (3) high-side LO 11.2 GHz ile image 13.0 GHz'e taşınır ve IF spektrumu evrilir — asimetrik rampa şekli ters döner.", out)


def g_62():
    """Referans senaryonun frekans planı: RF, LO, image, half-IF, preselector, IF bandı, Nyquist bölgeleri, alias."""
    RF, LO, IF = S["sinyal"]["rf_ghz"], S["on_uc"]["lo_ghz"], S["on_uc"]["if_ghz"]
    IMG = S["on_uc"]["image_ghz"]
    fs = S["adc"]["fs_msps"] / 1000
    alias = S["adc"]["alias_mhz"] / 1000
    bw = S["ddc"]["cikis_bant_mhz"] / 1000
    W, H = 920, 560
    x0, x1 = 60, W - 20
    xmin, xmax, ymin, ymax = 0, 14, 0, 1
    out = [metin(x0, 22, "Referans senaryo frekans planı — tek dönüşüm, low-side LO, direct IF sampling (2. Nyquist bölgesi)", "s-baslik")]
    y1p, y0p = 50, 220
    out.append(izgara(x0, x1, y0p, y1p, list(range(0, 15, 1)), [], xmin, xmax, ymin, ymax, lambda v: f"{v:d}"))

    def X(f):
        return x0 + (f - xmin) / (xmax - xmin) * (x1 - x0)
    # Nyquist bölgeleri (ilk 4)
    for k in range(4):
        a, b = k * fs / 2, (k + 1) * fs / 2
        cls = "spk-sinyal" if k == 1 else "spk-gurultu"
        out.append(f'<rect x="{X(a):.1f}" y="{y0p - 14}" width="{X(b) - X(a):.1f}" height="14" class="{cls}" opacity="{0.35 if k == 1 else 0.15}"/>')
        out.append(metin((X(a) + X(b)) / 2, y0p - 4, f"NZ{k + 1}", "s-kucuk", "middle"))
    # preselector
    out.append(f'<path d="M{X(8) - 40:.1f} {y0p} L{X(8):.1f} {y1p + 12} H{X(11):.1f} L{X(11) + 40:.1f} {y0p}" class="spk-filtre" fill="none"/>')
    out.append(metin(X(11) + 6, y1p + 24, "preselector 8–11", "s-kucuk s-altin"))
    # IF bandı
    out.append(f'<rect x="{X(IF - bw):.1f}" y="{y1p + 40}" width="{X(IF + bw) - X(IF - bw):.1f}" height="{y0p - y1p - 40}" class="spk-sinyal" opacity=".18"/>')
    out.append(metin(X(IF), y1p + 36, f"IF bandı {IF:g} ± {bw:g}", "s-kucuk s-vurgu", "middle"))
    # çizgiler
    cizgiler = [(RF, 0.9, "spk-sinyal", f"RF {RF:g}"), (LO, 0.95, "spk-gurultu", f"LO {LO:g}"), (IMG, 0.7, "spk-image", f"image {IMG:g}"),
                ((RF + LO) / 2, 0.55, "spk-image", "½-IF 8.5"), (IF, 0.9, "spk-sinyal", f"IF {IF:g}"), (alias, 0.5, "spk-gurultu", f"alias {alias:g} (evrik)"),
                (RF + LO, 0.0, "spk-image", "")]
    for f, g, cls, et in cizgiler:
        if f <= xmax:
            out.append(cubuk(x0, x1, y0p, y1p, xmin, xmax, ymin, ymax, f, g, cls, 5, et))
    # oklar: RF→IF (fark), IF→alias
    out.append(f'<path d="M{X(RF):.1f} {y1p + 6} Q{(X(RF) + X(IF)) / 2:.1f} {y1p - 30} {X(IF) + 4:.1f} {y1p + 6}" class="yol-analog" marker-end="url(#ok-analog)"/>')
    out.append(metin((X(RF) + X(IF)) / 2, y1p - 8, "RF − LO = IF (düz)", "s-kucuk s-altin", "middle"))
    out.append(f'<path d="M{X(IMG):.1f} {y1p + 40} Q{(X(IMG) + X(IF)) / 2:.1f} {y1p + 10} {X(IF) + 6:.1f} {y1p + 40}" class="yol-gurultu" marker-end="url(#ok-gurultu)"/>')
    out.append(metin((X(IMG) + X(IF)) / 2 + 10, y1p + 62, "LO − image = IF de! (preselector bastırır)", "s-kucuk s-kirmizi", "middle"))
    out.append(f'<path d="M{X(IF):.1f} {y0p - 30} Q{(X(IF) + X(alias)) / 2:.1f} {y0p - 70} {X(alias) + 4:.1f} {y0p - 30}" class="yol-sayisal" marker-end="url(#ok-sayisal)"/>')
    out.append(metin((X(IF) + X(alias)) / 2, y0p - 74, "ADC fs 2.4 GSPS: NZ2 → alias 0.6, evrik", "s-kucuk s-vurgu", "middle"))
    out.append(metin(x1, y0p + 28, "frekans (GHz)", "s-kucuk", "end"))
    # spur tablosu
    ty = 275
    out.append(metin(x0, ty, "Düşük mertebe mixer ürünleri m·f_in − n·LO = ±IF olan giriş frekansları (m, n ≤ 3; hesaplanmış):", "s-baslik"))
    spurlar = {}
    for m in range(1, 4):
        for n in range(0, 4):
            for s2 in (+1, -1):
                f = (s2 * IF + n * LO) / m
                if 0.5 < f < 14:
                    spurlar.setdefault(round(f, 3), []).append((m, n))
    satir = 0
    kolon = 0
    for f in sorted(spurlar):
        mn = ", ".join(f"{m}×{n}" for m, n in spurlar[f])
        icinde = 8.0 <= f <= 11.0
        istenen = abs(f - RF) < 1e-6
        durum = "istenen" if istenen else ("preselector İÇİNDE → tehlikeli" if icinde else "preselector dışında")
        cls = "s-vurgu" if istenen else ("s-kirmizi" if icinde else "s-kucuk")
        cx, cy = x0 + kolon * 430, ty + 22 + satir * 17
        out.append(metin(cx, cy, f"{f:6.3f} GHz", "s-mono2 " + cls))
        out.append(metin(cx + 80, cy, f"(m×n = {mn})", "s-mono2"))
        out.append(metin(cx + 190, cy, durum, "s-kucuk " + cls))
        satir += 1
        if satir == 10:
            satir, kolon = 0, 1
    out.append(metin(x0, 470, "Okuma: 8.5 GHz'deki bir giriş 2×2 ürünüyle (2·8.5 − 2·7.6 = 1.8) IF'e düşer — 'half-IF spur'. Preselector 8–11 GHz bandının içinde kaldığından", "s-kucuk"))
    out.append(metin(x0, 486, "yalnızca mixer'ın kendi 2×2 bastırması (tipik 50–70 dBc, doğrulanmadı) korur. 10.5 GHz'deki 2×3 ürünü de banttadır ama üçüncü mertebe LO çarpanı zayıftır.", "s-kucuk"))
    out.append(metin(x0, 502, "Image (5.8) ve 1×2 ürünü (13.4) preselector dışındadır: filtre bastırması + mixer izolasyonu yeter. Bu tablo W-05'te canlı olarak yeniden üretilir.", "s-kucuk"))
    out.append(metin(x0, 530, "Frekans planı bir 'temiz pencere' aramasıdır: IF öyle seçilir ki image ve düşük mertebe spur'lar preselector'ın reddettiği yere düşsün, IF de ADC'nin iyi çalıştığı Nyquist bölgesine otursun.", "s-kucuk s-altin"))
    yaz("g-62", "frekans-plani", W, H,
        "Referans senaryonun frekans planı: RF 9.4 GHz, low-side LO 7.6 GHz, image 5.8 GHz, half-IF spur girişi 8.5 GHz, preselector 8–11 GHz, IF bandı 1.8 ± 0.15 GHz, ilk dört Nyquist bölgesi (fs 2.4 GSPS) ve IF'in 600 MHz'e evrik katlanması; altta m×n ≤ 3 mixer ürünlerinin IF'e düşürdüğü giriş frekansları tablosu.", out)


# ================================================================== BÖLÜM 7 — mimari blok şemaları
def anten_etiket(x, y):
    return sym("anten", x, y, "anten")


def g_70():
    out = [metin(20, 24, "M-1 · Kristal video almaç (CVR) — RF → doğrudan zarf; frekans bilgisi yok", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="bpf", ad="geniş BPF", alt="2–18 GHz"), dict(sym="amp", ad="RF yükselteç", alt="(isteğe bağlı)"),
                    dict(sym="diyot", ad="kristal dedektör", alt="kare-yasa"), dict(sym="lpf", ad="video filtre", alt="~MHz"),
                    dict(sym="amp", ad="log video amp", alt="60–70 dB"), dict(sym="cmp", ad="eşik", alt="→ darbe var/yok", cikis="sayisal")], 20, 60)
    out.append(z)
    out.append(ok(xe, 80, xe + 30, 80, "sayisal"))
    out.append(metin(xe + 34, 84, "TOA · PW · PA", "s-kucuk s-vurgu"))
    out.append(kutu(20, 140, 820, 44, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 158, "Zarf tüm bant üzerinden alınır: hassasiyet düşük (geniş B → yüksek gürültü), eşzamanlı darbeler üst üste biner; ama darbe geldiği anda görülür (POI ≈ %100).", "s-kucuk"))
    out.append(metin(30, 174, "TRF (tuned radio frequency) aynı iskelettir: BPF dar ve ayarlanabilir → biraz seçicilik, hâlâ mixer yok.", "s-kucuk"))
    yaz("g-70", "cvr", 860, 196, "M-1 kristal video almaç blok şeması: anten → geniş bant BPF → (RF yükselteç) → kristal dedektör → video filtre → logaritmik video yükselteç → eşik; çıkışta TOA, PW, PA. Altta not: hassasiyet düşük, POI yüksek; TRF varyantı.", out)


def g_71():
    out = [metin(20, 24, "M-2 · Süperheterodin (taramalı, çift dönüşüm) — dar pencere, yüksek hassasiyet", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="bpf", ad="preselector", alt="ayarlı YIG"), dict(sym="amp", ad="LNA"),
                    dict(sym="mixer", ad="mixer 1"), dict(sym="bpf", ad="IF₁ filtre", alt="yüksek IF"), dict(sym="mixer", ad="mixer 2"),
                    dict(sym="bpf", ad="IF₂ filtre", alt="dar, ~MHz"), dict(sym="amp", ad="IF amp / log"), dict(sym="diyot", ad="dedektör", cikis="analog")], 20, 60, 92)
    out.append(z)
    # LO'lar
    out.append(sym("lo", 296, 130, "LO₁ (sentezleyici)", "taramalı"))
    out.append(ok(326, 130, 326, 100, "saat"))
    out.append(sym("lo", 480, 130, "LO₂ (sabit)"))
    out.append(ok(510, 130, 510, 100, "saat"))
    out.append(sym("reg", 140, 130, "tarama kontrolü"))
    out.append(ok(200, 150, 296, 150, "kontrol"))
    out.append(ok(170, 130, 170, 100, "kontrol"))
    out.append(ok(xe, 80, xe + 26, 80, "analog"))
    out.append(metin(xe - 40, 118, "video → eşik", "s-kucuk"))
    out.append(kutu(20, 200, 820, 44, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 218, "Anlık bant IF₂ filtresi kadar dardır; bandı LO₁ ile taramak gerekir → POI düşer. Karşılığında en iyi hassasiyet ve seçicilik, temiz dinamik aralık.", "s-kucuk"))
    out.append(metin(30, 234, "İlk IF yüksek (image uzak, preselector kolay), ikinci IF düşük (dar filtre kolay): çift dönüşümün klasik gerekçesi (Bölüm 6).", "s-kucuk"))
    yaz("g-71", "superheterodin", 860, 256, "M-2 süperheterodin blok şeması: anten → ayarlı preselector → LNA → mixer 1 (taramalı LO₁) → yüksek ilk IF filtresi → mixer 2 (sabit LO₂) → dar ikinci IF filtresi → IF/log yükselteç → dedektör; tarama kontrol register'ı yeşil. Not: dar anlık bant, düşük POI, en iyi hassasiyet.", out)


def g_72():
    out = [metin(20, 24, "M-3 · Zero-IF / homodyne — LO = RF, doğrudan baseband I/Q", "s-baslik")]
    out.append(sym("anten", 20, 60, "anten"))
    out.append(ok(80, 80, 120, 80))
    out.append(sym("bpf", 120, 60, "BPF"))
    out.append(ok(180, 80, 220, 80))
    out.append(sym("amp", 220, 60, "LNA"))
    # bölünme
    out.append(ok(280, 80, 320, 80, uc=False))
    out.append(ok(320, 80, 320, 40, uc=False))
    out.append(ok(320, 80, 320, 130, uc=False))
    out.append(ok(320, 40, 360, 40))
    out.append(ok(320, 130, 360, 130))
    out.append(sym("mixer", 360, 20, None))
    out.append(sym("mixer", 360, 110, None))
    out.append(sym("lo", 360, 175, "LO = f_RF"))
    out.append(ok(390, 175, 390, 150, "saat"))
    out.append(kutu(440, 168, 48, 26, "blok", 4))
    out.append(metin(464, 185, "0° / 90°", "s-mono2", "middle"))
    out.append(ok(390, 110, 390, 60, "saat", uc=False))
    out.append(metin(398, 92, "90°", "s-kucuk"))
    for yy, et in ((40, "I"), (130, "Q")):
        out.append(ok(420, yy, 460, yy))
        out.append(sym("lpf", 460, yy - 20, f"LPF ({et})", "baseband"))
        out.append(ok(520, yy, 560, yy))
        out.append(sym("amp", 560, yy - 20, "VGA"))
        out.append(ok(620, yy, 660, yy))
        out.append(sym("adc", 660, yy - 20, f"ADC {et}", "düşük fs"))
        out.append(ok(720, yy, 760, yy, "sayisal"))
        out.append(metin(764, yy + 4, f"{et}[n]", "s-mono s-vurgu"))
    out.append(kutu(20, 218, 820, 58, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 236, "Image problemi yok (image = sinyalin kendisi) ama üç yeni dert: DC ofset (LO kendi kendine karışır), I/Q dengesizliği (bir 'iç image' üretir) ve LO sızıntısı.", "s-kucuk"))
    out.append(metin(30, 252, "1/f gürültüsü baseband'de sinyalin üstüne biner. Entegre alıcılarda (tek çip) standarttır; sayısal I/Q düzeltme ile EH bantlarına da girer.", "s-kucuk"))
    out.append(metin(30, 268, "Kırmızı olmayan iki yol da analog (altın): I ve Q ayrı ADC'lerle örneklenir — ADC hızı yalnızca sinyal bandı kadar.", "s-kucuk"))
    yaz("g-72", "zero-if", 860, 288, "M-3 zero-IF/homodyne blok şeması: anten → BPF → LNA → iki mixer (LO = RF, 0° ve 90° faz) → baseband LPF → VGA → iki ADC → I[n] ve Q[n]. Not: image yok, ama DC ofset, I/Q dengesizliği ve LO sızıntısı.", out)


def g_73():
    out = [metin(20, 24, "M-4 · IFM (anlık frekans ölçer) — gecikme hattı diskriminatörü: faz farkı → frekans", "s-baslik")]
    out.append(sym("anten", 20, 60, "anten"))
    out.append(ok(80, 80, 120, 80))
    out.append(sym("limiter", 120, 60, "limiter / amp", "sabit genlik"))
    out.append(ok(180, 80, 230, 80, uc=False))
    out.append(ok(230, 80, 230, 40, uc=False)); out.append(ok(230, 80, 230, 130, uc=False))
    out.append(ok(230, 40, 300, 40)); out.append(ok(230, 130, 300, 130))
    out.append(sym("gecikme", 300, 110, "gecikme hattı τ", "faz = 2π·f·τ"))
    out.append(kutu(300, 22, 60, 36, "blok-analog", 4)); out.append(metin(330, 44, "τ = 0", "s-mono2", "middle"))
    out.append(ok(360, 40, 420, 60, "analog", d="M360 40 L420 66")); out.append(ok(360, 130, 420, 100, "analog", d="M360 130 L420 104"))
    out.append(kutu(420, 50, 100, 70, "blok-analog", 6))
    out.append(metin(470, 78, "faz korelatörü", "s-metin", "middle")); out.append(metin(470, 96, "cos φ, sin φ", "s-mono2", "middle"))
    for yy, et in ((60, "cos φ"), (110, "sin φ")):
        out.append(ok(520, yy, 570, yy))
        out.append(sym("adc", 570, yy - 20, f"ADC ({et})"))
        out.append(ok(630, yy, 670, yy, "sayisal"))
    out.append(kutu(670, 50, 110, 70, "blok", 6))
    out.append(metin(725, 78, "atan2 / tablo", "s-metin", "middle")); out.append(metin(725, 96, "f = φ / (2π·τ)", "s-mono2", "middle"))
    out.append(ok(780, 85, 830, 85, "sayisal")); out.append(metin(834, 89, "f", "s-mono s-vurgu"))
    out.append(kutu(20, 176, 820, 58, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 194, "Tek darbede (100 ns içinde) frekans verir; genlik bilgisi limiter'da atılır. Belirsizlik aralığı 1/τ: kaba (kısa τ) ve ince (uzun τ) birkaç korelatör birlikte kullanılır.", "s-kucuk"))
    out.append(metin(30, 210, "Zayıf noktası eşzamanlı sinyal: iki darbe üst üste gelirse tek ve yanlış bir frekans okur. Tipik olarak CVR ile birlikte RWR'lerde kullanılır.", "s-kucuk"))
    out.append(metin(30, 226, "Sayısal IFM: aynı ilke DDC çıkışında ardışık örneklerin faz farkıyla (anlık frekans) yapılır — Bölüm 25'in konusu.", "s-kucuk"))
    yaz("g-73", "ifm", 860, 246, "M-4 IFM blok şeması: anten → limiter/yükselteç → ikiye böl → gecikme hattı τ ve gecikmesiz kol → faz korelatörü (cos φ, sin φ) → iki ADC → atan2 tablosu → frekans. Not: tek darbede frekans, eşzamanlı sinyal zayıflığı.", out)


def g_74():
    out = [metin(20, 24, "M-5 · Analog kanallaştırılmış almaç — filtre bankası: her kanal küçük bir CVR", "s-baslik")]
    out.append(sym("anten", 20, 100, "anten"))
    out.append(ok(80, 120, 120, 120))
    out.append(sym("amp", 120, 100, "LNA"))
    out.append(ok(180, 120, 220, 120))
    out.append(kutu(220, 40, 50, 160, "blok-analog", 6)); out.append(metin(245, 116, "güç", "s-kucuk", "middle")); out.append(metin(245, 130, "bölücü", "s-kucuk", "middle"))
    kanallar = [("f₁", 50), ("f₂", 95), ("f₃", 140), ("⋮", 185), ("f_N", 230)]
    for et, yy in kanallar:
        if et == "⋮":
            out.append(metin(330, yy + 8, "⋮", "s-metin", "middle")); out.append(metin(580, yy + 8, "⋮", "s-metin", "middle")); continue
        out.append(ok(270, yy, 300, yy))
        out.append(sym("bpf", 300, yy - 20, None)); out.append(metin(330, yy - 24, et, "s-mono2", "middle"))
        out.append(ok(360, yy, 400, yy))
        out.append(sym("diyot", 400, yy - 20, None))
        out.append(ok(460, yy, 500, yy))
        out.append(sym("amp", 500, yy - 20, None))
        out.append(ok(560, yy, 600, yy))
        out.append(sym("cmp", 600, yy - 20, None, cikis="sayisal") if False else sym("cmp", 600, yy - 20, None))
        out.append(ok(660, yy, 700, yy, "sayisal"))
    out.append(metin(430, 262, "dedektör", "s-kucuk", "middle")); out.append(metin(530, 262, "video amp", "s-kucuk", "middle")); out.append(metin(630, 262, "eşik", "s-kucuk", "middle"))
    out.append(kutu(700, 40, 120, 210, "blok", 6))
    out.append(metin(760, 130, "kodlayıcı /", "s-metin", "middle")); out.append(metin(760, 148, "öncelik mantığı", "s-metin", "middle")); out.append(metin(760, 170, "kanal no → f", "s-mono2", "middle"))
    out.append(ok(820, 145, 850, 145, "sayisal"))
    out.append(kutu(20, 280, 820, 44, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 298, "N kanal aynı anda dinler: eşzamanlı sinyal başarımı ve POI yüksek, hassasiyet kanal bandına göre (dar kanal → iyi). Bedel: N adet filtre + dedektör → hacim, güç, maliyet.", "s-kucuk"))
    out.append(metin(30, 314, "Kanal kenarındaki sinyal iki kanalda birden görünür ('rabbit ears'); frekans doğruluğu kanal genişliğiyle sınırlı. Sayısal karşılığı M-9.", "s-kucuk"))
    yaz("g-74", "analog-kanallastirilmis", 860, 336, "M-5 analog kanallaştırılmış almaç blok şeması: anten → LNA → güç bölücü → N paralel kanal (BPF → dedektör → video yükselteç → eşik) → kodlayıcı/öncelik mantığı → kanal numarası. Not: eşzamanlı sinyal ve POI yüksek, hacim ve maliyet yüksek.", out)


def g_75():
    out = [metin(20, 24, "M-6 · Compressive (microscan) almaç — hızlı tarama + dispersif hat; kısa tarih: akusto-optik (Bragg cell)", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="amp", ad="LNA"), dict(sym="mixer", ad="mixer"), dict(sym="bpf", ad="IF filtre"),
                    dict(sym="blok", ad="dispersif gecikme", alt="SAW chirp filtre"), dict(sym="diyot", ad="dedektör"), dict(sym="cmp", ad="eşik + zaman", alt="t → f", cikis="sayisal")], 20, 60, 100)
    out.append(z)
    out.append(metin(450, 76, "τ(f)", "s-mono2", "middle"))
    out.append(sym("lo", 200, 130, "chirp LO", "hızlı süpürme"))
    out.append(ok(230, 130, 230, 100, "saat"))
    out.append(kutu(300, 126, 240, 48, "blok", 6, ' opacity=".9"'))
    out.append(metin(310, 144, "LO frekansı süpürülür; dispersif hat", "s-kucuk")); out.append(metin(310, 160, "chirp'i tek darbeye sıkıştırır → tepe zamanı = frekans", "s-kucuk"))
    out.append(ok(xe, 80, xe + 30, 80, "sayisal")); out.append(metin(xe + 34, 84, "f, PA", "s-kucuk s-vurgu"))
    # akusto-optik mini
    out.append(kutu(20, 196, 820, 70, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 214, "Akusto-optik (Bragg cell) almaç — tarih notu: RF sinyali bir kristalde ses dalgasına, lazer ışığı bu 'kırınım ağı'ndan frekansa orantılı açıyla saparak", "s-kucuk"))
    out.append(metin(30, 230, "fotodedektör dizisine düşer: her piksel bir frekans kanalı. 1970–80'lerde geniş anlık bant + çok sinyal için çekiciydi; dinamik aralığı (~30–40 dB) ve", "s-kucuk"))
    out.append(metin(30, 246, "kalibrasyon güçlüğü nedeniyle yerini sayısal FFT/kanallaştırıcıya bıraktı. Compressive almaç da aynı kaderi paylaştı: FFT, 'analog Fourier dönüşümü'nü gereksiz kıldı.", "s-kucuk"))
    out.append(metin(30, 262, "İkisi de Fourier dönüşümünü analog yolla yapıyordu; bugün aynı işlev M-9'un içindedir.", "s-kucuk s-altin"))
    yaz("g-75", "compressive", 860, 278, "M-6 compressive (microscan) almaç blok şeması: anten → LNA → mixer (hızlı süpürülen chirp LO) → IF filtre → dispersif gecikme hattı (SAW chirp filtre) → dedektör → eşik ve zaman ölçümü, tepe zamanı frekansa karşılık gelir. Altta akusto-optik Bragg cell almacın kısa tarih notu.", out)


def g_76():
    out = [metin(20, 24, "M-7 · Sayısal IF almaç — süperhet ön uç + hızlı ADC + DDC: bu kılavuzun referans zinciri", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="limiter", ad="limiter"), dict(sym="amp", ad="LNA"), dict(sym="bpf", ad="preselector"),
                    dict(sym="mixer", ad="mixer"), dict(sym="bpf", ad="IF filtre", alt="1.8 GHz"), dict(sym="amp", ad="IF amp"), dict(sym="lpf", ad="AAF"),
                    dict(sym="adc", ad="ADC", alt="2.4 GSPS", cikis="sayisal")], 20, 60, 88)
    out.append(z)
    out.append(sym("lo", 342, 130, "LO 7.6 GHz", "PLL"))
    out.append(ok(372, 130, 372, 100, "saat"))
    out.append(sym("saat", 694, 130, "örnekleme saati", "düşük jitter"))
    out.append(ok(724, 130, 724, 100, "saat"))
    # sayısal devam (ikinci satır)
    out.append(ok(xe, 80, 840, 80, "sayisal", uc=False)); out.append(ok(840, 80, 840, 200, "sayisal", uc=False)); out.append(ok(840, 200, 700, 200, "sayisal", uc=False))
    z2, xe2 = zincir([dict(sym="mixer-d", ad="⊗ NCO", alt="600 MHz", alan="sayisal"), dict(sym="fir", ad="FIR / CIC", alan="sayisal"), dict(sym="dec", ad="↓8", alan="sayisal"),
                      dict(sym="zarf", ad="zarf", alan="sayisal"), dict(sym="cmp", ad="CFAR", alan="sayisal"), dict(sym="fifo", ad="PDW FIFO", alan="sayisal")], 100, 180, 100)
    # zinciri sağdan sola göstermek yerine soldan sağa çiz, giriş okunu sola bağla
    out.append(z2)
    out.append(ok(700, 200, 100, 200, "sayisal", d="M700 200 H860 V150 H60 V200 H100"))
    out.append(sym("nco", 100, 240, None))
    out.append(ok(130, 240, 130, 220, "sayisal"))
    out.append(sym("reg", 20, 240, "PS register"))
    out.append(ok(80, 260, 100, 260, "kontrol"))
    out.append(kutu(240, 246, 600, 30, "blok", 6, ' opacity=".8"'))
    out.append(metin(250, 265, "Analog–sayısal sınır IF'te: ADC'den sonrası FPGA. Frekans doğruluğu NCO/FFT'den, kanal seçiciliği sayısal filtreden gelir; bant ADC'nin Nyquist bölgesi kadar.", "s-kucuk"))
    yaz("g-76", "sayisal-if", 860, 290, "M-7 sayısal IF almaç blok şeması: anten → limiter → LNA → preselector → mixer (LO 7.6 GHz) → IF filtre 1.8 GHz → IF yükselteç → anti-alias → ADC 2.4 GSPS; sayısal tarafta NCO ile kompleks mixer → FIR/CIC → decimation ↓8 → zarf → CFAR → PDW FIFO; PS register'ları yeşil.", out)


def g_77():
    out = [metin(20, 24, "M-8 · Direct RF sampling almaç — mixer yok: LNA'dan sonra doğrudan ADC, kanal seçimi tamamen sayısal", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="limiter", ad="limiter"), dict(sym="amp", ad="LNA"), dict(sym="bpf", ad="Nyquist bandı BPF", alt="bölge seçici"),
                    dict(sym="att", ad="att / AGC"), dict(sym="amp", ad="ADC sürücü"), dict(sym="adc", ad="RF ADC", alt="çok GSPS", cikis="sayisal"),
                    dict(sym="mixer-d", ad="⊗ NCO", alan="sayisal"), dict(sym="fir", ad="DDC", alan="sayisal")], 20, 60, 92)
    out.append(z)
    out.append(sym("saat", 550, 130, "örnekleme saati", "jitter kritik"))
    out.append(ok(580, 130, 580, 100, "saat"))
    out.append(sym("nco", 664, 130, None)); out.append(ok(694, 130, 694, 100, "sayisal"))
    out.append(ok(xe, 80, xe + 30, 80, "sayisal")); out.append(metin(xe + 34, 84, "I/Q", "s-mono s-vurgu"))
    out.append(kutu(20, 196, 820, 74, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 214, "Frekans planı ortadan kalkmaz, ADC'ye taşınır: hangi Nyquist bölgesi, harmonikler ve interleaving spur'ları nereye katlanır (Bölüm 8, 10). LO faz gürültüsünün yerini saat jitter'ı alır.", "s-kucuk"))
    out.append(metin(30, 230, "Kazanç: image yok, LO sızıntısı yok, aynı ADC'den çok kanal (birden fazla NCO), anında yeniden ayar. Bedel: ADC'nin dinamik aralığı bütün bantla paylaşılır — güçlü", "s-kucuk"))
    out.append(metin(30, 246, "tek sinyal tüm bandı doyurur; analog seçicilik yalnızca Nyquist bandı filtresi kadardır. RFSoC sınıfı çipler bu mimariyi tek yongaya sığdırır.", "s-kucuk"))
    out.append(metin(30, 262, "Referans senaryodan farkı: mixer ve IF katları yok; 9.4 GHz doğrudan (ör. 5. Nyquist bölgesinden) örneklenir.", "s-kucuk s-altin"))
    yaz("g-77", "direct-rf", 860, 282, "M-8 direct RF sampling almaç blok şeması: anten → limiter → LNA → Nyquist bandı seçici BPF → zayıflatıcı/AGC → ADC sürücü → çok GSPS RF ADC → NCO ile kompleks mixer → DDC → I/Q; örnekleme saati jitter kritik. Not: frekans planı ADC'ye taşınır, image ve LO sızıntısı yok.", out)


def g_78():
    out = [metin(20, 24, "M-9 · Sayısal kanallaştırılmış almaç — polyphase filtre bankası + FFT: N kanal, tek ADC", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="amp", ad="LNA"), dict(sym="bpf", ad="BPF"), dict(sym="adc", ad="ADC", alt="geniş bant", cikis="sayisal")], 20, 60, 92)
    out.append(z)
    out.append(kutu(320, 30, 90, 100, "blok", 6)); out.append(metin(365, 70, "seri → paralel", "s-kucuk", "middle")); out.append(metin(365, 86, "(↓M komütatör)", "s-mono2", "middle"))
    out.append(ok(xe, 80, 320, 80, "sayisal"))
    out.append(kutu(440, 30, 110, 100, "blok", 6)); out.append(metin(495, 66, "polyphase", "s-metin", "middle")); out.append(metin(495, 82, "FIR bankası", "s-metin", "middle")); out.append(metin(495, 98, "E₀(z) … E_{M−1}(z)", "s-mono2", "middle"))
    for yy in (45, 65, 85, 105, 120):
        out.append(ok(410, yy, 440, yy, "sayisal"))
        out.append(ok(550, yy, 580, yy, "sayisal"))
    out.append(sym("fft", 580, 60, "M-nokta FFT", "her M örnekte bir"))
    for i, yy in enumerate((45, 65, 85, 105, 120)):
        out.append(ok(640, yy, 690, yy, "sayisal"))
        out.append(kutu(690, yy - 8, 70, 16, "blok", 3))
        out.append(metin(725, yy + 4, f"kanal {i if i < 4 else 'M−1'}" if i != 3 else "⋮", "s-mono2", "middle"))
        out.append(ok(760, yy, 790, yy, "sayisal"))
    out.append(kutu(790, 30, 60, 100, "blok", 6)); out.append(metin(820, 74, "zarf +", "s-kucuk", "middle")); out.append(metin(820, 88, "CFAR", "s-kucuk", "middle")); out.append(metin(820, 102, "/ kanal", "s-kucuk", "middle"))
    out.append(kutu(20, 160, 820, 74, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 178, "M-5'in sayısal ikizi: N kanal bir kez tasarlanır, filtre şekli her kanalda birebir aynıdır (analogda imkânsız). Kanal başına hassasiyet dar banda göre, POI ≈ %100,", "s-kucuk"))
    out.append(metin(30, 194, "eşzamanlı sinyal kanal sayısı kadar. FFT çıkışının her bin'i bir kanal; polyphase FIR, düz FFT'nin yaprak sızıntısını ve kenar 'tavşan kulaklarını' düzeltir.", "s-kucuk"))
    out.append(metin(30, 210, "Karmaşıklığı en yüksek mimari: bellek, DSP slice ve kanal-arası mantık (aynı darbe komşu kanallarda). Bölüm 17 (kanallaştırma) ve 18 (FFT) ayrıntıyı verir.", "s-kucuk"))
    out.append(metin(30, 226, "Referans zincirin tek kanallı DDC'si bu yapının M = 1 halidir.", "s-kucuk s-altin"))
    yaz("g-78", "sayisal-kanallastirilmis", 860, 246, "M-9 sayısal kanallaştırılmış almaç blok şeması: anten → LNA → BPF → geniş bant ADC → seri-paralel komütatör → polyphase FIR bankası → M-nokta FFT → M kanal → kanal başına zarf ve CFAR. Not: analog filtre bankasının sayısal ikizi, en yüksek karmaşıklık.", out)


def g_79():
    out = [metin(20, 24, "M-10 · Monobit almaç — 1 bitlik ADC + FFT: en ucuz geniş bant frekans ölçer (kavram)", "s-baslik")]
    z, xe = zincir([dict(sym="anten", ad="anten"), dict(sym="limiter", ad="limiter / amp", alt="sabit genlik"), dict(sym="bpf", ad="BPF"),
                    dict(sym="cmp", ad="1-bit ADC", alt="işaret karşılaştırıcı", cikis="sayisal"), dict(sym="fft", ad="monobit FFT", alt="çarpımsız (±1, ±j)", alan="sayisal"),
                    dict(sym="cmp", ad="tepe bul", alan="sayisal")], 20, 60, 110)
    out.append(z)
    out.append(sym("saat", 316, 130, "çok yüksek fs", "(≈ 2.5 GSPS+)")); out.append(ok(346, 130, 346, 100, "saat"))
    out.append(ok(xe, 80, xe + 30, 80, "sayisal")); out.append(metin(xe + 34, 84, "f (kaba), TOA", "s-kucuk s-vurgu"))
    out.append(kutu(20, 190, 820, 60, "blok", 6, ' opacity=".8"'))
    out.append(metin(30, 208, "Girişin yalnızca işareti örneklenir; FFT'nin twiddle çarpanları da ±1, ±j'ye yuvarlanır → çarpma yok, çok küçük mantık, çok yüksek fs. Tek sinyalde frekans doğruluğu şaşırtıcı iyidir.", "s-kucuk"))
    out.append(metin(30, 224, "Bedeli dinamik aralık: 1 bit, güçlü sinyalin yanındaki zayıfı yutar (~20 dB anlık DR, doğrulanmadı) ve eşzamanlı iki sinyalde güçlü olan kazanır. Genlik bilgisi yoktur.", "s-kucuk"))
    out.append(metin(30, 240, "Kavramsal önemi: 'bit sayısı' ile 'bant genişliği' arasındaki takasın en uç noktası; IFM'in sayısal, FFT tabanlı akrabası.", "s-kucuk s-altin"))
    yaz("g-79", "monobit", 860, 262, "M-10 monobit almaç blok şeması: anten → limiter/yükselteç → BPF → 1-bit ADC (işaret karşılaştırıcı, çok yüksek fs) → çarpımsız monobit FFT → tepe bulma → kaba frekans ve TOA. Not: çok küçük mantık, çok düşük dinamik aralık.", out)


def g_7a():
    """Tarihsel / evrimsel harita: on yıllar × mimariler, evrim okları."""
    W, H = 920, 470
    x0, x1 = 60, W - 20
    yillar = list(range(1940, 2030, 10))
    out = [metin(x0, 22, "Almaç mimarilerinin evrim haritası (yaklaşık on yıllar; açık literatüre göre, ± bir on yıl)", "s-baslik")]

    def X(y):
        return x0 + (y - 1940) / (2025 - 1940) * (x1 - x0)
    for y in yillar:
        out.append(f'<line x1="{X(y):.1f}" y1="40" x2="{X(y):.1f}" y2="{H - 60}" class="izgara"/>')
        out.append(metin(X(y), H - 46, f"{y}", "s-mono2", "middle"))
    # üç şerit: genlik/zaman (CVR soyu), frekans ölçüm (IFM soyu), süperhet soyu, kanallaştırma soyu
    seritler = [("zarf soyu", 60), ("anlık frekans soyu", 140), ("süperhet soyu", 220), ("kanallaştırma soyu", 300)]
    for ad, yy in seritler:
        out.append(metin(x0 + 4, yy - 8, ad, "s-kucuk s-altin"))
        out.append(f'<line x1="{x0}" y1="{yy + 40}" x2="{x1}" y2="{yy + 40}" stroke="var(--line-2)" stroke-dasharray="3 5"/>')
    kutular = [  # (id, ad, yıl_bas, şerit_y, alan, genişlik)
        ("M-1", "CVR / TRF", 1942, 60, "analog", 90),
        ("M-4", "IFM", 1957, 140, "analog", 70),
        ("M-2", "süperheterodin (taramalı)", 1945, 220, "analog", 150),
        ("M-5", "analog kanallaştırılmış", 1968, 300, "analog", 130),
        ("M-6", "compressive · akusto-optik", 1972, 140, "analog", 150),
        ("M-3", "zero-IF (entegre)", 1988, 220, "analog", 110),
        ("M-7", "sayısal IF", 1992, 220, "sayisal", 100),
        ("M-10", "monobit", 1998, 140, "sayisal", 70),
        ("M-9", "sayısal kanallaştırılmış", 2000, 300, "sayisal", 140),
        ("M-8", "direct RF sampling", 2012, 220, "sayisal", 110),
    ]
    poz = {}
    for mid, ad, yil, yy, alan, gw in kutular:
        xx = X(yil)
        cls = "blok-analog" if alan == "analog" else "blok"
        out.append(kutu(xx, yy, gw, 34, cls, 6))
        out.append(metin(xx + 6, yy + 14, mid, "s-mono2"))
        out.append(metin(xx + 6, yy + 28, ad, "s-kucuk"))
        poz[mid] = (xx, yy, gw)
    def bag(a, b, tur="sayisal", not_=None):
        xa, ya, ga = poz[a]; xb, yb, gb = poz[b]
        d = f"M{xa + ga:.1f} {ya + 17} C{xa + ga + 40:.1f} {ya + 17} {xb - 40:.1f} {yb + 17} {xb:.1f} {yb + 17}"
        out.append(f'<path d="{d}" class="yol-{tur}" fill="none" marker-end="url(#ok-{tur})" opacity=".9"/>')
        if not_:
            out.append(metin((xa + ga + xb) / 2, (ya + yb) / 2 + 8, not_, "s-kucuk", "middle"))
    bag("M-1", "M-4", "analog", "+ frekans")
    bag("M-2", "M-7", "sayisal", "IF'te ADC")
    bag("M-7", "M-8", "sayisal", "ADC RF'e")
    bag("M-5", "M-9", "sayisal", "filtre bankası → FFT")
    bag("M-6", "M-9", "sayisal", "analog Fourier → sayısal")
    bag("M-4", "M-10", "sayisal", "1-bit FFT")
    bag("M-2", "M-3", "analog", "IF = 0")
    # sayısal sınır
    out.append(f'<rect x="{X(1990):.1f}" y="40" width="{x1 - X(1990):.1f}" height="{H - 100}" class="spk-sinyal" opacity=".06"/>')
    out.append(metin(X(1990) + 6, 52, "hızlı ADC + FPGA çağı →", "s-kucuk s-vurgu"))
    out.append(metin(x0, H - 20, "Altın kutular analog, mavi kutular sayısal çekirdekli mimariler. Oklar 'hangi fikir hangisine dönüştü' ilişkisidir; tarihler kaynaklara göre ± bir on yıl oynar.", "s-kucuk"))
    out.append(metin(x0, H - 6, "Bugün RWR'lerde M-1 + M-4 ikilisi, ESM/ELINT'te M-7/M-8 + M-9 yaygındır; M-6 ve akusto-optik tarihî ilgi alanıdır.", "s-kucuk"))
    yaz("g-7a", "evrim-haritasi", W, H, "Almaç mimarilerinin tarihsel/evrimsel haritası: 1940'lardan 2020'lere dört soy (zarf, anlık frekans, süperhet, kanallaştırma) üzerinde on mimari; CVR→IFM, süperhet→sayısal IF→direct RF, analog kanallaştırılmış ve compressive→sayısal kanallaştırılmış, IFM→monobit evrim okları; 1990 sonrası hızlı ADC + FPGA çağı vurgulu.", out)


def g_7b():
    """'Analog–sayısal sınır nereye kaydı' şeridi: beş mimari, aynı sekiz durak, ADC'nin yeri."""
    duraklar = ["anten", "LNA / RF", "mixer + IF", "kanal seçimi", "zarf / dedektör", "eşik", "ölçüm", "PDW"]
    satirlar = [
        ("CVR (M-1)", 5, "ADC yok; sayısal olan yalnızca eşik sonrası sayaçlar"),
        ("süperhet + video ADC (M-2)", 5, "ADC zarftan sonra (video): yavaş, düşük bit"),
        ("sayısal IF (M-7)", 3, "ADC IF'te: kanal seçimi ve zarf sayısal"),
        ("direct RF (M-8)", 2, "ADC LNA'dan hemen sonra: mixer de sayısal"),
        ("sayısal kanallaştırılmış (M-9)", 2, "aynı sınır, ama N kanal paralel"),
    ]
    W, H = 900, 380
    x0, cw, rh = 230, 82, 46
    out = [metin(20, 22, "Analog–sayısal sınır nereye kaydı? Aynı sekiz durak, beş mimari; kırmızı çizgi ADC'nin yeri", "s-baslik")]
    for j, d in enumerate(duraklar):
        out.append(metin(x0 + j * cw + cw / 2, 46, d, "s-kucuk", "middle"))
    for i, (ad, sinir, not_) in enumerate(satirlar):
        yy = 60 + i * (rh + 14)
        out.append(metin(x0 - 10, yy + 20, ad, "s-metin", "end"))
        out.append(metin(x0 - 10, yy + 36, not_, "s-kucuk", "end") if False else "")
        for j in range(len(duraklar)):
            cls = "blok-analog" if j < sinir else "blok"
            out.append(kutu(x0 + j * cw + 3, yy, cw - 6, rh - 14, cls, 4))
        px = x0 + sinir * cw
        out.append(f'<line x1="{px:.1f}" y1="{yy - 4}" x2="{px:.1f}" y2="{yy + rh - 10}" stroke="var(--red)" stroke-width="3"/>')
        out.append(metin(px + 5, yy - 6, "ADC", "s-kucuk s-kirmizi"))
        out.append(metin(x0 + 3, yy + rh - 1, not_, "s-kucuk"))
    yy = 60 + 5 * (rh + 14)
    out.append(ok(x0 + 5 * cw + 10, yy, x0 + 2 * cw + 10, yy, "gurultu"))
    out.append(metin(x0 + 3.5 * cw, yy + 16, "sınır sola kaydıkça: analog blok azalır, ADC hızı ve FPGA yükü artar, esneklik ve tekrarlanabilirlik artar", "s-kucuk s-kirmizi", "middle"))
    out.append(metin(20, H - 8, "Altın: analog durak. Mavi: sayısal durak. Her sağa-sol adım, bir analog tasarım problemini (filtre, mixer, dedektör) bir DSP problemine çevirir — bu kılavuzun Kısım III–VIII'i o problemlerdir.", "s-kucuk"))
    yaz("g-7b", "analog-sayisal-sinir", W, H, "Analog–sayısal sınırın kayması: sekiz durak (anten, LNA/RF, mixer+IF, kanal seçimi, zarf, eşik, ölçüm, PDW) beş mimari için altın (analog) veya mavi (sayısal) kutularla; kırmızı çizgi ADC'nin yeri — CVR ve süperhette zarftan sonra, sayısal IF'te IF'te, direct RF ve sayısal kanallaştırılmışta LNA'dan hemen sonra.", out)


URETICILER = {"g-50": g_50, "g-51": g_51, "g-52": g_52, "g-60": g_60, "g-61": g_61, "g-62": g_62,
              "g-70": g_70, "g-71": g_71, "g-72": g_72, "g-73": g_73, "g-74": g_74, "g-75": g_75,
              "g-76": g_76, "g-77": g_77, "g-78": g_78, "g-79": g_79, "g-7a": g_7a, "g-7b": g_7b}


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
