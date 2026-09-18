# CLAUDE.md — almac-saha-kilavuzu

Bu klasör, *Antenden PDW'ye — Radar ve Elektronik Harp Sayısal Almaç Sistemleri
Saha Kılavuzu* belgesinin tam kaynağıdır (Saha Kılavuzu serisi, SK-05).

**Tek içerik/pedagoji talimatı: [KICKOFF.md](KICKOFF.md).** Repo yapısı,
build ve seri konvansiyonu için KICKOFF §1 (referans repo yolu), §9 (bağımsız
repo) ve §13 (başlatma promptu) yerine **bu repodaki seri düzeni** geçerlidir;
kararlar ve gerekçeleri [PLAN.md](PLAN.md)'de.

## Kısa harita

- İçerik: `content/NN-ad.md` — bölüm başına bir dosya, `# Bölüm N — Ad` + `::meta`
- Şemalar: `assets/svg/g-XX-*.svg` (el yazımı, yalnızca CSS değişkenli renk,
  ortak semboller `assets/svg/symbols.svg`'den `<use href="#sym-…">`)
- Tema/bileşenler: `assets/css/kilavuz.css`
- JS: `assets/js/dsp-core.js` (hesap), `widget-kit.js` (kap/çizim),
  `widgets/wNN-*.js` (her widget), `site.js` (TOC, tema, sekmeler)
- Veri: `data/scenario.json` (referans senaryo — tek doğruluk kaynağı),
  `data/glossary.json` (sözlük + baloncuk)
- Derleyici: `build/build.py` (stdlib) → `dist/index.html`
- Denetim: `build/check.py` (kalite kapıları + testler)
- Testler: `tests/dsp-core.test.js` (`node --test`), `tests/test_bilinen_cevap.py`

## Komutlar

```
python build/build.py        # derle
python build/check.py        # kalite kapıları + testler (node varsa JS testleri)
python build/gen_figures.py  # hesaplanmış SVG path'lerini yeniden üret
```

Windows'ta `python3` yoksa `python` / `py`. Tüm G/Ç utf-8.

## Değişmez kurallar

1. `dist/index.html` tamamen self-contained: CDN, font, fetch, ES module yok.
2. Renkler yalnızca CSS değişkeni; SVG/widget içinde sabit hex yok.
3. Referans senaryo sayıları metne elle yazılmaz: `{{s:yol}}` makrosu.
4. Kurgusal senaryo, açık literatür; gerçek sistem/tehdit parametresi yok.
5. Widget hesapları `dsp-core.js`'te; widget dosyası yalnızca çizer.
