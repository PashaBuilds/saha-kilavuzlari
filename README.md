# Saha Kılavuzları

Gömülü yazılımcı için **tek dosyalık, bağımlılıksız, çevrimdışı** Türkçe teknik
belge serisi — ve hepsini tek çatı altında toplayan sıvı cam tasarımlı raf sayfası.

Her belge derlendiğinde CDN'siz, fontsuz, internetsiz çalışan tek bir HTML
dosyasına iner. USB'ye kopyala, air-gapped laba gir, oku.

Rafta iki tür belge var:

- **Rehberli yolculuk** — sahaya sıfırdan girene elden tutan müfredat (okuma +
  uygulamalı lab). Raf sayfasında en üstteki *"Buradan başla"* bandında durur.
- **Saha kılavuzu** — zaten sahada olana derinlemesine referans eseri. Alttaki
  kart ızgarasında.

## Hızlı başlangıç

Tarayıcıdan oku: **https://pashabuilds.github.io/saha-kilavuzlari/**

veya indir, çevrimdışı oku:

```bash
git clone https://github.com/PashaBuilds/saha-kilavuzlari.git
```

Sonra `index.html`'e çift tıkla. Hepsi bu — sunucu, kurulum, internet gerekmez.

| Belge | Tür | Konu |
|---|---|---|
| **Introduction to Embedded Systems** (İngilizce) | Yolculuk | Yeni mezuna oryantasyon: Zynq/ZCU111, boot & bellek, register, interrupt, I2C/SPI/UART, FreeRTOS, Vitis debug — 10 uygulamalı lab + capstone projesi |
| **Doğrudan RF Örnekleme ve Ön Uç Tasarımı** | Kılavuz | ADC/DAC, SERDES, JESD204B/C, clocking & SYSREF, TI·ADI zincirleri, Versal GT, bring-up ve debug |
| **Ethernet ve Ağ İletişimi** | Kılavuz | PHY/MAC'ten ARP, IP, TCP/UDP, DNS ve TLS'e; Wireshark, gömülü Ethernet, arıza teşhisi |
| **Lokal LLM Dünyası** | Kılavuz | Quantization, MoE & mimariler, VRAM hesabı, Ollama/LM Studio, lokal API — modeli kendi makinende koşturmak |

## Repo yapısı

```
saha-kilavuzlari/
├── index.html          ← raf (hub) sayfası; buradan başla
├── kilavuzlar.js       ← kayıtlar (başlık, açıklama, renk, tür, kaynak, yol...)
├── guncelle.py         ← senkronizasyon scripti (stdlib, ağsız)
├── kilavuzlar/         ← DERLENMİŞ belgeler (okuma katmanı)
│   ├── oryantasyon/index.html
│   ├── rf-sampling/index.html
│   ├── ethernet/index.html
│   └── lokal-llm/index.html
└── kaynak/             ← belgelerin TAM KAYNAKLARI (düzenleme katmanı)
    ├── gomulu-oryantasyon/          md bölümler + 10 lab (C) + şemalar + derleyici
    ├── rf-sampling-saha-kilavuzu/   md + şemalar + Node derleyici
    ├── ethernet-saha-kilavuzu/      md + SVG şemalar + Python derleyici
    └── lokal-llm-saha-kilavuzu/     md + SVG şemalar + Python derleyici
```

> Not: `kilavuzlar/` klasörü tüm derlenmiş belgeleri tutar (tür ayrımı yok);
> "yolculuk / kılavuz" ayrımı `kilavuzlar.js`teki `tur` alanında ve raf
> sayfasının sunumunda yaşar.

## Bir belgeyi düzenlemek

Kaynaklar repoda eksiksiz durur; klonlayan herkes düzenleyip yeniden derleyebilir.

```bash
# 1) Kaynağı düzenle — ör.:
#    Oryantasyon: kaynak/gomulu-oryantasyon/content/*.md  (+ labs/ C çözümleri)
#    RF Sampling: kaynak/rf-sampling-saha-kilavuzu/src/*.md

# 2) Belgeyi derle (kaynak klasörünün tipine göre)
cd kaynak/gomulu-oryantasyon && python3 build/build.py           # Python derleyici
cd kaynak/rf-sampling-saha-kilavuzu && npm install && npm run build   # Node derleyici

# 3) Taze derlemeyi rafa taşı (repo köküne dön)
python3 guncelle.py

# 4) index.html'i açıp gör
```

Her kaynak klasöründeki `KICKOFF.md`, o belgenin yazım kurallarını, tasarım
sistemini ve kalite çıtasını tanımlar — düzenlemeden önce göz at.

## Yeni belge eklemek

1. `kaynak/` altına (veya yazar makinesinde üst dizine) belgenin reposunu ekle;
   derleyicisi `dist/index.html` üretsin.
2. `kilavuzlar.js`e bir kayıt ekle: en azından `slug`, `kaynak` (repo klasör
   adı) ve `yol` alanları. Rehberli yolculuk ise `tur: "yolculuk"` ver.
3. `python3 guncelle.py` → dosyaları rafa taşır, kaynağı yansıtır, boyut/tarih
   alanlarını tazeler. (`*-saha-kilavuzu` adlı yeni bir repoyu kayıtsız
   bulursa hazır bir kayıt taslağı da basar.)
4. Açıklama/etiketleri yaz, boş bir renk tonu (hue) seç. Raf sayfası kartı
   kendiliğinden çizer — `index.html`'e dokunulmaz.

## Yazar iş akışı (bu reponun beslenişi)

Belgeler asıl olarak üst dizindeki **kardeş repolarda** yazılır
(`../gomulu-oryantasyon`, `../ethernet-saha-kilavuzu` gibi). `python3 guncelle.py`
her kaydın `kaynak` reposunu bulur, derlenmiş `dist/index.html`'i `kilavuzlar/`e
kopyalar ve kaynak ağacını (`.git`, `node_modules`, `dist`, `_`-önekli
scratch dosyaları hariç) `kaynak/`a yansıtır. Kardeş repo yoksa (ör. taze klon)
`kaynak/` içindeki yansı kaynak kabul edilir — yukarıdaki düzenleme akışı budur.

## Tasarım notları

Raf sayfası da serinin kurallarına uyar: harici istek sıfır (font/CDN/fetch yok),
`file://` üzerinden çalışır, `prefers-reduced-motion`a saygılıdır. Giriş
koreografisini atlayan anlık görünüm için: `index.html?anlik`.
