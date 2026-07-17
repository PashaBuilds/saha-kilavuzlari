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
    "01": {"boxes": [(0.012, 0.058, 0.082, 0.700, 1),
                     (0.100, 0.088, 0.170, 0.377, 2),
                     (0.267, 0.085, 0.720, 0.680, 3)]},
    "02": {"boxes": [(0.106, 0.144, 0.135, 0.023, 1),
                     (0.100, 0.440, 0.116, 0.027, 2)]},
    "04": {"boxes": [(0.283, 0.195, 0.700, 0.492, 1)]},
    "05": {"boxes": [(0.344, 0.483, 0.052, 0.032, 1),
                     (0.289, 0.442, 0.073, 0.100, 2),
                     (0.091, 0.462, 0.157, 0.078, 3)]},
    "06": {"boxes": [(0.271, 0.146, 0.085, 0.028, 1),
                     (0.271, 0.175, 0.096, 0.033, 2)]},
    "07": {"boxes": [(0.091, 0.462, 0.157, 0.078, 1),
                     (0.740, 0.356, 0.072, 0.088, 2)]},
    "17": {"boxes": [(0.265, 0.141, 0.150, 0.116, 1),
                     (0.482, 0.124, 0.053, 0.134, 2),
                     (0.538, 0.124, 0.072, 0.134, 3)]},
    "21": {"boxes": [(0.336, 0.253, 0.187, 0.239, 1),
                     (0.658, 0.253, 0.104, 0.239, 2),
                     (0.715, 0.362, 0.262, 0.030, 3)]},
    "27": {"boxes": [(0.269, 0.190, 0.338, 0.038, 1),
                     (0.269, 0.224, 0.338, 0.022, 2)]},
    "28": {"boxes": [(0.520, 0.269, 0.146, 0.030, 1),
                     (0.088, 0.271, 0.160, 0.106, 2)]},
    "29": {"boxes": [(0.015, 0.133, 0.358, 0.106, 1)]},

    # ---------- US Re-customize diyaloğu (2080x1561) ----------
    "08": {"boxes": [(0.01, 0.30, 0.16, 0.20, 1),
                     (0.185, 0.235, 0.805, 0.675, 2),
                     (0.905, 0.938, 0.068, 0.038, 3)]},
    "09": {"boxes": [(0.180, 0.472, 0.165, 0.095, 1),
                     (0.268, 0.450, 0.065, 0.030, 2),
                     (0.222, 0.274, 0.435, 0.070, 3)]},
    "10": {"boxes": [(0.225, 0.782, 0.125, 0.032, 1),
                     (0.225, 0.815, 0.125, 0.032, 2)]},
    "11": {"boxes": [(0.175, 0.405, 0.29, 0.035, 1)]},
    "12": {"boxes": [(0.215, 0.650, 0.42, 0.065, 1),
                     (0.618, 0.650, 0.155, 0.065, 2)]},
    "13": {"boxes": [(0.215, 0.576, 0.42, 0.036, 1),
                     (0.215, 0.614, 0.42, 0.092, 2)]},
    "14": {"boxes": [(0.183, 0.450, 0.26, 0.165, 1),
                     (0.438, 0.450, 0.295, 0.078, 2),
                     (0.188, 0.618, 0.255, 0.285, 3)]},
    "15": {"boxes": [(0.205, 0.435, 0.165, 0.032, 1),
                     (0.205, 0.467, 0.165, 0.032, 2),
                     (0.205, 0.530, 0.145, 0.032, 3)]},
    "16": {"boxes": [(0.215, 0.436, 0.135, 0.034, 1),
                     (0.215, 0.470, 0.135, 0.034, 2)]},
    "18": {"badges": [(0.09, 0.5)]},

    # ---------- Export Hardware sihirbazı (1578x1339) ----------
    "19": {"boxes": [(0.19, 0.058, 0.62, 0.108, 1)]},
    "20": {"boxes": [(0.042, 0.201, 0.56, 0.050, 1),
                     (0.042, 0.271, 0.90, 0.068, 2)]},

    # ---------- Versal CIPS presets (1578x1389) ----------
    "22": {"boxes": [(0.045, 0.408, 0.75, 0.036, 1),
                     (0.045, 0.492, 0.75, 0.135, 2)]},

    # ---------- Versal Configure PS PMC (1978x1589) ----------
    "23": {"boxes": [(0.18, 0.415, 0.17, 0.033, 1),
                     (0.38, 0.33, 0.28, 0.035, 2)]},
    "24": {"boxes": [(0.245, 0.46, 0.16, 0.035, 1),
                     (0.64, 0.46, 0.175, 0.035, 2)]},

    # ---------- Versal NoC (2560x1762) ----------
    "25": {"boxes": [(0.263, 0.208, 0.225, 0.102, 1),
                     (0.263, 0.438, 0.375, 0.158, 2)]},
    "26": {"boxes": [(0.263, 0.228, 0.158, 0.032, 1),
                     (0.263, 0.312, 0.308, 0.075, 2)]},
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
    # serbest rozetler — numara kutulardan SONRA devam eder
    # (aksi hâlde kutu+rozet karışımı karelerde iki "1" oluşur)
    for i, (bx, by) in enumerate(badges, start=len(boxes) + 1):
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
