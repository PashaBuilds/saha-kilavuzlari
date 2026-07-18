# -*- coding: utf-8 -*-
"""
qc_sema.py — Katman C şemaları ve Katman A BD export'ları için görsel QC.

Şemalar CSS değişkeni kullandığından tek başına render edilemez; bu script
her şemayı koyu+açık tema değişkenleriyle YAN YANA tek sayfaya koyar ve
headless Chrome ile PNG'ye basar. BD export'ları (sabit renkli) tek kopya
render edilir. Çıktılar build/qc/ altına düşer; gözle denetim için.

Kullanım: python build/qc_sema.py [sema-01 bd-ultrascale ...]  (argümansız: hepsi)
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVGDIR = ROOT / "assets" / "svg"
BDDIR = ROOT / "assets" / "bd-exports"
QC = ROOT / "build" / "qc"
QC.mkdir(exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

KOYU = """--zemin:#0E1116;--kart:#161B22;--kart-2:#1C232D;--cizgi:#2A3340;
--metin:#D7DEE7;--metin-soluk:#8B97A5;--vurgu:#4DA3FF;--altin:#E8B84B;
--yesil:#5BB0A6;--kirmizi:#E06C75;--mor:#B48EAD;--kod-zemin:#10151C;
--vurgu-yumusak:rgba(77,163,255,0.12);--altin-yumusak:rgba(232,184,75,0.10);
--yesil-yumusak:rgba(91,176,166,0.10);--kirmizi-yumusak:rgba(224,108,117,0.10);
--mor-yumusak:rgba(180,142,173,0.10);"""

ACIK = """--zemin:#F6F8FA;--kart:#FFFFFF;--kart-2:#EEF2F6;--cizgi:#D4DCE4;
--metin:#24313F;--metin-soluk:#5D6B7A;--vurgu:#1C6FD4;--altin:#9A7115;
--yesil:#22796F;--kirmizi:#B3392F;--mor:#7C5295;--kod-zemin:#F0F3F6;
--vurgu-yumusak:rgba(28,111,212,0.08);--altin-yumusak:rgba(154,113,21,0.08);
--yesil-yumusak:rgba(34,121,111,0.08);--kirmizi-yumusak:rgba(179,57,47,0.07);
--mor-yumusak:rgba(124,82,149,0.08);"""


def viewbox(svg: str):
    m = re.search(r'viewBox="([\d.\s-]+)"', svg)
    x, y, w, h = (float(v) for v in m.group(1).split())
    return w, h


def suffix_ids(svg: str, sfx: str) -> str:
    svg = re.sub(r'id="([^"]+)"', rf'id="\1{sfx}"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', rf'url(#\1{sfx})', svg)
    svg = re.sub(r'aria-labelledby="([^"]+)"', rf'aria-labelledby="\1{sfx}"', svg)
    return svg


def chrome_shot(html: str, out: Path, w: int, h: int) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as f:
        f.write(html)
        yol = f.name
    subprocess.run([CHROME, "--headless=new", "--disable-gpu",
                    "--hide-scrollbars", f"--screenshot={out}",
                    f"--window-size={w},{h}", f"file:///{yol}"],
                   capture_output=True, timeout=60)
    Path(yol).unlink(missing_ok=True)
    print(f"qc: {out.name}")


def sema_qc(ad: str) -> None:
    yol = SVGDIR / f"{ad}.svg"
    if not yol.exists():
        print(f"atlandı: {ad}")
        return
    svg = yol.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    vw, vh = viewbox(svg)
    pw = 860                       # panel içi svg genişliği
    ph = round(vh * pw / vw)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;display:flex}}
.p{{width:900px;padding:20px;box-sizing:border-box}}
.koyu{{{KOYU}background:#0E1116}}
.acik{{{ACIK}background:#F6F8FA}}
svg{{width:{pw}px;height:auto;display:block}}
</style></head><body>
<div class="p koyu">{suffix_ids(svg, 'D')}</div>
<div class="p acik">{suffix_ids(svg, 'L')}</div>
</body></html>"""
    chrome_shot(html, QC / f"qc-{ad}.png", 1800, ph + 40)


def bd_qc(ad: str) -> None:
    yol = BDDIR / f"{ad}.svg"
    if not yol.exists():
        print(f"atlandı: {ad}")
        return
    svg = yol.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    vw, vh = viewbox(svg)
    pw = 1560
    ph = round(vh * pw / vw)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#fff}}svg{{width:{pw}px;height:auto;display:block}}
</style></head><body>{svg}</body></html>"""
    chrome_shot(html, QC / f"qc-{ad}.png", pw, ph)


if __name__ == "__main__":
    hedef = sys.argv[1:]
    if not hedef:
        hedef = [p.stem for p in sorted(SVGDIR.glob("sema-*.svg"))] + \
                [p.stem for p in sorted(BDDIR.glob("*.svg"))]
    for ad in hedef:
        if ad.startswith("sema-"):
            sema_qc(ad)
        else:
            bd_qc(ad)
