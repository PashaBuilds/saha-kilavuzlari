# -*- coding: utf-8 -*-
"""kucult.py — screenshot'ları makul çözünürlüğe indirir (KICKOFF kuralı).

Kullanım: python build/kucult.py assets/screenshots/shot-01.png [...]
Argümansız: assets/screenshots/*.png içinden genişliği MAX'ı aşanları işler.

- Genişlik > MAX (2560) ise orantılı küçültür (LANCZOS).
- 256 renkli adaptif palete indirger (Vivado arayüzü düz renkli — kayıpsıza
  yakın, dosya ~%60 küçülür). Sonuç aynı dosyanın üzerine yazılır.
"""
import sys
from pathlib import Path
from PIL import Image

MAX = 2560
ROOT = Path(__file__).resolve().parent.parent


def isle(yol: Path) -> None:
    img = Image.open(yol)
    w, h = img.size
    degisti = False
    if w > MAX:
        img = img.convert("RGB").resize((MAX, round(h * MAX / w)), Image.LANCZOS)
        degisti = True
    if img.mode != "P":
        img = img.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)
        degisti = True
    if degisti:
        img.save(yol, optimize=True)
        print(f"kucultuldu: {yol.name} -> {img.size[0]}x{img.size[1]}, "
              f"{yol.stat().st_size // 1024} KB")
    else:
        print(f"degisiklik yok: {yol.name}")


if __name__ == "__main__":
    hedefler = [Path(a) for a in sys.argv[1:]] or sorted(
        (ROOT / "assets" / "screenshots").glob("*.png"))
    for y in hedefler:
        isle(y)
