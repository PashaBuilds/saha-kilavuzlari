# -*- coding: utf-8 -*-
"""
annotate.py — Katman B açıklama katmanı üreteci.

Her screenshot için assets/svg/ekran-NN.svg üretir: screenshot SVG içine
`__SHOT_NN__` yer tutucusuyla gömülür (build.py base64 enjekte eder),
üstüne numaralı rozetler + vurgu çerçeveleri vektörel olarak çizilir.

Koordinatlar SPEC sözlüğünde 0..1 kesirli (x,y) olarak verilir; badge
görüntünün o noktasına oturur. İsteğe bağlı "box" [x,y,w,h] (kesirli)
vurgu çerçevesi çizer. Böylece ekran çözünürlüğünden bağımsız kalır.

Kullanım: python build/annotate.py
"""
import base64
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "assets" / "screenshots"
SVGDIR = ROOT / "assets" / "svg"

# Her shot: {"badges":[(x,y), ...], "boxes":[(x,y,w,h,badge_no), ...]}
# x,y,w,h hepsi 0..1 kesirli (görüntü boyutundan bağımsız).
# badge, kutunun sol-üst köşesine oturur.
#
# İki tür kare var:
#   - PENCERE kareleri (2560x1400): tüm Vivado penceresi
#   - DİYALOG kareleri: yalnız diyalog penceresi (PrintWindow -Title ile)
SPEC = {
    # ---------- Pencere kareleri (2560x1400) ----------
    "01": {"boxes": [(0.002, 0.05, 0.088, 0.44, 1),
                     (0.10, 0.09, 0.17, 0.29, 2),
                     (0.285, 0.11, 0.545, 0.45, 3)]},
    "02": {"boxes": [(0.103, 0.10, 0.17, 0.032, 1),
                     (0.103, 0.098, 0.10, 0.02, 2)]},
    "04": {"boxes": [(0.285, 0.115, 0.55, 0.45, 1)]},
    "05": {"boxes": [(0.345, 0.26, 0.075, 0.05, 1)],
           "badges": [(0.095, 0.275)]},
    "06": {"boxes": [(0.25, 0.125, 0.115, 0.045, 1),
                     (0.25, 0.155, 0.095, 0.05, 2)]},
    "07": {"boxes": [(0.735, 0.20, 0.075, 0.075, 1)],
           "badges": [(0.095, 0.29)]},
    "17": {"boxes": [(0.245, 0.085, 0.135, 0.02, 1),
                     (0.485, 0.10, 0.075, 0.085, 2),
                     (0.535, 0.10, 0.06, 0.085, 3)]},
    "21": {"boxes": [(0.335, 0.145, 0.115, 0.30, 1),
                     (0.66, 0.145, 0.085, 0.20, 2),
                     (0.685, 0.195, 0.14, 0.045, 3)]},
    "27": {"boxes": [(0.245, 0.085, 0.35, 0.13, 1),
                     (0.245, 0.26, 0.35, 0.045, 2)]},
    "28": {"boxes": [(0.505, 0.155, 0.16, 0.025, 1),
                     (0.093, 0.135, 0.155, 0.135, 2)]},
    "29": {"boxes": [(0.015, 0.135, 0.355, 0.095, 1)]},

    # ---------- US Re-customize diyaloğu (2080x1561) ----------
    "08": {"boxes": [(0.01, 0.30, 0.16, 0.20, 1),
                     (0.19, 0.28, 0.80, 0.56, 2)],
           "badges": [(0.90, 0.915)]},
    "09": {"boxes": [(0.012, 0.325, 0.155, 0.035, 1),
                     (0.225, 0.265, 0.42, 0.075, 2),
                     (0.175, 0.435, 0.16, 0.028, 3)]},
    "10": {"boxes": [(0.22, 0.752, 0.135, 0.03, 1),
                     (0.22, 0.786, 0.135, 0.03, 2)]},
    "11": {"boxes": [(0.175, 0.405, 0.29, 0.035, 1)]},
    "12": {"boxes": [(0.265, 0.235, 0.095, 0.035, 1),
                     (0.63, 0.635, 0.11, 0.075, 2)]},
    "13": {"boxes": [(0.215, 0.555, 0.30, 0.033, 1),
                     (0.215, 0.59, 0.075, 0.14, 2)]},
    "14": {"boxes": [(0.18, 0.42, 0.53, 0.045, 1),
                     (0.44, 0.465, 0.29, 0.045, 2),
                     (0.315, 0.815, 0.42, 0.035, 3)]},
    "15": {"boxes": [(0.205, 0.415, 0.14, 0.033, 1),
                     (0.205, 0.448, 0.14, 0.032, 2),
                     (0.205, 0.48, 0.14, 0.032, 3)]},
    "16": {"boxes": [(0.215, 0.415, 0.135, 0.033, 1),
                     (0.215, 0.448, 0.135, 0.033, 2)]},
    "18": {"badges": [(0.09, 0.5)]},

    # ---------- Export Hardware sihirbazı (1578x1339) ----------
    "19": {"boxes": [(0.19, 0.06, 0.62, 0.09, 1)]},
    "20": {"boxes": [(0.045, 0.16, 0.55, 0.045, 1),
                     (0.045, 0.225, 0.72, 0.05, 2)]},

    # ---------- Versal CIPS presets (1578x1389) ----------
    "22": {"boxes": [(0.045, 0.40, 0.75, 0.13, 1),
                     (0.045, 0.535, 0.75, 0.095, 2)]},

    # ---------- Versal Configure PS PMC (1978x1589) ----------
    "23": {"boxes": [(0.18, 0.415, 0.17, 0.033, 1),
                     (0.38, 0.33, 0.28, 0.035, 2)]},
    "24": {"boxes": [(0.245, 0.46, 0.16, 0.035, 1),
                     (0.64, 0.46, 0.175, 0.035, 2)]},

    # ---------- Versal NoC (2560x1762) ----------
    "25": {"boxes": [(0.20, 0.225, 0.28, 0.085, 1),
                     (0.19, 0.44, 0.36, 0.13, 2)]},
    "26": {"boxes": [(0.32, 0.225, 0.16, 0.04, 1),
                     (0.185, 0.31, 0.38, 0.075, 2)]},
}


