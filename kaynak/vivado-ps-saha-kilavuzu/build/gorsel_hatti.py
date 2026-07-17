# -*- coding: utf-8 -*-
"""
gorsel_hatti.py — görsel son-işlem hattını tek komutta koşar:
  1. duzelt_bd  : BD SVG'lerindeki 90° yan yatmayı düzeltir
  2. crop_bd    : PS-yakın / CIPS-yakın kırpımları üretir
  3. kucult     : screenshot'ları makul çözünürlüğe indirir
  4. annotate   : açıklama katmanı SVG'lerini üretir
Sonra build.py çağrılmaya hazırdır.

Kullanım: python build/gorsel_hatti.py
"""
import runpy
from pathlib import Path

BUILD = Path(__file__).resolve().parent

for adim in ("duzelt_bd", "crop_bd", "kucult", "annotate"):
    print(f"\n=== {adim} ===")
    runpy.run_path(str(BUILD / f"{adim}.py"), run_name="__main__")
print("\nGÖRSEL HATTI TAMAM. Şimdi: python build/build.py")
