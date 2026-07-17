# KICKOFF — vivado-ps-saha-kilavuzu

> Bu dosya, projenin tek başlangıç talimatıdır. Claude Code bu dosyayı okuyarak
> üretime başlar. Repo kökünde durur; CLAUDE.md bu dosyaya referans verir.

---

## 1. Proje Kimliği

- **Klasör / repo adı:** `vivado-ps-saha-kilavuzu`
- **Doküman adı:** *Vivado'yu Yazılımcı Gibi Okumak — PS Perspektifinden
  Sayısal Tasarım Analizi Saha Kılavuzu*
- **Seri:** "Saha Kılavuzu" serisinin beşinci üyesi (Bellek Mimarisi,
  RF Örnekleme, Ethernet, Lokal LLM). Aynı görsel aile, aynı kalite çıtası.
  Serinin en **workflow odaklı** üyesi: kavram anlatımından çok
  "aç → tıkla → şuraya bak → bu ayar yazılımına şöyle yansır" akışı.
- **Hedef kitle:** Gömülü yazılımı bilen (register, driver, Vitis, BSP
  kavramlarına aşina) ama **Vivado'ya hiç girmemiş ya da korkarak giren**
  yazılımcı. Donanım tasarlamayacak; donanımcının teslim ettiği projeyi açıp
  analiz edecek. Ekipteki mevcut mühendisler — yeni mezun oryantasyonu DEĞİL.
