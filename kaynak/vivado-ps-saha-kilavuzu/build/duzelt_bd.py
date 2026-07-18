# -*- coding: utf-8 -*-
"""
duzelt_bd.py — Vivado write_bd_layout SVG'lerindeki yan yatmayı düzeltir.

Vivado, -orientation landscape ile üretilen SVG'de içeriği
`transform="rotate(-90) translate(-W)"` ile döndürür ve viewBox'ı dikey
(H x W) bırakır — tarayıcıda diyagram 90° yan görünür. Bu script:
  1. rotate/translate transform'unu kaldırır,
  2. viewBox'ı içerik uzayına (W x H) çevirir.

İçerik koordinatları zaten yatay uzayda çizildiği için başka değişiklik
gerekmez. write_bd_layout her yeniden koşulduğunda bu script de koşulmalıdır
(build hattının parçası).

Kullanım: python build/duzelt_bd.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "assets" / "bd-exports"


def duzelt(ad: str) -> None:
    yol = BD / ad
    if not yol.exists():
        print(f"atlandı (yok): {ad}")
        return
    t = yol.read_text(encoding="utf-8")

    m = re.search(r'transform="rotate\(-90\) translate\(-(\d+)\)"', t)
    if not m:
        print(f"değişiklik yok (rotate bulunamadı): {ad}")
        return
    genislik = int(m.group(1))  # içerik uzayının genişliği (örn. 1775)

    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', t)
    if not vb:
        print(f"HATA: viewBox okunamadı: {ad}")
        return
    h_eski, w_eski = int(vb.group(1)), int(vb.group(2))
    # dikey viewBox (H x W) -> yatay (W x H)
    if w_eski != genislik:
        print(f"UYARI: {ad} boyut uyuşmazlığı (translate {genislik}, viewBox {h_eski}x{w_eski})")

    t = t.replace(vb.group(0), f'viewBox="0 0 {w_eski} {h_eski}"', 1)
    t = t.replace(f'\n   transform="rotate(-90) translate(-{genislik})"', "")
    t = t.replace(f' transform="rotate(-90) translate(-{genislik})"', "")
    yol.write_text(t, encoding="utf-8")
    print(f"düzeltildi: {ad} -> viewBox 0 0 {w_eski} {h_eski} (yatay)")


if __name__ == "__main__":
    duzelt("ultrascale-bd-full.svg")
    duzelt("versal-bd-full.svg")
    duzelt("microblaze-bd-full.svg")