def uret(no: str, spec: dict) -> None:
    png = SHOTS / f"shot-{no}.png"
    if not png.exists():
        print(f"atlandı (png yok): {no}")
        return
    w, h = Image.open(png).size
    boxes = spec.get("boxes", [])
    badges = spec.get("badges", [])
    r = max(14, round(w * 0.011))       # badge yarıçapı
    sw = max(2, round(w * 0.0018))      # çizgi kalınlığı
    fs = round(r * 1.15)

    parts = [
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'font-family="Segoe UI, system-ui, sans-serif">',
        f'<image x="0" y="0" width="{w}" height="{h}" '
        f'xlink:href="__SHOT_{no}__" preserveAspectRatio="xMidYMid meet"/>',
    ]
    # vurgu çerçeveleri
    for (bx, by, bw, bh, bn) in boxes:
        px, py = round(bx * w), round(by * h)
        pw, ph = round(bw * w), round(bh * h)
        parts.append(
            f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{r//2}" '
            f'fill="none" stroke="#E8B84B" stroke-width="{sw}"/>')
        parts.append(_badge(px, py, r, fs, sw, bn))
    # serbest rozetler
    for i, (bx, by) in enumerate(badges, start=1):
        parts.append(_badge(round(bx * w), round(by * h), r, fs, sw, i))
    parts.append("</svg>")
    (SVGDIR / f"ekran-{no}.svg").write_text("\n".join(parts), encoding="utf-8")
    print(f"üretildi: ekran-{no}.svg ({len(boxes)+len(badges)} rozet)")


def _badge(x: int, y: int, r: int, fs: int, sw: int, n: int) -> str:
    return (
        f'<g><circle cx="{x}" cy="{y}" r="{r}" fill="#E8B84B" '
        f'stroke="#14100a" stroke-width="{max(1, sw//2)}"/>'
        f'<text x="{x}" y="{y + fs//3}" text-anchor="middle" '
        f'font-size="{fs}" font-weight="700" fill="#14100a">{n}</text></g>')


if __name__ == "__main__":
    for no, spec in SPEC.items():
        uret(no, spec)
