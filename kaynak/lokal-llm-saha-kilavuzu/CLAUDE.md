# CLAUDE.md — lokal-llm-saha-kilavuzu

**Önce [KICKOFF.md](KICKOFF.md) oku ve oradaki kurallara uy.** Proje kimliği,
tasarım sistemi, içindekiler iskeleti, yazım kuralları ve kalite çıtası orada.

## Hızlı özet

- Çıktı: `dist/index.html` — tek, self-contained, offline çalışan HTML.
- Kaynak: `content/NN-slug.md` (bölüm başına bir dosya), `assets/svg/*.svg`,
  `assets/css/kilavuz.css`.
- Derleme: `python3 build/build.py` (stdlib-only).

## Kaynak markdown sözleşmesi (build.py'nin anladığı)

- Her dosya `# Bölüm N — Başlık` ile başlar (çıktıda `<h2>` olur; `##` → `<h3>`,
  otomatik N.M numarası alır).
- Kutu direktifi:
  ```
  :::saha-notu Başlık
  ...markdown...
  :::
  ```
  Tipler: `saha-notu`, `tuzak`, `analoji`, `hesap`, `derin-dalis`
  (derin-dalis katlanabilir `<details>` üretir).
- SVG şema: `{{svg:dosya-adi.svg|Figür alt yazısı}}` — `assets/svg/` içinden
  inline gömülür. SVG'lerde hard-coded renk YASAK, CSS değişkeni kullan
  (`var(--ink)`, `var(--muted)`, `var(--accent)`, `var(--gold)`, `var(--teal)`,
  `var(--red)`, `var(--card)`, `var(--line)`).
- Kod bloklarına otomatik kopyala butonu eklenir.
- Tablolar dar ekranda yatay scroll kabına sarılır.
- Blok seviyesinde `<` ile başlayan satırlar ham HTML olarak geçer
  (hesaplayıcı widget'ları böyle gömülür).
