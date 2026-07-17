# -*- coding: utf-8 -*-
"""
qc_shots.py — rozet/kutu yerleşimi kalite kontrol kompozitleri.

annotate.py'deki SPEC'i gerçek screenshot'ların üzerine PIL ile çizer ve
küçültülmüş kontrol görüntülerini qc/ dizinine yazar. Amaç: rozetlerin
hedef UI öğesinin üstüne oturduğunu gözle doğrulamak.

Kullanım: python build/qc_shots.py [NN NN ...]   (argümansız: hepsi)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
from annotate import SPEC  # noqa: E402

SHOTS = ROOT / "assets" / "screenshots"
QC = ROOT / "build" / "qc"
QC.mkdir(exist_ok=True)

QC_W = 1300


def qc(no: str, spec: dict) -> None:
    png = SHOTS / f"shot-{no}.png"
    if not png.exists():
        print(f"atlandı: {no}")
        return
    img = Image.open(png).convert("RGB")
    w, h = img.size
    d = ImageDraw.Draw(img)
    r = max(14, round(w * 0.011))
    sw = max(2, round(w * 0.0018))
    try:
        font = ImageFont.truetype("segoeui.ttf", round(r * 1.2))
    except OSError:
        font = ImageFont.load_default()

    def badge(x, y, n):
        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 184, 75),
                  outline=(20, 16, 10), width=max(1, sw // 2))
        d.text((x, y), str(n), fill=(20, 16, 10), font=font, anchor="mm")

    for (bx, by, bw, bh, bn) in spec.get("boxes", []):
        px, py = round(bx * w), round(by * h)
        pw, ph = round(bw * w), round(bh * h)
        d.rectangle([px, py, px + pw, py + ph], outline=(232, 184, 75), width=sw)
        badge(px, py, bn)
    for i, (bx, by) in enumerate(spec.get("badges", []),
                                 start=len(spec.get("boxes", [])) + 1):
        badge(round(bx * w), round(by * h), i)

    if w > QC_W:
        img = img.resize((QC_W, round(h * QC_W / w)), Image.LANCZOS)
    out = QC / f"qc-{no}.png"
    img.save(out)
    print(f"qc: {out.name} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    hedef = sys.argv[1:] or sorted(SPEC.keys())
    for no in hedef:
        qc(no, SPEC.get(no, {}))
