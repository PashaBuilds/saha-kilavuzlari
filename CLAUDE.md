# CLAUDE.md — saha-kilavuzlari (hub / raf)

Bu repo, "Saha Kılavuzu" serisinin **karşılama sayfası (hub)**. Kılavuzların
kendisi burada YAZILMAZ — her kılavuz üst dizindeki kendi reposunda, ayrı
Claude oturumlarında yönetilir. Buraya yalnızca derlenmiş son sürümleri düşer.

## "yapıyı güncelle" prosedürü

Kullanıcı "yapıyı güncelle" (veya benzeri) dediğinde:

1. `python3 guncelle.py` çalıştır. Script:
   - Üst dizindeki `*-saha-kilavuzu` repolarını tarar,
   - her `dist/index.html`i `kilavuzlar/<slug>/index.html`e kopyalar,
   - `kilavuzlar.js`teki `boyut` ve `guncelleme` alanlarını tazeler.
2. Script **yeni** (kayıtsız) bir kılavuz bulursa taslak kayıt basar:
   taslağı `kilavuzlar.js`e ekle; `aciklama`yı ve `etiketler`i o kılavuzun
   dist başlığına/içeriğine bakarak özenle yaz. `bolumSayi`, `sema`, `kelime`
   için kaynak repodaki md/şema sayılarına bak (aşağıdaki not).
3. Bölüm/şema sayıları değiştiyse (`kilavuzlar.js`te elle duran alanlar):
   kaynak repoda `content/*.md` ya da `src/*.md` sayısı ve dist'teki
   `<figure` adedi ile karşılaştırıp güncelle.
4. Tarayıcıda `index.html`i açıp kartları ve istatistikleri gözle doğrula.

## Dosya yapısı

```
saha-kilavuzlari/
├── index.html        ← hub sayfası; TASARIM burada. Güncellemede dokunulmaz.
├── kilavuzlar.js     ← kayıt listesi; kartlar + hero istatistikleri buradan üretilir.
├── guncelle.py       ← senkronizasyon scripti (stdlib, ağsız).
├── kilavuzlar/       ← derlenmiş kılavuzlar (okuma rafı)
│   ├── ethernet/index.html
│   └── rf-sampling/index.html
└── kaynak/           ← kılavuz kaynaklarının TAM yansıları (klonlayan düzenleyebilsin)
    ├── ethernet-saha-kilavuzu/     (.git, node_modules, dist hariç ayna)
    └── rf-sampling-saha-kilavuzu/
```

`guncelle.py` kaynağı önce üst dizindeki kardeş repolarda arar (yazar makinesi;
bulursa kaynak/'ı da tazeler), yoksa kaynak/ yansılarını kullanır (taze klon).
Yansı tazelemesi rmtree+copytree'dir: kaynak/ altında elle değişiklik yapma,
kardeş repo varken ezilir — asıl düzenleme her zaman kardeş repoda yapılır.

## Git / GitHub

- Uzak repo: `https://github.com/PashaBuilds/saha-kilavuzlari` (hesap her
  zaman **PashaBuilds**). Yayın akışı: `guncelle.py` → gözle doğrula →
  commit → push. Push'tan önce kullanıcı onayı gerekmiyorsa da commit
  mesajında ne güncellendiğini (hangi kılavuz, hangi sürüm) belirt.
- Kılavuzların kaynak REPOLARI (üst dizindekiler) bu repoya dahil değildir;
  yalnızca temiz yansıları `kaynak/` altında taşınır. rf reposunun kendi
  .gitignore'u `notes/`u dışlar — bu bilinçli, yansıda da dışlanmış kalır.

## Değişmez kısıtlar (seri ruhu)

- **Tamamen self-contained:** CDN, harici font, fetch, ES module YOK.
  `file://` üzerinden çift tıkla açılabilmeli; USB ile air-gapped ortama
  taşınabilmeli. `kilavuzlar.js` klasik `<script src>` ile yüklenir (bilinçli).
- Dil Türkçe; teknik terimler İngilizce kalır.
- Kart linkleri `kilavuzlar/<slug>/index.html`e **açık dosya adıyla** gider
  (file:// dizin → index.html çözümlemesi yapmaz).

## Tasarım sistemi (index.html)

- Konsept: "sıvı cam" — koyu petrol zemin, aurora + dönen tayf + gratikül +
  gren; imleci izleyen kostik ışık; kartlarda cam kırılması, parıltı
  süpürmesi, işaretçi eğimi.
- Kart vurgu rengi `renk` alanındaki **hue açısından** türetilir
  (kullanılan: 285 RF moru, 160 Ethernet turkuazı; boşta: 25, 210, 340).
  Yeni kılavuz = yeni hue; CSS'e dokunmak gerekmez.
- Kart deseni `motif` alanı: `analog` | `digital` | `sinir` | `varsayilan`.
  Yeni motif gerekiyorsa index.html'deki `MOTIF` sözlüğüne SVG path ekle.
- `prefers-reduced-motion` ve klavye odağı destekleri korunmalı.
- `index.html?anlik` → giriş koreografisini atlar, son hali anında basar
  (yazdırma ve headless ekran görüntüsü/otomasyon için; doğrulamada bunu kullan).
- Not: gizli sekmede CSS geçiş saati donduğundan koreografi sayfa ilk kez
  görünür olduğunda başlar (visibilitychange koruması JS'te mevcut).

## Yeni kılavuz ekleme (özet)

1. Üst dizine `<konu>-saha-kilavuzu` reposu gelir, içinde `dist/index.html`.
2. `python3 guncelle.py` → kopyalar + taslak kayıt basar.
3. Taslağı `kilavuzlar.js`e ekle, metinlerini yaz, hue + motif seç.
4. Tarayıcıda doğrula. Hepsi bu — index.html'e dokunma.