- **Misyon:** Okuyan kişi bittiğinde:
  1. Donanımcıdan gelen bir Vivado projesini (MPSoC/RFSoC veya Versal) açıp
     blok dizaynda yolunu bulabilmeli: hangi IP ne, sinyaller nereden nereye,
     hiyerarşi nasıl gezilir.
  2. PS konfigürasyon ekranını (UltraScale+ PS IP) ve Versal CIPS'i açıp
     yazılımı ilgilendiren her ayarı okuyabilmeli: clock'lar, DDR, MIO/EMIO,
     aktif çevre birimleri, PS-PL arayüzleri, interrupt bağlantıları.
  3. Address Editor'dan adres haritasını çıkarıp xparameters.h ile
     eşleştirebilmeli; "bu IP'nin base adresi neden bu" sorusunu
     cevaplayabilmeli.
  4. .xsa export'un ne taşıdığını ve Vitis platformuna nasıl dönüştüğünü
     anlatabilmeli.
  5. Bring-up öncesi "PS ayar kontrol listesi"ni tek başına yürütebilmeli
     ("UART hangi MIO'da, clock kaç MHz, DDR açık mı, interrupt hangi PL
     pininden geliyor").
- **Dil:** Türkçe gövde; teknik terimler İngilizce korunur, ilk geçtiği yerde
  parantezle açıklanır. Ton: seriyle aynı — usta-çırak, hype'sız, emoji'siz.
- **Araç sürümü:** Vivado **2023.2** baz alınır; doküman başına sürüm notu
  düşülür ("ekranlar sürümler arası değişebilir, kavramlar kalıcıdır").

---

## 2. Repo Yapısı

```
vivado-ps-saha-kilavuzu/
├── KICKOFF.md
├── CLAUDE.md                    ← "KICKOFF.md'yi oku, kurallara uy"
├── content/                     ← bölüm başına markdown
├── vivado/                      ← DEMO PROJE ÜRETİM HATTI
│   ├── rfsoc/
│   │   └── create_bd.tcl        ← ZCU111 demo blok dizaynını sıfırdan kuran script
│   ├── versal/
│   │   └── create_bd.tcl        ← Versal demo (CIPS+NoC) kuran script
│   ├── export_visuals.tcl       ← BD layout SVG/PDF + raporları üreten script
│   ├── gui_capture/             ← otomatik ekran yakalama araç seti
│   │   ├── stage_*.tcl          ← GUI'yi karelere hazırlayan Tcl durum scriptleri
│   │   ├── shots.yaml           ← kare manifesti: Tcl durumu + GUI eylemi + doğrulama kriteri + kutu koordinatları
│   │   └── capture_log.md       ← her karenin tekrar üretim reçetesi
│   └── README.md                ← scriptlerin nasıl koşulacağı
├── assets/
│   ├── bd-exports/              ← write_bd_layout çıktıları (SVG/PDF)
│   ├── reports/                 ← Tcl'den sökülen konfig/adres raporları
│   ├── screenshots/             ← KULLANICININ çektiği GUI ekranları (shot-list'e göre)
│   ├── svg/                     ← el yapımı şemalar + screenshot açıklama katmanları
│   └── css/kilavuz.css
├── SHOT-LIST.md                 ← kullanıcı için numaralı ekran çekim listesi
├── build/build.py
└── dist/index.html
```

**Kural:** `dist/index.html` tamamen self-contained (CSS/SVG/görseller inline —
screenshot'lar base64 gömülür, bu yüzden PNG'ler makul çözünürlükte tutulur).
İnternet bağımlılığı yok.

---

## 3. Görsel Boru Hattı (bu kılavuzun ayırt edici altyapısı)

Üç katman, üçü de ZORUNLU:

### Katman A — Gerçek blok dizayn export'ları (otomatik)
`vivado -mode batch` ile demo projeler kurulur, `write_bd_layout` ile blok
dizaynlar **SVG** olarak dışa verilir (SVG başarısız olursa PDF alınıp build
sırasında SVG'ye çevrilir). Bu görseller HTML'de zoom/pan yapılabilir bir
sarmalayıcıyla sunulur (saf CSS/JS, kütüphane yok) — okuyucu gerçek dizaynı
dokümanın içinde gezebilmeli. Ayrıca `report_property`, `report_bd_utilization`,
adres haritası raporları Tcl'den alınır; dokümandaki tüm konfig tabloları bu
gerçek çıktılardan derlenir, elle uydurulmaz.

### Katman B — Açıklamalı GUI ekran görüntüleri (önce otomatik, sonra manuel)
GUI diyalogları (PS re-customize sekmeleri, CIPS sihirbazı, Address Editor,
Export Hardware akışı) batch export'la alınamaz. Yakalama iki aşamalıdır:

**B1 — Otomatik yakalama döngüsü (birincil yol):** Claude Code, **yerleşik
computer use yeteneğiyle** Vivado GUI'sini kendisi sürer. Prensip yine de
aynı kalır: *Tcl ile duruma getir, GUI'de sadece son adımı at, her karede
gör-doğrula.*
- Vivado, `vivado -mode tcl` + `start_gui` ile açılır; proje/BD açma, zoom,
  pencere düzeni gibi her şey `gui_capture/stage_*.tcl` durum scriptlerinden
  yapılır — GUI'de gezinme minimuma iner, computer use yalnızca diyalog
  açma/sekme değiştirme gibi son adımları atar.
- **Kapalı döngü zorunlu:** her eylemden sonra ekran doğrulanır (doğru sekme
  açık mı, diyalog yüklendi mi, beklenmedik popup var mı). Doğrulanmadan
  sonraki adıma geçilmez; ağır diyaloglar için cömert bekleme + yeniden
  deneme payı bırakılır. Kaydedilmemiş değişiklik uyarısı gibi popup'lar
  görülürse güvenli tarafta kalınır (değişiklik kaydedilmez, popup kapatılır).
- Kareler doğrudan `assets/screenshots/shot-NN.png` düzeninde kaydedilir;
  her başarılı karenin yanına yakalama log'u (hangi Tcl durumu + hangi
  eylemler) yazılır ki tekrar üretilebilir olsun.
- Bir kare 2-3 denemede doğrulanamazsa ısrar edilmez: o ekran `SHOT-LIST.md`'ye
  düşülür ve kullanıcıya raporlanır.

**B2 — Manuel shot-list (yedek yol):** Otomasyonun alamadığı kareler için
numaralı çekim listesi: nereye tıklanacağı, hangi sekme/satırın görünür
olacağı, pencere durumu. Kullanıcı kareleri çekip aynı adlandırmayla klasöre
bırakır.

Kaynağı hangisi olursa olsun, Claude Code her screenshot'ın üzerine **SVG
açıklama katmanı** bindirir (numaralı rozetler, oklar, vurgu çerçeveleri;
screenshot `<image>` olarak SVG içine gömülür, açıklamalar vektörel kalır).
Screenshot henüz yoksa build placeholder üretir ve eksikleri raporlar — doküman
kareler tamamlanmadan da iskelet olarak build edilebilir. Görsel tutarlılık
için tüm kareler aynı Vivado teması, aynı pencere boyutu (mümkünse maksimize,
%100 DPI) ile alınır; bu ayarlar yakalama scriptinde sabitlenir.

### Katman C — El yapımı kavramsal SVG'ler
Seri standardı: CSS değişkenli, çift temaya uyumlu, `<title>`+`<figcaption>`'lı
el çizimi şemalar. Akışlar, mimari kuşbakışları, karşılaştırmalar bu katmanda.
Gerçek ekranların yerini almazlar; onları kavramsal olarak tamamlarlar
(bir ekranda GÖRÜLENİN arkasındaki mimariyi çizerler).

### Demo Projelerin Tanımı (görsellerin kaynağı)

İki demo proje, tüm gerçek görsellerin ve raporların tek kaynağıdır:

**Demo 1 — RFSoC / ZCU111** (`vivado/rfsoc/`)
- Hedef: ZCU111 board part'ı (xczu28dr sınıfı; kesin part/board file adı
  Vivado 2023.2'de teyit edilir). Ekipteki oryantasyon kartıyla aynı olması
  bilinçli tercih — okuyucu dokümandaki projeyi elindeki kartla eşleştirir.
- İçerik: Zynq UltraScale+ PS IP (board preset uygulanmış) + öğretici PL
  seti: AXI GPIO, AXI Timer, AXI UARTLITE, AXI BRAM Controller + BRAM,
  concat üzerinden pl_ps_irq'ya bağlanmış interrupt'lar. Amaç gerçekçi ama
  okunabilir bir dizayn — 8-10 IP'lik, tek bakışta kavranabilir.
- RF Data Converter bilinçli olarak eklenmez (kılavuzun kapsamı PS analizi;
  RF tarafı RF Örnekleme Saha Kılavuzu'na çapraz link ile devredilir).

**Demo 2 — Versal / VPK120** (`vivado/versal/`)
- Hedef: VPK120 board part'ı (ekipteki gerçek Versal kartı; 2023.2'de board
  file yoksa eşdeğer VCK190'a düşülür ve doküman buna göre not alır).
- İçerik: CIPS (board preset) + NoC + DDRMC + AXI GPIO/Timer sınıfı birkaç
  PL IP'si — özellikle "DDR artık NoC'un arkasında" ve "PL IP'ye giden yol
  NoC'tan geçebilir" derslerini blok dizaynda GÖSTERECEK şekilde bağlanır.

**Ortak kurallar:**
- Projeler yalnızca Tcl ile kurulur (`create_bd.tcl`), tekrar üretilebilir;
  GUI'de elle kurulum yok.
- Bitstream/PDI üretimi GEREKMEZ — BD analizi, raporlar ve GUI ekranları
  sentezsiz alınabilir; saatler süren implementasyon bu iş için gereksiz.
  (.xsa export anlatımında bitstream'li/bitstream'siz fark bir kutuyla
  açıklanır.)
- Air-gap notu: board file'lar makinede yoksa Xilinx Board Store'dan offline
  kopya kurulumu README'de tarif edilir; hiçbiri bulunamazsa part-only
  kurulum + preset Tcl'i ile ilerlenir ve board preset kavramı yine anlatılır.

---

## 4. Tasarım Sistemi

Seriyle birebir aynı temel: koyu/açık çift tema (zemin `#0E1116`, kart
`#161B22`, vurgu `#4DA3FF`, altın `#E8B84B`, yeşil `#5BB0A6`), sticky TOC,
progress bar, anchor linkler, kopyala butonlu kod kutuları; `saha-notu`,
`tuzak`, `derin-dalis`, `analoji` kutuları aynen. Bu kılavuza özgü ekler:

- **`vivado-adim` bileşeni:** numaralı tıklama-yolu şeridi. Örn:
  `Flow Navigator → IP Integrator → Open Block Design`. Ekmek kırıntısı
  görünümlü, monospace, kopyalanabilir.
- **`ekran` bileşeni:** Katman B görselleri için standart çerçeve — üstte
  "Ekran N: <başlık>", altta rozet numaralarının açıklama listesi.
- **`yazilima-yansimasi` kutusu (turkuaz):** her ayar anlatımının sonunda
  "bu ayar senin dünyanda şuraya düşer" bağlantısı — xparameters.h satırı,
  device tree parçası, BSP davranışı ya da register değeri. Bu kutu kılavuzun
  ruhu; PS ayarı anlatılıp yazılım karşılığı verilmeyen bölüm eksik sayılır.
- **`deneme` kutusu (lab guide bileşeni):** her ana bölümde en az bir kısa
  uygulama görevi — okuyucu demo projeyi kendi Vivado'sunda açıp aynı ekrana
  gider ve somut bir soruyu cevaplar ("MIO tablosunda UART0'ın pinlerini bul
  ve baud saatinin kaynağını yaz"). Yapısı: hedef → `vivado-adim` yolu →
  gözlemlenebilir cevap → katlanabilir çözüm. Oryantasyon dokümanının görev
  kartının hafifletilmiş hali; checkbox + localStorage ilerlemesi burada da
  kullanılır. Teori bölümü + deneme kutusu ikilisi, dokümanın "hem ders
  kitabı hem lab guide" karakterini kurar.
- Zoom/pan'li BD görüntüleyici (Katman A için).

---

## 5. Görselleştirme Envanteri (asgari)

Katman A (otomatik, gerçek): en az 6 export —
RFSoC demo BD tam görünüm + PS-yakın kırpım, Versal demo BD tam görünüm +
CIPS/NoC-yakın kırpım, her iki projenin adres haritası raporu (tabloya işlenir).

Katman B (screenshot + açıklama): **Parametre Atlası kapsamı** — hedef sayı
sabit değil, kapsam sabittir: *yazılıma parametre olarak çıkan her ayar
grubu* gerçek Vivado ekranıyla, ilgili alan vurgu kutusuna alınmış halde
gösterilir. Pratikte 25-40 kare beklenir: proje açılışı, blok dizayn görünümü,
PS IP re-customize'ın TÜM yazılım-ilgili sekmeleri (I/O Configuration MIO
tablosu, Clock Configuration'ın her saat grubu, DDR, PS-PL AXI portları,
interrupt satırları), CIPS sihirbazının karşılık gelen sayfaları, NoC/DDRMC
görünümleri, Address Editor, Validate sonucu, Export Hardware akışı.
Kesin liste `gui_capture/shots.yaml` manifestinde yaşar; SHOT-LIST.md yalnızca
otomatik alınamayan kareleri listeler.

Katman C (el yapımı): en az 12 şema —

| # | Şema | Bölüm |
|---|------|-------|
| 1 | "Donanımcının dünyası / senin dünyan" el sıkışma haritası: Vivado → .xsa → Vitis → uygulama zinciri | 1 |
| 2 | Vivado kuş bakışı: proje → blok dizayn → sentez/implementasyon → bitstream; "yazılımcının umursadığı şerit" vurgulu | 2 |
| 3 | Blok dizayn okuma anahtarı: IP kutusu anatomisi (port türleri, AXI arayüz gösterimi, clock/reset iğneleri) | 3 |
| 4 | MPSoC PS kuşbakışı: APU/RPU, sabit çevre birimleri, MIO/EMIO çıkış kapıları, PS-PL AXI kapıları | 4 |
| 5 | MIO vs EMIO yönlendirme şeması: aynı UART'ın iki farklı yoldan dünyaya çıkışı | 5 |
| 6 | Clock ağacı basitleştirilmiş: PS kaynak saatler → PL'ye giden fabric clock'lar → IP'lerin beslenmesi | 5 |
| 7 | PS-PL arayüz haritası: M_AXI_HPM / S_AXI_HP / ACP pencereleri, hangi yönde kim master | 6 |
| 8 | Interrupt yolculuğu: PL IP → pl_ps_irq → GIC → yazılımdaki ISR; ID eşleşmesi | 6 |
| 9 | Adres çözümleme zinciri: Address Editor satırı → .xsa → xparameters.h #define → koddaki base pointer | 7 |
| 10 | Versal vs MPSoC mimari farkı: PS IP'nin yerini CIPS+NoC+AI Engine dünyasının alması, DDR denetleyicinin NoC'a taşınması | 8 |
| 11 | NoC sezgisi: yatay/dikey ağ, NMU/NSU kapıları, "AXI'nin şehir içi metrosu" analojisi | 8 |
| 12 | Bring-up öncesi PS kontrol listesi karar akışı (kılavuzun kapanış şeması) | 10 |

---

## 6. İçindekiler (bölüm iskeleti)

Her bölüm: "neden umursamalısın" girişi → anlatı → ekran/şema →
`yazilima-yansimasi` kutuları → bölüm özeti.

### Bölüm 0 — Önsöz: Bu Kılavuz Ne Değildir
FPGA tasarım eğitimi değil; RTL yazmayacağız, timing kapatmayacağız.
Amaç: teslim aldığın projeyi okumak. Sürüm notu (2023.2). Okuma rotaları
("acil bring-up: 3-5-7-10").

### Bölüm 1 — İki Dünyanın El Sıkışması
Donanım-yazılım iş bölümü; teslimat zinciri (Vivado projesi → .xsa → Vitis
platform → BSP → uygulama); yazılımcının Vivado'da NE aradığı (4 soru:
hangi IP'ler var, adresleri ne, clock'ları ne, interrupt'ları nereye bağlı).
`ekip-notu` tarzı kültür: donanımcıya doğru soru sorma.

### Bölüm 2 — Vivado'ya İlk Giriş (Yazılımcı Rotası)
Projeyi açma (xpr vs proje dizini), arayüz turu: Flow Navigator, Sources,
blok dizayn penceresi; "yanlışlıkla neyi bozabilirim" korkusunun giderilmesi
(read-only inceleme alışkanlıkları, kaydetmeden kapatma, git'teki projeye
dokunmama görgüsü). Sentez/implementasyon/bitstream'in bir paragraflık
sezgisi — "bu düğmelere basmak senin işin değil ama ne yaptıklarını bil".

### Bölüm 3 — Blok Dizaynı Okuma Sanatı
IP kutuları, portlar, AXI arayüz çizgileri, clock/reset dağıtımı; hiyerarşi
gezinme, sinyal takibi (bir çizgiyi ucundan ucuna izleme, highlight);
arama ile IP bulma; Interconnect/SmartConnect'in "trafik göbeği" rolü.
Demo RFSoC BD'si (Katman A görseli) üzerinde rehberli tur: "şu kutu PS,
şu AXI GPIO, şu çizgi interrupt".

### Bölüm 4 — Kalbin İçi: UltraScale+ PS IP'si
PS IP'ye çift tıklayınca açılan dünyanın haritası; sekmelerin kuşbakışı;
board preset kavramı ("bu yüzlerce ayarı kimse elle girmedi").
RFSoC'un PS'inin MPSoC PS'i ile aynı olduğu netleştirilir — ZCU111
anlatımı tüm UltraScale+ ailesini kapsar.

### Bölüm 5 — PS Ayarları I: I/O, Clock, DDR
**I/O Configuration:** MIO tablosu okuma (hangi çevre birimi hangi pinde,
MIO bank gerilimleri), EMIO kavramı ve "UART'ım PL'den mi çıkıyor?" analizi.
**Clock Configuration:** kaynak saatler, PLL'ler, çevre birimi saatleri,
PL fabric clock'ları — "baud rate hesabın bu sayfadaki değere bağlı".
**DDR Configuration:** açık mı, tip/hız, "heap'in fiziksel evi burası".
Her alt başlıkta `yazilima-yansimasi` zorunlu.

### Bölüm 6 — PS Ayarları II: PS-PL Arayüzleri ve Interrupt'lar
PS-PL Configuration sekmesi: master/slave AXI portları (HPM/HP/ACP),
hangi IP hangi porttan bağlı; interrupt satırları (pl_ps_irq), IRQ ID'lerin
yazılımdaki karşılığı; reset sinyalleri. "PL'deki IP'me neden erişemiyorum"
teşhisinin konfig tarafı.

### Bölüm 7 — Adres Haritası: Address Editor'dan xparameters.h'a
Address Editor okuma (segment, base/high, aralık); unmapped tehlikesi;
adres çakışması kavramı; validate design'ın anlamı; .xsa export akışı ve
içinde ne taşındığı; Vitis tarafında platformun doğuşu, xparameters.h
eşleşmesi — şema #9'un ete kemiğe bürünmesi. Demo projenin GERÇEK adres
haritası (Katman A raporu) tablo olarak işlenir ve satır satır okunur.

### Bölüm 8 — Versal: Yeni Dünya, Yeni Sözlük
Versal mimari farkı: PS IP yerine **CIPS** (Control, Interfaces & Processing
System); **NoC** kavramı ve DDR denetleyicinin NoC arkasına taşınması
(DDRMC); "blok dizaynda DDR'ı PS içinde arama, NoC'a bak" uyarısı;
CIPS sihirbazında yazılımcının bakacağı sayfalar (PS PMC/PL config, clocking,
peripheral'lar); PDI vs bitstream farkına bir paragraf; AI Engine'e sadece
pencere. Demo Versal BD'si üzerinde rehberli tur.

### Bölüm 9 — Vaka Analizleri (rehberli okuma turları)
Üç kısa vaka, her biri gerçek demo proje üzerinde soru-cevap kurgusuyla:
(a) "Bu projede debug UART'ı hangi pinde ve kaç baud?" — iz sürme;
(b) "PL'deki timer IP'sinin adresi ve interrupt ID'si ne?" — uçtan uca takip;
(c) "Donanımcı 'DDR'ı NoC'a aldık' dedi, Versal projesinde bunu doğrula" —
Versal okuması. Her vaka `vivado-adim` şeritleriyle adım adım.

### Bölüm 10 — SENTEZ: Bring-up Öncesi PS Kontrol Listesi
Kılavuzun kapanış hediyesi: yeni bir proje teslim alındığında yürütülecek
maddeler halinde kontrol listesi (yazdırılabilir his) + karar akışı şeması
(#12). Her madde ilgili bölüme link verir.

### Ek A — Tcl Hızlı Başvuru (yazılımcı seti)
Projeyi batch açma, BD'yi SVG'ye export etme, adres haritası raporu alma,
IP property dökme — "GUI açmadan cevap alma" reçeteleri. Repo'daki
scriptlerin kullanımı.

### Ek B — Sözlük
BD/IP/XSA/CIPS/NoC/MIO... alfabetik, bölüm linkli.

### Ek C — Parametre Atlası
Kılavuzun referans çekirdeği: yazılıma parametre olarak çıkan her ayarın
tek tablosu. Satır yapısı: parametre → hangi ekranda (Ekran N linki) →
ne anlama gelir (bir cümle) → yazılım karşılığı (xparameters/BSP/register) →
ilgili bölüm linki. Bölümlerdeki anlatımlardan otomatik derlenir; "hızlıca
şu ayara bakacağım" kullanım senaryosunun tek durağıdır.

---

## 7. Yazım Kuralları

1. Pedagojik sıra ve tanımsız kavram yasağı — seriyle aynı.
2. Ton: usta-çırak, hype yok, emoji yok. Vivado korkusunu ciddiye alıp
   nazikçe söken bir dil.
3. **Her ayar anlatımı `yazilima-yansimasi` ile kapanır** — yazılım karşılığı
   verilmeyen ayar anlatımı eksik sayılır.
4. **Parametre = gerçek ekran kuralı:** yazılıma parametre olarak çıkan her
   ayar grubu, ilgili alanı vurgu kutusuna alınmış GERÇEK Vivado ekranıyla
   gösterilir; el yapımı SVG bu ekranların yerine geçemez, yalnızca arkadaki
   kavramı tamamlar. Her ana bölümde en az bir `deneme` kutusu bulunur.
5. Teknik doğruluk: menü yolları, sekme adları, Tcl komutları 2023.2'de
   doğrulanır (scriptler gerçekten koşularak); koşulamayan ortamda komut
   çıktısı varsayımla yazılmaz, "doğrulanacak" işaretiyle bırakılıp
   kullanıcıya raporlanır. Versal/MPSoC iddiaları resmî dokümantasyondan
   (TRM, PG201/PG352 sınıfı IP kılavuzları) web ile teyit edilir.
6. Bölüm uzunluğu: 800–1500 kelime; PS ayar bölümleri (5-6) ve Versal (8)
   2000'e çıkabilir.
7. Screenshot'lı anlatımda metin screenshot'a köle olmaz: ekran değişse bile
   paragraf tek başına anlamlı kalmalı.

---

## 8. Üretim Akışı (Claude Code için)

1. Repo iskeleti + CLAUDE.md + tema; boş bölümle build doğrula.
2. **Demo proje hattı:** `vivado/rfsoc/create_bd.tcl` (ZCU111 board part,
   PS + board preset + AXI GPIO + AXI Timer + AXI UARTLITE + interrupt
   bağlantıları + BRAM gibi öğretici bir set) ve `vivado/versal/create_bd.tcl`
   (CIPS + NoC + DDRMC + birkaç AXI IP; hedef kart olarak eldeki Versal kartı
   veya xcvp1202 sınıfı bir part) yazılır. `export_visuals.tcl` ile BD
   layout'ları ve raporlar alınır. Vivado ortam yolu kullanıcıdan istenir;
   scriptler koşulur, çıktılar `assets/bd-exports/` ve `assets/reports/`e düşer.
3. **GUI yakalama turu (B1):** önce platform tespiti ve araç kontrolü yapılır
   (xdotool/ImageMagick veya PowerShell yolu; eksikse kullanıcıya bildirilir).
   Tek bir pilot kareyle uçtan uca döngü (Tcl durumu → eylem → screenshot →
   gör-doğrula) kanıtlanır, sonra tüm kare listesi otomatik yürünür. Her kare
   Claude Code tarafından görsel olarak doğrulanıp onaylanır; alınamayanlar
   `SHOT-LIST.md`'ye (B2) düşülür ve kullanıcıya kısa bir "kalan kareler"
   raporu verilir. Screenshot'lar beklenirken içerik yazımı placeholder'larla
   sürer.
4. Bölümler sırayla yazılır; konfig tabloları Katman A raporlarından derlenir.
5. Screenshot'lar geldikçe SVG açıklama katmanları bindirilir.
6. Vaka analizleri (9) ve sentez (10) en son.
7. Son tur: tüm `yazilima-yansimasi` kutularının varlık kontrolü, çapraz
   linkler, sözlük, eksik screenshot raporu.

## 9. Kalite Çıtası (bitmiş sayılma kriterleri)

- [ ] `dist/index.html` internetsiz kusursuz; BD görüntüleyicide zoom/pan çalışıyor
- [ ] Her iki demo projenin Tcl scriptleri temiz koşuyor ve README'li
- [ ] Katman A: en az 6 gerçek BD export'u + gerçek adres haritası tabloları
- [ ] Katman B: kareler önce otomatik döngüyle denendi, her kare gör-doğrulandı
      ve tekrar üretim log'u var; alınamayanlar SHOT-LIST'te net; her screenshot
      açıklama katmanlı
- [ ] Katman C: en az 12 el yapımı SVG, iki temada okunaklı
- [ ] Her ayar anlatımında `yazilima-yansimasi` kutusu var
- [ ] Parametre Atlası (Ek C) tam: yazılıma çıkan her parametre gerçek
      ekran linkli ve yazılım karşılıklı
- [ ] Her ana bölümde en az bir `deneme` kutusu var ve demo proje üzerinde
      gerçekten yürünebilir
- [ ] Üç vaka analizi uçtan uca yürünebilir
- [ ] Bring-up kontrol listesi tek başına paylaşılabilir kalitede
- [ ] Tcl hızlı başvuru eki çalışır komutlardan oluşuyor
