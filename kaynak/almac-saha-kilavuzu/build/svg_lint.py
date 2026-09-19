#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svg_lint.py — şemalarda metin çakışması / taşması bulucu (sezgisel)

  python build/svg_lint.py               → tüm g-*.svg
  python build/svg_lint.py g-14 g-2      → önek filtresi

Her <text>'in kutusunu font-size ve karakter sayısından kestirir (ortalama karakter
genişliği 0.56·em, text-anchor ve transform=translate/rotate(-90) dikkate alınır),
şunları raporlar:
  • TAŞMA: kutu viewBox dışına çıkıyor
  • ÇAKIŞMA: iki metin kutusu üst üste biniyor (aynı <g> içinde ya da genel)
Kesin değil; her bulgu tarayıcıda doğrulanmalı. Amaç denetçiye öncelik listesi vermek.
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "svg"
CSS = (ROOT / "assets" / "css" / "kilavuz.css").read_text(encoding="utf-8")

# sınıf → font boyutu (kilavuz.css'ten)
SINIF_FS = {}
for m in re.finditer(r"svg \.([a-z0-9-]+)\s*\{[^}]*font-size:\s*([\d.]+)px", CSS):
    SINIF_FS[m.group(1)] = float(m.group(2))


def stil_fs(svg_text):
    """SVG içi <style> bloğundaki .x { font-size } tanımları."""
    out = {}
    for m in re.finditer(r"\.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}", svg_text):
        fm = re.search(r"font-size:\s*([\d.]+)px", m.group(2))
        if fm:
            out[m.group(1)] = float(fm.group(1))
    return out


def transform_ofset(t):
    """translate(x,y) ve rotate(-90 …) yakalar; dönüş (dx, dy, dondu)."""
    dx = dy = 0.0
    dondu = False
    if not t:
        return dx, dy, dondu
    for m in re.finditer(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)?\s*\)", t):
        dx += float(m.group(1)); dy += float(m.group(2) or 0)
    if re.search(r"rotate\(\s*-?90", t):
        dondu = True
    return dx, dy, dondu


def lint(path):
    t = path.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', t)
    if not vb:
        return [f"{path.name}: viewBox yok"]
    vx, vy, vw, vh = [float(x) for x in vb.group(1).split()]
    yerel_fs = stil_fs(t)
    bulgular = []
    kutular = []
    # <g transform> yığınını kabaca izle
    g_stack = []
    pos = 0
    tok = re.compile(r"<g\b([^>]*)>|</g>|<text\b([^>]*)>(.*?)</text>", re.S)
    for m in tok.finditer(t):
        if m.group(0).startswith("<g"):
            g_stack.append(transform_ofset(re.search(r'transform="([^"]+)"', m.group(1) or "") and re.search(r'transform="([^"]+)"', m.group(1)).group(1)))
            continue
        if m.group(0) == "</g>":
            if g_stack:
                g_stack.pop()
            continue
        attrs, icerik = m.group(2) or "", m.group(3) or ""
        metin = re.sub(r"<[^>]+>", "", icerik).strip()
        if not metin:
            continue
        def attr(ad, vars=None):
            mm = re.search(rf'\b{ad}="([^"]*)"', attrs)
            return mm.group(1) if mm else None
        try:
            x = float(attr("x") or 0); y = float(attr("y") or 0)
        except ValueError:
            continue
        fs = None
        sm = re.search(r"font-size:\s*([\d.]+)px", attr("style") or "")
        if sm:
            fs = float(sm.group(1))
        if fs is None and attr("font-size"):
            fs = float(re.sub(r"[^\d.]", "", attr("font-size")) or 12)
        if fs is None:
            for c in (attr("class") or "").split():
                if c in yerel_fs:
                    fs = yerel_fs[c]; break
                if c in SINIF_FS:
                    fs = SINIF_FS[c]; break
        if fs is None:
            fs = 12.0
        w = 0.56 * fs * len(metin)
        h = fs
        anchor = attr("text-anchor") or "start"
        sm2 = re.search(r"text-anchor:\s*(\w+)", attr("style") or "")
        if sm2:
            anchor = sm2.group(1)
        dx, dy, dondu = transform_ofset(attr("transform") or "")
        for gx, gy, gd in g_stack:
            dx += gx; dy += gy; dondu = dondu or gd
        if dondu:
            continue  # döndürülmüş eksen etiketleri: atla
        X, Y = x + dx, y + dy
        if anchor == "middle":
            x0 = X - w / 2
        elif anchor == "end":
            x0 = X - w
        else:
            x0 = X
        kutu = (x0, Y - h * 0.8, x0 + w, Y + h * 0.25, metin, fs)
        if kutu[0] < vx - 2 or kutu[2] > vx + vw + 2 or kutu[1] < vy - 2 or kutu[3] > vy + vh + 2:
            bulgular.append(f"  TAŞMA  '{metin[:40]}' (x≈{kutu[0]:.0f}–{kutu[2]:.0f}, y≈{Y:.0f}; viewBox {vw:.0f}×{vh:.0f})")
        kutular.append(kutu)
    for i in range(len(kutular)):
        for j in range(i + 1, len(kutular)):
            a, b = kutular[i], kutular[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 3 and oy > 3:
                bulgular.append(f"  ÇAKIŞMA '{a[4][:32]}' × '{b[4][:32]}' (bindirme {ox:.0f}×{oy:.0f}px)")
    return [f"{path.name}:"] + bulgular if bulgular else []


def main():
    argv = sys.argv[1:]
    dosyalar = sorted(p for p in SVG.glob("g-*.svg") if not argv or any(p.name.startswith(a) for a in argv))
    toplam = 0
    for p in dosyalar:
        b = lint(p)
        if b:
            toplam += len(b) - 1
            print("\n".join(b))
    print(f"\n{len(dosyalar)} dosya, {toplam} sezgisel bulgu (tarayıcıda doğrula).")


if __name__ == "__main__":
    main()
