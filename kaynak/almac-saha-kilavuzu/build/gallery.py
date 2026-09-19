#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gallery.py — şema QA galerisi

  python build/gallery.py            → dist/_galeri-tum.html (tüm şekiller); argümanlar dosya adına eklenir
  python build/gallery.py g-1 g-2    → yalnızca adı bu öneklerle başlayan şekiller (ör. "g-1" → g-10…g-19, g-100…)
  python build/gallery.py --bolum 5 6 7   → bu bölümlerin md'lerinde geçen şekiller

Her şekil koyu ve açık temada yan yana, gerçek sayfa CSS'i ile (symbols.svg dahil)
gösterilir; altında dosya adı ve viewBox. Çıktı `_` önekli olduğundan repoya girmez.
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "svg"
CSS = (ROOT / "assets" / "css" / "kilavuz.css").read_text(encoding="utf-8")
SYM = (SVG / "symbols.svg").read_text(encoding="utf-8")


def secilenler(argv):
    dosyalar = sorted(p for p in SVG.glob("g-*.svg"))
    if not argv:
        return dosyalar
    if argv[0] == "--bolum":
        adlar = set()
        for b in argv[1:]:
            for md in (ROOT / "content").glob(f"{int(b):02d}-*.md"):
                adlar |= set(re.findall(r"\{\{svg:([^|}]+)", md.read_text(encoding="utf-8")))
                adlar |= set(re.findall(r"sema=([^\s]+\.svg)", md.read_text(encoding="utf-8")))
        return [SVG / a.strip() for a in sorted(adlar) if (SVG / a.strip()).exists()]
    return [p for p in dosyalar if any(p.name.startswith(a) for a in argv)]


def main():
    dosyalar = secilenler(sys.argv[1:])
    kartlar = []
    for p in dosyalar:
        svg = re.sub(r"<\?xml[^>]*\?>\s*", "", p.read_text(encoding="utf-8").strip())
        vb = re.search(r'viewBox="([^"]+)"', svg)
        kartlar.append(f'''
<section class="kart"><h2>{p.name} <small>viewBox {vb.group(1) if vb else "?"}</small></h2>
<div class="cift">
  <div class="tema" data-theme="dark"><figure class="sema">{svg}</figure></div>
  <div class="tema" data-theme="light"><figure class="sema">{svg}</figure></div>
</div></section>''')
    html = f'''<!DOCTYPE html><html lang="tr" data-theme="dark"><head><meta charset="utf-8"><title>Şema galerisi</title>
<style>{CSS}
/* galeri */
body {{ padding: 20px; }}
.kart {{ margin: 0 0 40px; }}
.kart h2 {{ font-size: 16px; margin: 0 0 8px; font-family: var(--mono); }}
.kart h2 small {{ color: var(--ink-3); font-weight: 400; }}
.cift {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.tema {{ padding: 12px; border-radius: 12px; }}
.tema[data-theme="dark"] {{ --bg:#0E1116; --bg-2:#161B22; --bg-3:#1D2430; --line:#2A3140; --line-2:#3A4356; --ink:#E6EDF3; --ink-2:#8B949E; --ink-3:#6A7380; --accent:#4DA3FF; --gold:#E8B84B; --green:#5BB0A6; --red:#F0716B; --purple:#B48EAD; --accent-soft:#14263C; --gold-soft:#2C2413; --green-soft:#122A27; --red-soft:#2E1817; --purple-soft:#261F2A; --dia-panel:#131820; --dia-blok:#1C2330; --dia-blok-2:#242D3D; --dia-grid:#1E2634; --dia-noise:#3A4356; background: var(--bg); }}
.tema[data-theme="light"] {{ --bg:#F7F8FA; --bg-2:#FFFFFF; --bg-3:#EDF0F4; --line:#D9DEE6; --line-2:#C2C9D4; --ink:#1B2430; --ink-2:#57606C; --ink-3:#7B8492; --accent:#0B67C2; --gold:#8A5D00; --green:#16766B; --red:#C2352E; --purple:#6E4A8A; --accent-soft:#E3EFFB; --gold-soft:#FAF0D7; --green-soft:#DEF0ED; --red-soft:#FBE4E2; --purple-soft:#EFE6F4; --dia-panel:#FFFFFF; --dia-blok:#EFF2F6; --dia-blok-2:#E2E8F0; --dia-grid:#E6EAF0; --dia-noise:#C9D0DA; background: var(--bg); }}
figure.sema {{ margin: 0; width: 100%; max-width: none; }}
@media (max-width: 1100px) {{ .cift {{ grid-template-columns: 1fr; }} }}
</style></head><body>{SYM}
<h1 style="font-size:20px">Şema galerisi — {len(kartlar)} şekil (sol koyu, sağ açık)</h1>
{"".join(kartlar)}
</body></html>'''
    etiket = "-".join(a.lstrip("-") for a in sys.argv[1:]) or "tum"
    out = ROOT / "dist" / f"_galeri-{etiket}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"OK {out} — {len(kartlar)} şekil")


if __name__ == "__main__":
    main()
