# CLAUDE.md — ethernet-saha-kilavuzu

Bu projenin tek yetkili talimat kaynağı **KICKOFF.md**'dir.
Herhangi bir üretim/düzenleme işine başlamadan önce KICKOFF.md'yi oku ve
oradaki kurallara uy: proje kimliği, tasarım sistemi, şema envanteri,
bölüm iskeleti, yazım kuralları, build kuralları ve kalite çıtası orada.

Kısa harita:

- İçerik kaynağı: `content/*.md` (bölüm başına bir dosya, sıralı prefix)
- Şemalar: `assets/svg/*.svg` (el yapımı inline SVG, CSS değişkenli renkler)
- Tema: `assets/css/kilavuz.css` (koyu varsayılan + açık, çift tema)
- Derleyici: `build/build.py` (Python 3 stdlib, md → tek HTML)
- Çıktı: `dist/index.html` (tamamen self-contained, offline)

Build almak için:

```
python3 build/build.py
```

İçerik markdown'ında proje-özel sözdizimi:

- `:::saha-notu Başlık` … `:::` → pratik bilgi kutusu (altın)
- `:::tuzak Başlık` … `:::` → yaygın hata kutusu (kırmızı)
- `:::analoji Başlık` … `:::` → benzetme kutusu (yeşil)
- `:::derin-dalis Başlık` … `:::` → katlanabilir derinlik (`<details>`)
- `:::ozet` … `:::` → bölüm özeti kutusu
- `{{svg:dosya-adi.svg|Şekil açıklaması}}` → inline SVG + figcaption
- Çitli kod blokları otomatik "kopyala" butonlu `komut` kutusu olur
