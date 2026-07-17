# -*- coding: utf-8 -*-
"""
crop_bd.py — Katman A kırpımları: tam BD SVG'sini bir viewBox penceresiyle
kırparak PS-yakın / CIPS-NoC-yakın export'ları üretir.

Tam SVG bir <image> data URI olarak gömülür; dış viewBox kırpım bölgesini
belirler. Böylece kırpım da vektörel kalır ve zoom/pan'da net görünür.
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "assets" / "bd-exports"

# (kaynak, hedef, native_w, native_h, [vbx, vby, vbw, vbh])
# NOT: koordinatlar duzelt_bd.py sonrasi YATAY icerik uzayindadir.
KIRPIMLAR = [
    # concat(80-210) + ps_ultra(280-810) + axi_smc(880-1080) + reset(400-690)
    ("ultrascale-bd-full.svg", "ultrascale-bd-ps.svg", 1775, 690,
     [40, 20, 1070, 520]),
    # CIPS(244-764) + NoC(1194-1450) + aradaki NoC arayuz demeti + CH0_DDR4_0
    ("versal-bd-full.svg", "versal-bd-cips.svg", 2143, 650,
     [190, 0, 1330, 480]),
]


def kirp(kaynak, hedef, nw, nh, vb):
    src = (BD / kaynak)
    if not src.exists():
        print(f"atlandı (yok): {kaynak}")
        return
    data = base64.b64encode(src.read_bytes()).decode()
    uri = "data:image/svg+xml;base64," + data
    x, y, w, h = vb
    out = (
        f'<svg viewBox="{x} {y} {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink">'
        f'<image x="0" y="0" width="{nw}" height="{nh}" '
        f'xlink:href="{uri}"/></svg>'
    )
    (BD / hedef).write_text(out, encoding="utf-8")
    print(f"üretildi: {hedef} (viewBox {x} {y} {w} {h})")


if __name__ == "__main__":
    for k in KIRPIMLAR:
        kirp(*k)
