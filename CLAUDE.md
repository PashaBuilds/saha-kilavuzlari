# CLAUDE.md — saha-kilavuzlari (hub / raf)

Bu repo, "Saha Kılavuzu" serisinin **karşılama sayfası (hub)**. Belgelerin
kendisi burada YAZILMAZ — her belge üst dizindeki kendi reposunda, ayrı Claude
oturumlarında yönetilir. Buraya yalnızca derlenmiş son sürümleri düşer.

## İki tür belge

`kilavuzlar.js`teki her kaydın bir `tur` alanı vardır:

- `tur: "kilavuz"` (varsayılan) → derinlemesine referans eseri. Alttaki kart
  ızgarasında (SK-01, SK-02, ...). Hero istatistiklerini bunlar toplar.
- `tur: "yolculuk"` → sıfırdan başlayana rehberli müfredat (okuma + uygulamalı
  lab). En üstteki **"Buradan başla"** bandında, kendi sıcak şafak (altın→yeşil)
  tasarımıyla render edilir. Hero sayımına GİRMEZ; kendi sayıları (bölüm, lab,
  mezuniyet görevi) bandın içinde durur.

Tür ayrımı yalnızca kayıtta + sunumda yaşar; dosyalar hepsi `kilavuzlar/` altında.

## "yapıyı güncelle" prosedürü

Kullanıcı "yapıyı güncelle" (veya benzeri) dediğinde:

1. `python3 guncelle.py` çalıştır. Script **kayıt-güdümlüdür**:
   - `kilavuzlar.js`teki her kaydın `kaynak` reposunu bulur (önce üst dizindeki
     kardeş `../<kaynak>`, yoksa `kaynak/<kaynak>` yansısı),
   - `dist/index.html`i kaydın `yol` alanındaki hedefe kopyalar,
   - kardeş repoysa kaynağı `kaynak/`a yansıtır (`.git`, `node_modules`, `dist`,
     `_`-önekli scratch hariç),
   - `boyut` ve `guncelleme` alanlarını tazeler.
2. Script **yeni** (`*-saha-kilavuzu` adlı, kayıtsız) bir repo bulursa taslak
   kayıt basar. Son eki taşımayan repolar (ör. `gomulu-oryantasyon`) otomatik
   keşfedilmez — kaydını elle ekle (`kaynak` alanını açıkça yaz).
3. `bolumSayi`, `sema`, `kelime`, `lab` gibi elle duran alanlar değiştiyse
   kaynak repodaki md/şema sayısıyla karşılaştırıp güncelle.
4. `index.html?anlik`i headless veya tarayıcıda açıp bandı, kartları ve
   istatistikleri gözle doğrula.
5. Sonra commit + push (aşağıdaki Git bölümü).

## Dosya yapısı

```
saha-kilavuzlari/
├── index.html        ← hub sayfası; TASARIM burada. Güncellemede dokunulmaz.
├── kilavuzlar.js     ← kayıt listesi; band + kartlar + hero buradan üretilir.
├── guncelle.py       ← senkronizasyon scripti (stdlib, ağsız).
├── kilavuzlar/       ← derlenmiş belgeler (okuma rafı; tür ayrımı yok)
│   ├── oryantasyon/index.html
│   ├── rf-sampling/index.html
│   ├── ethernet/index.html
│   └── lokal-llm/index.html
└── kaynak/           ← belge kaynaklarının TAM yansıları (klonlayan düzenleyebilsin)
    ├── gomulu-oryantasyon/         (.git, node_modules, dist, _scratch hariç ayna)
    ├── rf-sampling-saha-kilavuzu/
    ├── ethernet-saha-kilavuzu/
    └── lokal-llm-saha-kilavuzu/
```

`guncelle.py` her kaydın kaynağını önce üst dizindeki kardeş repoda arar (yazar
makinesi; bulursa kaynak/'ı da tazeler), yoksa kaynak/ yansısını kullanır (taze
klon). Yansı tazelemesi rmtree+copytree'dir: kaynak/ altında elle değişiklik
yapma, kardeş repo varken ezilir — asıl düzenleme her zaman kardeş repoda yapılır.

## Git / GitHub

- Uzak repo: `https://github.com/PashaBuilds/saha-kilavuzlari` (hesap her
  zaman **PashaBuilds**). Yayın akışı: `guncelle.py` → gözle doğrula →
  commit → push. Push'tan önce kullanıcı onayı gerekmiyorsa da commit
  mesajında ne güncellendiğini (hangi kılavuz, hangi sürüm) belirt.
- Belgelerin kaynak REPOLARI (üst dizindekiler) bu repoya dahil değildir;
  yalnızca temiz yansıları `kaynak/` altında taşınır. `_`-önekli dosyalar
  (araştırma, stil, görev-zinciri scratch'leri) ve rf'in `notes/`u yansıya
  girmez — bilinçli.

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
  (kullanılan: 285 RF moru, 160 Ethernet turkuazı, 25 Lokal-LLM amberi,
  40 Oryantasyon altını; boşta: 210, 340). Yeni belge = yeni hue.
- Kart deseni `motif` alanı: `analog` | `digital` | `sinir` | `varsayilan`.
  Yeni motif gerekiyorsa index.html'deki `MOTIF` sözlüğüne SVG path ekle.
- "Buradan başla" bandı (`tur:"yolculuk"`) kendi CSS'iyle (`.yol-kart`) çift-tonlu
  şafak gradyanı kullanır; `renk` yerine sabit `--y1`/`--y2` (altın/yeşil) ile
  boyanır. Rota rayı kaydın `rota` dizisinden çizilir.
- `prefers-reduced-motion` ve klavye odağı destekleri korunmalı.
- `index.html?anlik` → giriş koreografisini atlar, son hali anında basar
  (yazdırma ve headless ekran görüntüsü/otomasyon için; doğrulamada bunu kullan).
- Not: gizli sekmede CSS geçiş saati donduğundan koreografi sayfa ilk kez
  görünür olduğunda başlar (visibilitychange koruması JS'te mevcut).

## Yeni belge ekleme (özet)

1. Üst dizine belgenin reposu gelir, içinde `dist/index.html`.
2. `kilavuzlar.js`e kayıt ekle (`slug`, `kaynak`, `yol`; yolculuksa `tur:"yolculuk"`
   + `lab`/`rota`/`final`/`altBaslik`). `*-saha-kilavuzu` reposu için
   `python3 guncelle.py` taslak da basar.
3. `python3 guncelle.py` → kopyalar, yansıtır, boyut/tarih tazeler.
4. Açıklama/etiket yaz, hue seç (kılavuzsa motif de). `index.html`e dokunma.
5. `index.html?anlik` ile doğrula, sonra commit + push.
