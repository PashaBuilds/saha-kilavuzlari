# Saha Kılavuzları

Gömülü yazılımcı için **tek dosyalık, bağımlılıksız, çevrimdışı** Türkçe teknik
kılavuz serisi — ve hepsini tek çatı altında toplayan sıvı cam tasarımlı raf sayfası.

Her kılavuz, konusunda tek başına literatür oluşturacak kapsamda yazılır;
derlendiğinde CDN'siz, fontsuz, internetsiz çalışan tek bir HTML dosyasına iner.
USB'ye kopyala, air-gapped laba gir, oku.

## Hızlı başlangıç

```bash
git clone https://github.com/PashaBuilds/saha-kilavuzlari.git
```

Sonra `index.html`'e çift tıkla. Hepsi bu — sunucu, kurulum, internet gerekmez.
Raf sayfası açılır; kartlardan kılavuzlara geçilir.

| Kılavuz | Konu |
|---|---|
| **Doğrudan RF Örnekleme ve Ön Uç Tasarımı** | ADC/DAC, SERDES, JESD204B/C, clocking & SYSREF, TI·ADI zincirleri, Versal GT, bring-up ve debug |
| **Ethernet ve Ağ İletişimi** | PHY/MAC'ten ARP, IP, TCP/UDP, DNS ve TLS'e; Wireshark, gömülü Ethernet, arıza teşhisi |

## Repo yapısı

```
saha-kilavuzlari/
├── index.html          ← raf (hub) sayfası; buradan başla
├── kilavuzlar.js       ← kart kayıtları (başlık, açıklama, renk, yol...)
├── guncelle.py         ← senkronizasyon scripti (stdlib, ağsız)
├── kilavuzlar/         ← DERLENMİŞ kılavuzlar (okuma katmanı)
│   ├── ethernet/index.html
│   └── rf-sampling/index.html
└── kaynak/             ← kılavuzların TAM KAYNAKLARI (düzenleme katmanı)
    ├── ethernet-saha-kilavuzu/      md içerik + SVG şemalar + Python derleyici
    └── rf-sampling-saha-kilavuzu/   md içerik + şemalar + Node derleyici
```

## Bir kılavuzu düzenlemek

Kaynaklar repoda eksiksiz durur; klonlayan herkes düzenleyip yeniden derleyebilir.

```bash
# 1) Kaynağı düzenle
#    Ethernet:    kaynak/ethernet-saha-kilavuzu/content/*.md
#    RF Sampling: kaynak/rf-sampling-saha-kilavuzu/src/*.md

# 2) Kılavuzu derle
cd kaynak/ethernet-saha-kilavuzu && python3 build/build.py        # Ethernet
cd kaynak/rf-sampling-saha-kilavuzu && npm install && npm run build   # RF (ilk seferde npm install)

# 3) Taze derlemeyi rafa taşı (repo köküne dön)
python3 guncelle.py

# 4) index.html'i açıp gör
```

Her kaynak klasöründeki `KICKOFF.md`, o kılavuzun yazım kurallarını, tasarım
sistemini ve kalite çıtasını tanımlar — düzenlemeden önce göz at.

## Yeni kılavuz eklemek

1. `kaynak/` altına (veya yazar makinesinde üst dizine) `<konu>-saha-kilavuzu`
   klasörü ekle; derleyicisi `dist/index.html` üretsin.
2. `python3 guncelle.py` → dosyaları rafa taşır, `kilavuzlar.js` için hazır
   kayıt taslağı basar.
3. Taslağı `kilavuzlar.js`e ekle: açıklama ve etiketleri yaz, karta boş bir
   renk tonu (hue açısı) seç. Raf sayfası kartı kendiliğinden çizer —
   `index.html`'e dokunulmaz.

## Yazar iş akışı (bu reponun beslenişi)

Kılavuzlar asıl olarak üst dizindeki **kardeş repolarda** yazılır
(`../ethernet-saha-kilavuzu` gibi). `python3 guncelle.py` kardeşleri bulur,
derlenmiş `dist/index.html`'i `kilavuzlar/`e kopyalar ve kaynak ağacını
(`.git`, `node_modules`, `dist` hariç) `kaynak/`a yansıtır. Kardeş repo yoksa
(ör. taze klon) `kaynak/` içindeki yansılar kaynak kabul edilir — yukarıdaki
düzenleme akışı tam da budur.

## Tasarım notları

Raf sayfası da serinin kurallarına uyar: harici istek sıfır (font/CDN/fetch yok),
`file://` üzerinden çalışır, `prefers-reduced-motion`a saygılıdır. Giriş
koreografisini atlayan anlık görünüm için: `index.html?anlik`.
