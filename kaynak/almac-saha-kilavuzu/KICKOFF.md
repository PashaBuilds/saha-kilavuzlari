# KICKOFF — almac-saha-kilavuzu

> Bu dosya, projenin tek başlangıç talimatıdır. Claude Code bu dosyayı okuyarak
> üretime başlar. Repo kökünde durur; CLAUDE.md bu dosyaya referans verir.
> Çelişki halinde öncelik sırası: bu dosya > CLAUDE.md > referans repodaki alışkanlıklar.

---

## 0. Bu Dosya Nasıl Okunur

| Bölüm | Ne söyler |
|---|---|
| 1–2 | Proje kimliği, hedef kitle, kapsam sınırları |
| 3 | Tüm dokümanı birbirine bağlayan **referans senaryo** (tek bir darbenin yolculuğu) |
| 4 | Pedagoji: bilginin hangi sırayla ve hangi kalıpla kurulacağı |
| 5 | Tasarım sistemi ve içerik bileşenleri |
| 6 | **İçerik haritası** — Kısım/Bölüm hiyerarşisi, her bölümün içeriği, görselleri, widget'ları |
| 7 | İnteraktif widget kataloğu ve ortak DSP çekirdeği |
| 8 | Görsel (SVG / Mermaid / formül) kuralları |
| 9 | Repo yapısı ve build hattı |
| 10 | Doğruluk, kaynak ve gizlilik kuralları + bilinen-cevap kontrolleri |
| 11 | Çalışma fazları |
| 12 | Kabul kriterleri ve kapanış raporu |
| 13 | Başlatma promptu |

---

## 1. Proje Kimliği

- **Klasör / repo adı:** `almac-saha-kilavuzu`
- **Doküman adı:** *Antenden PDW'ye — Radar ve Elektronik Harp Sayısal Almaç
  Sistemleri Saha Kılavuzu*
- **Seri:** "Saha Kılavuzu" serisinin altıncı üyesi (Bellek Mimarisi, RF Örnekleme,
  Ethernet, Lokal LLM, Vivado'yu Yazılımcı Gibi Okumak). Aynı görsel aile, aynı
  kalite çıtası: tek başına literatür oluşturacak kapsamda, pedagojik, "çok
  kaliteli bir teknik blog okuyorum" hissi veren **tek, offline, self-contained HTML**.
- **Referans repo:** `/Users/mpcukur/Projects/claude/rf-sampling-saha-kilavuzu`
  (çıktısı `dist/index.html`). Üretime başlamadan önce bu repoyu incele; tasarım
  sistemi, bileşen sınıfları, build yaklaşımı ve formül çözümü oradan devralınır.
  Varsa diğer seri repolarına da (`ethernet-saha-kilavuzu` vb.) bak.
- **Dil:** Türkçe anlatım, teknik terimler İngilizce aslıyla. Terimin ilk
  geçtiği yerde `Türkçe karşılık (English term)` kalıbı, sonrasında yerleşik
  olan hangisiyse o (ör. "decimation", "eşik", "gürültü tabanı").

### 1.1 Hedef Kitle

Birincil okur: FPGA'li bir almaç kartının PS tarafında çalışan **gömülü
yazılımcı**. Register'a eşik yazıyor, NCO frekansı ayarlıyor, DMA ile PDW
çekiyor; ama o register'ın arkasındaki DSP'nin ne yaptığını, RF tarafın neden
öyle tasarlandığını, MATLAB'daki algoritmanın FPGA'ya nasıl indiğini bütün
olarak görmemiş.

İkincil okurlar: DSP'ye yeni giren sayısal tasarımcı (RTL biliyor, sinyal
işleme teorisi zayıf) ve RF/sistem tarafından gelip sayısal zinciri anlamak
isteyen mühendis. Doküman üç dünyayı (**RF**, **almaç/DSP**, **sayısal
tasarım**) tek bir anlatıda birleştirir; hiçbirinde ön bilgi varsaymaz ama
hiçbirinde de yüzeysel kalmaz.

### 1.2 Misyon — Okuyan Kişi Bitirdiğinde

1. Antenden PDW FIFO'suna kadar olan zinciri tahtaya çizebilmeli; her bloğun
   **neden** orada olduğunu söyleyebilmeli.
2. RF / IF / baseband, örnekleme frekansı, Nyquist bölgesi, real ve I/Q veri
   kavramlarını sayısal örnekle açıklayabilmeli.
3. Bir ADC datasheet'ini okuyup SNR, SFDR, ENOB, NSD, jitter değerlerinin
   sisteme etkisini yorumlayabilmeli.
4. NCO → mixer → filtre → decimation zincirinde her adımda spektrumun, veri
   hızının ve bit genişliğinin nasıl değiştiğini izleyebilmeli.
5. FFT'nin boyu, penceresi, ölçeklemesi ve gürültü tabanı ilişkisini doğru
   kurabilmeli; "FFT'de gürültü tabanı neden datasheet SNR'ından aşağıda?"
   sorusunu cevaplayabilmeli.
6. Eşik, gürültü tahmini, CFAR, Pfa/Pd ilişkisini hem sezgisel hem formülle
   açıklayabilmeli; "eşiği 3 dB indirirsem ne olur?" sorusunu cevaplayabilmeli.
7. Bir PDW'nin alanlarını, her alanın nasıl ölçüldüğünü ve ölçüm hatasının
   SNR'a nasıl bağlı olduğunu bilmeli; PDW'yi C tarafında parse edebilmeli.
8. Almaç mimarilerini (kristal video'dan direct RF sampling'e) güçlü/zayıf
   yanlarıyla karşılaştırabilmeli.
9. MATLAB modelinden FPGA gerçeklemesine giden akışı ve bit-true doğrulamanın
   mantığını anlayabilmeli.
10. Sahada gördüğü bir belirtiyi (beklenmeyen spur, patlayan false alarm, kısa
    ölçülen PW, aynalı spektrum) olası nedenlere bağlayabilmeli.

---

## 2. Kapsam Sınırları

**Kapsam içi:** Darbeli/CW sinyal temelleri, gürültü ve hassasiyet, RF ön uç
yapıtaşları, almaç mimarileri kataloğu, örnekleme ve ADC performansı, direct
RF-sampling ADC'ler ve ADC→FPGA arayüzleri, FPGA'da sabit noktalı DSP, MATLAB→FPGA
akışı, DDC zinciri (NCO, mixing, FIR/CIC/halfband, decimation), kanallaştırma,
FFT ve pencereleme, tespit teorisi ve CFAR, PDW üretimi ve parametre ölçümü,
PS tarafı kontrol yüzeyi, doğrulama ve hata ayıklama.

**Ufuk turu (yalnızca genel bakış, tek bölüm):** PDW sonrası işleme —
deinterleaving, PRI analizi, emiter tanımlama. Radar tarafında matched filter /
pulse compression ve Doppler işleme yalnızca "EH almacından farkı" bağlamında.

**Kapsam dışı:** Karıştırma (jamming) teknikleri, anten tasarımı, belirli
gerçek sistemlerin/tehditlerin parametreleri, şirket içi tasarım detayları.

**RF Örnekleme Saha Kılavuzu ile ilişki:** Örnekleme teoremi, aliasing ve
Nyquist bölgeleri orada derinlemesine işlendi. Bu kılavuzda o konular **kısa
bir hatırlatma + bu kılavuza özgü uzantı** (frekans planlama, harmonik/spur
katlanması, almaç bağlamı) olarak yer alır; "derin anlatım için bkz. RF
Örnekleme Saha Kılavuzu" notu düşülür. Önce referans repoda neyin ne derinlikte
anlatıldığını çıkar, tekrarı buna göre ayarla.

---

## 3. Referans Senaryo — "Bir Darbenin Yolculuğu"

Dokümanın omurgası: **tek bir darbe antenden girer, PDW olarak çıkar.** Her
bölüm bu yolculuğun bir durağıdır ve sayısal örneklerini aynı senaryodan alır.
Sayılar öğreticidir; gerçek bir sistemi temsil etmez (bunu dokümanda da belirt).

| Parametre | Değer |
|---|---|
| Gelen sinyal | X-bant, RF = 9.4 GHz, darbeli |
| Darbe | PW = 1 µs, PRI = 1 ms (duty %0.1); varyant B: darbe içi 10 MHz LFM |
| LO (low-side) | 7.6 GHz → IF = 1.8 GHz; image = 5.8 GHz |
| Ön uç | toplam NF = 6 dB (kaskad hesabı bölümde türetilir) |
| ADC | direct IF sampling, fs = 2400 MSPS, 14-bit, real çıkış |
| Nyquist bölgesi | IF 1.8 GHz → 2. bölge (1200–2400 MHz) → alias = 600 MHz, **spektrum evrik** |
| DDC | NCO = 600 MHz, kompleks mixing, toplam decimation = 8 |
| DDC çıkışı | 300 MSPS kompleks I/Q (16+16 bit), ±150 MHz |
| Zaman çözünürlüğü | 3.33 ns/örnek; 1 µs darbe = 300 örnek |
| Tespit | güç zarfı (I²+Q²), CA-CFAR, N = 16 referans, Pfa = 1e-6 |
| FFT yolu | N = 1024, Hann, %50 overlap → bin = 293 kHz |

Türetilmiş beklenen değerler (Claude Code yeniden hesaplayıp doğrular; bölüm
metinlerinde adım adım türetilir):

- Gürültü tabanı (B = 300 MHz): −174 + 84.8 + 6 ≈ **−83.2 dBm**
- 15 dB tespit SNR'ı ile hassasiyet ≈ **−68 dBm**
- 14-bit ideal kuantizasyon SNR'ı = 6.02·14 + 1.76 = **86.0 dB**
- Decimation işlem kazancı: 10·log10(1200/300) = **6 dB**
- 1 µs dikdörtgen darbenin ana lob genişliği (null-to-null) = **2 MHz**
- Pfa = 1e-6 için Rayleigh zarfta eşik = σ·√(−2·ln Pfa) = **5.26σ**
- CA-CFAR çarpanı (N=16, Pfa=1e-6, kare-yasa): α = N·(Pfa^(−1/N) − 1) ≈ **21.9**

**"Sinyal pasaportu" şeridi:** Zincirin her durağında aynı formatta küçük bir
bilgi şeridi gösterilir: `alan (analog/sayısal) · frekans konumu · real/kompleks ·
fs · bit genişliği · veri hızı (Gbps) · SNR`. Okur, pasaportun durak durak
nasıl değiştiğini izleyerek bütünü kurar. Bölüm 28'de tüm pasaportlar tek
tabloda toplanır.

---

## 4. Pedagoji — Bilgi Nasıl Kurulur

### 4.1 İlkeler

1. **Temelden yukarı, boşluk bırakmadan.** Bir kavram, kendisinden önce
   anlatılmamış hiçbir kavrama yaslanamaz. Her bölüm başında "Ön koşul" ve "Bu
   bölüm neyi açar" satırları bulunur. Kısım 0'da tüm bölümlerin **kavram
   bağımlılık haritası** (SVG) yer alır.
2. **Önce sezgi, sonra resim, sonra formül, sonra sayı.** Formül asla ilk
   cümle olmaz. Her formülün hemen altında referans senaryodan sayısal örnek.
3. **Her kavramın üç yüzü.** Mümkün olan her yerde aynı kavram üç gözle
   gösterilir: *RF/sinyal gözüyle* (ne oluyor), *FPGA gözüyle* (nasıl
   gerçekleniyor, kaç bit, kaç DSP slice, latency), *yazılımcı gözüyle* (hangi
   register, hangi birim dönüşümü, ne ters gidebilir).
4. **Gör → oyna → anla.** Statik şema kavramı tanıtır; hemen ardından gelen
   widget "bu parametreyi değiştirirsem sonuca ne olur" sorusunu okura sordurur.
   Her widget'ın altında "Ne gözlemlemeliyim?" kutusu (2–4 yönlendirilmiş deney).
5. **Zaman ve frekans hep yan yana.** Sinyal gösteren her görselde mümkünse
   zaman domaini ve frekans domaini birlikte verilir.
6. **Yanlış sezgileri açıkça avla.** Her bölümde en az bir "tuzak" kutusu:
   sahada gerçekten yapılan hata veya yaygın kavram yanılgısı.
7. **Blok şemada tutarlı dil.** Bir blok (ör. NCO) bir kez tasarlanır, tüm
   dokümanda aynı sembolle çizilir. Büyük resim posterindeki blok, ilgili
   bölümde "büyüteç altına alınır" (aynı şekil, vurgulu).

### 4.2 Bölüm Şablonu (her bölüm bu iskeleti izler)

1. **Başlık şeridi:** bölüm no, başlık, tahmini okuma süresi, ön koşul, açtığı bölümler
2. **Zincirdeki yerim:** büyük resim şemasının küçük hali, bu bölümün bloğu vurgulu
3. **Neden önemli:** 3–5 cümle, sahadan bir soru ile açılır
4. **Sezgi / analoji**
5. **Kavram anlatımı** — görsellerle iç içe
6. **Matematik** — minimal, her sembol tanımlı, birimli
7. **Referans senaryoda sayısal örnek** + sinyal pasaportu güncellemesi
8. **FPGA'da nasıl gerçeklenir**
9. **Yazılımcıya dokunan yer** (register, birim dönüşümü, C snippet)
10. **Tuzaklar**
11. **Özet kartı** (5–7 madde) + **Kendini sına** (3–5 soru, açılır cevaplı)
12. **Köprü:** sonraki bölüme tek paragraf geçiş

Şablonun bir maddesi bir bölüm için anlamsızsa (ör. Bölüm 1'de "FPGA'da nasıl")
atlanır; zorla doldurulmaz.

### 4.3 Okuma Rotaları

Kısım 0'da üç rota sunulur (TOC'ta filtrelenebilir rozetlerle):
- **Tam yolculuk:** baştan sona
- **Yazılımcı hızlı rotası:** 2, 3, 8, 9, 14–16, 18–19, 21, 23–26, 30
- **Sayısal tasarımcı rotası:** 2, 8–9, 11–20, 22–23, 26, 29

---

## 5. Tasarım Sistemi

Referans repodaki tasarım sistemi **aynen** devralınır; aşağıdakiler hatırlatma
ve bu kılavuza özgü eklerdir.

### 5.1 Devralınanlar

- Çift tema (koyu varsayılan + açık), tüm renkler CSS değişkeni, tema seçimi kalıcı
- Koyu tema çekirdek paleti: arka plan `#0E1116`, kart `#161B22`, vurgu
  `#4DA3FF`, altın `#E8B84B`, yeşil `#5BB0A6` (açık tema karşılıkları referans repodan)
- Sticky TOC, scroll-aware vurgulama, okuma ilerleme çubuğu, bölüm içi anchor'lar
- İçerik bileşenleri: `saha-notu`, `tuzak`, `derin-dalis` (açılır), `analoji`,
  `komut` (kod/komut kutusu)
- Elle yazılmış, tema-duyarlı inline SVG'ler; CDN / dış kaynak **yok**
- Yazdırma stil sayfası (açık tema, widget'lar statik snapshot)

### 5.2 Bu Kılavuza Özgü Yeni Bileşenler

| Bileşen | İşlev |
|---|---|
| `sinyal-pasaportu` | Zincir durağındaki sinyal özet şeridi (bkz. §3) |
| `zincirdeki-yerim` | Büyük resmin mini hali, aktif blok vurgulu; tıklayınca o bölüme gider |
| `uc-goz` | Üç sekmeli kutu: RF gözüyle / FPGA gözüyle / Yazılımcı gözüyle |
| `formul-karti` | Formül + sembol tablosu + birimler + sayısal örnek |
| `matlab-fpga` | Yan yana iki sütun: MATLAB (floating) ↔ FPGA (fixed-point) karşılığı |
| `belirti-neden` | Hata ayıklama tablosu satırı: belirti → olası nedenler → nasıl kontrol edilir |
| `kendini-sina` | Açılır cevaplı soru seti |
| `widget` | İnteraktif blok kabı: başlık, kontrol paneli, çizim alanı, preset'ler, "Ne gözlemlemeliyim?" |
| `mimari-karti` | Almaç mimarisi kartı: blok şema + özellik çubuğu + artı/eksi + tipik kullanım |

### 5.3 Şema Renk Dili (tüm SVG'lerde sabit)

| Alan | Renk değişkeni | Çizgi |
|---|---|---|
| Analog RF / IF yolu | altın | düz, kalın |
| Sayısal veri yolu (örnekler) | mavi vurgu | düz |
| Kontrol / PS / register | yeşil | ince |
| Saat / LO / referans | nötr gri | kesikli |
| Gürültü / istenmeyen bileşen | kırmızımsı uyarı tonu | noktalı / yarı saydam |

Spektrum çizimlerinde: istenen sinyal mavi, image/alias/spur kırmızımsı,
gürültü tabanı gri dolgu, filtre yanıtı altın kesikli. Bu dil Kısım 0'da bir
"lejant" kartıyla okura öğretilir.

---

## 6. İçerik Haritası

Notasyon: **G-xx** statik görsel (SVG), **W-xx** interaktif widget (§7'de
tanımlı). Madde listeleri asgari içeriktir; konu bütünlüğü gerektiriyorsa
genişlet, ama bölüm sırasını ve bağımlılık zincirini bozma. "Saymadığım önemli
her şey" ilkesi geçerli: bir bölümü yazarken eksik kalan temel bir kavram fark
edersen ekle ve kapanış raporunda bildir.

### KISIM 0 — Yön Bulma

**Bölüm 0 · Bu Kılavuz ve Büyük Resim**
- Kılavuzun amacı, kimin için, nasıl okunur, okuma rotaları
- **G-00 Poster şema — "Antenden PDW'ye":** anten → limiter/LNA → preselector →
  mixer+LO → IF filtre/kazanç → anti-alias → ADC → (JESD/LVDS) → FPGA: DDC (NCO,
  mixer, filtre, decimation) → iki kol: *zaman kolu* (zarf → gürültü tahmini →
  eşik → darbe FSM → parametre ölçümü) ve *frekans kolu* (pencere → FFT → tepe
  bulma) → PDW birleştirme → FIFO → DMA → PS/yazılım. Üstte üç dünya bandı:
  RF dünyası | veri dönüştürme | sayısal dünya | yazılım dünyası. Her blok
  tıklanabilir, ilgili bölüme gider.
- G-01 Kavram bağımlılık haritası (bölümler arası ön koşul grafı)
- G-02 Şema renk dili lejantı
- Referans senaryonun tanıtımı (§3 tablosu, okur diliyle)
- Radar almacı ile EH almacı arasındaki temel fark (tek paragraf + tablo):
  bilinen sinyal/eşlenik filtre vs bilinmeyen sinyal/geniş bant/POI

### KISIM I — Temeller: Sinyal, Spektrum, Gürültü

**Bölüm 1 · Sinyalin Dili: Genlik, Frekans, Faz ve dB**
- Sinüs, genlik/frekans/faz; zaman domaini ↔ frekans domaini fikri (Fourier'nin sezgisi)
- Güç ve voltaj; dB, dBm, dBW, dBc, dBFS, dBm/Hz — hangisi neye göre
- 10·log vs 20·log; 3 dB / 6 dB / 10 dB / 20 dB ezber kartı
- 50 Ω dünyası: dBm ↔ Vrms ↔ Vpp dönüşümü
- G-10 aynı sinyalin zaman ve frekans görünümü; G-11 dB merdiveni (−174 dBm/Hz'den +30 dBm'e, tipik seviyeler işaretli)
- W-01 dB dönüştürücü

**Bölüm 2 · Kompleks Sinyal ve I/Q**
- Fazör, Euler, dönen vektör; cos = iki ters dönen fazörün toplamı → **negatif frekans**
- Reel sinyalin simetrik spektrumu; kompleks sinyalin tek taraflı spektrumu
- I ve Q nedir; neden iki kanal; genlik = √(I²+Q²), faz = atan2(Q,I), anlık frekans = dφ/dt
- Analitik sinyal, Hilbert dönüşümü (sezgi düzeyi)
- "Real veri mi I/Q mu?" — ADC'den hangisi gelir, ne zaman hangisi (Bölüm 15'e köprü)
- I/Q dengesizliği (gain/phase) → image bileşeni; I/Q yer değişirse spektrum aynalanır
- G-20 dönen fazör ve I/Q izdüşümleri; G-21 reel vs kompleks spektrum; G-22 I/Q imbalance image'ı
- W-02 fazör laboratuvarı

**Bölüm 3 · Darbeli Sinyalin Anatomisi**
- PW, PRI/PRF, duty cycle, tepe/ortalama güç, rise/fall time, droop, overshoot
- Darbe katarının spektrumu: sinc zarfı, PRF aralıklı çizgiler, bant genişliği ≈ 1/PW
- Darbe içi modülasyon (MOP): LFM/chirp, faz kodlu (Barker vb.), frekans atlamalı, CW/FMCW
- PRI tipleri: sabit, stagger, jitter, dwell-switch (tanım düzeyi)
- Almaç tasarımına etkisi: kısa darbe ↔ geniş bant ↔ daha çok gürültü
- G-30 darbe anatomisi (ölçü noktaları işaretli); G-31 PW–spektrum ilişkisi; G-32 MOP türlerinin zaman-frekans görünümü
- W-03 darbe katarı ↔ spektrum

**Bölüm 4 · Gürültü, SNR ve Hassasiyet**
- Termal gürültü: kTB, −174 dBm/Hz; bant genişliği ile ölçekleme
- Noise figure / noise factor, gürültü sıcaklığı; **Friis kaskad formülü** — LNA neden en başta
- Gürültü tabanı; SNR; minimum tespit edilebilir sinyal (MDS); hassasiyet denklemi
- Dinamik aralık kavramına giriş: altta gürültü, üstte doyum
- Bant genişliği ↔ hassasiyet ↔ POI takası (EH almacının temel ikilemi)
- Gürültünün istatistiği: Gauss, beyaz, güç spektral yoğunluğu (Bölüm 21'e köprü)
- G-40 kaskad zincirde sinyal ve gürültü seviyesi diyagramı (level diagram); G-41 bant genişliği–gürültü tabanı
- W-04 kaskad NF / kazanç / hassasiyet hesaplayıcı

### KISIM II — RF Ön Uç ve Almaç Mimarileri

**Bölüm 5 · RF Zincirinin Yapıtaşları**
- Anten (yalnızca arayüz düzeyi), limiter, LNA, preselector/bant geçiren filtre,
  zayıflatıcı/AGC/STC, mixer, LO (PLL/sentezleyici), IF filtre ve yükselteç,
  anti-alias filtre, balun / ADC sürücü
- Her blok için: ne yapar, kilit parametre (kazanç, NF, P1dB, IP3, izolasyon, VSWR)
- Doğrusal olmama: P1dB, IP2/IP3, intermodülasyon (2f1−f2), harmonikler; **çift ton SFDR**
- Anlık dinamik aralık vs toplam dinamik aralık (AGC ile)
- LO faz gürültüsü ve karşılıklı karışma (reciprocal mixing) — tanım düzeyi
- G-50 her bloğun sembolü + tek satır işlev kartları; G-51 çift ton testi ve IMD3 spektrumu; G-52 seviye planı (kazanç/NF/IP3 kaskadı)

**Bölüm 6 · Frekans Dönüştürme: RF, IF, Baseband**
- Mixer = çarpım: cos(a)·cos(b) → toplam ve fark frekansı
- **RF, IF, baseband ne demek**; neden IF'e inilir (filtreleme, kazanç, ADC erişimi)
- Image frekansı ve image reddi; high-side / low-side injection ve spektral evrilme
- Mixer spur'ları (m·RF ± n·LO), LO sızıntısı; frekans planlamanın mantığı
- Tek / çift dönüşüm; ilk IF'in yüksek seçilmesinin nedeni
- G-60 çarpımın spektrumdaki etkisi (adım adım); G-61 image problemi; G-62 referans senaryonun frekans planı (9.4 GHz → 1.8 GHz)
- W-05 mixer frekans planı ve image gezgini

**Bölüm 7 · Almaç Mimarileri Kataloğu**
Her mimari bir `mimari-karti`: blok şema, çalışma ilkesi, artı/eksi, tipik kullanım.
1. Kristal video almaç (CVR) ve TRF
2. Süperheterodin (dar bant, taramalı; tek ve çift dönüşüm)
3. Homodyne / zero-IF / direct conversion — DC offset, I/Q imbalance, LO sızıntısı
4. IFM (instantaneous frequency measurement) — gecikme hattı diskriminatörü ilkesi
5. Analog kanallaştırılmış (filtre bankası) almaç
6. Compressive (microscan) ve akusto-optik (Bragg cell) — kısa tarih notu
7. Sayısal IF almaç (digital IF): süperhet + hızlı ADC + DDC
8. **Direct RF sampling almaç**
9. Sayısal kanallaştırılmış almaç (polyphase/FFT filtre bankası)
10. Monobit almaç (kavram düzeyi)
- Radar almacına özgü notlar: koherent almaç, STALO/COHO, eşlenik filtre, monopulse kanalları (tanım düzeyi)
- EH bağlamı: RWR / ESM / ELINT almaçlarının öncelik farkları (POI, hassasiyet, doğruluk)
- **Büyük karşılaştırma tablosu:** anlık BW, hassasiyet, dinamik aralık, eşzamanlı
  sinyal başarımı, frekans doğruluğu, POI, karmaşıklık/maliyet
- G-70…G-79 her mimarinin blok şeması (ortak sembol dili); G-7A mimarilerin tarihsel/evrimsel haritası; G-7B "analog–sayısal sınır nereye kaydı" şeridi
- W-06 mimari karşılaştırıcı

### KISIM III — Analogdan Sayısala: ADC

**Bölüm 8 · Örnekleme ve Frekans Planlama**
- Kısa hatırlatma: fs neyi ifade eder, Nyquist, aliasing, Nyquist bölgeleri,
  bandpass/undersampling, çift bölgelerde spektral evrilme (derin anlatım →
  RF Örnekleme Saha Kılavuzu)
- Bu kılavuza özgü: anti-alias filtrenin bölge seçimindeki rolü; **harmoniklerin
  (HD2, HD3) ve interleaving spur'larının nereye katlandığı**; "temiz bant" seçimi
- Referans senaryo: 1.8 GHz IF → 600 MHz alias, evrik; evrilmenin NCO işareti/IQ swap ile düzeltilmesi
- G-80 Nyquist bölgeleri ve katlanma (yelpaze/akordeon gösterimi); G-81 referans senaryonun katlanma haritası
- W-07 katlanma ve spur haritası

**Bölüm 9 · Kuantizasyon ve ADC Performans Metrikleri**
- LSB, full-scale, dBFS; kuantizasyon hatası → gürültü modeli; **SNR = 6.02N + 1.76**
- SNR, SINAD, **ENOB**, THD, **SFDR** (tek ton), çift ton IMD, **NSD (dBFS/Hz)**
- **İşlem kazancı:** 10·log10(fs/2B) — dar banda inince gürültü neden azalır
- **Aperture jitter:** SNR = −20·log10(2π·f_in·σ_j); giriş frekansı yükseldikçe
  saat kalitesi neden belirleyici; saat faz gürültüsü → jitter
- Toplam SNR = kuantizasyon + termal + jitter bileşimi
- INL/DNL → spur; time-interleaving hataları (offset → fs/M, gain/timing → fs/M ± f_in)
- Aşırı sürme / clipping, overrange bayrağı; dither; ADC'nin eşdeğer noise figure'ı
- ADC önündeki kazancın ayarı: gürültü tabanını ADC tabanının üstüne çıkarmak ↔ doyum payı
- **Datasheet okuma rehberi:** tipik bir RF ADC datasheet'inin ilk sayfası açıklamalı
- G-90 kuantizasyon merdiveni ve hata sinyali; G-91 açıklamalı ADC FFT grafiği (temel ton, HD2/HD3, en kötü spur, SFDR, gürültü tabanı, NSD, FFT işlem kazancı okları); G-92 jitter–SNR eğri ailesi; G-93 interleaving spur mekanizması
- W-08 kuantizasyon laboratuvarı; W-09 jitter–SNR hesaplayıcı

**Bölüm 10 · ADC Mimarileri ve Direct RF-Sampling ADC'ler**
- Flash, pipeline, SAR, ΣΔ, time-interleaved — hız/çözünürlük haritası, hangisi nerede
- **Direct RF-sampling ADC nedir:** geniş analog giriş bant genişliği + GSPS örnekleme
  + entegre DDC (NCO, decimation) + JESD204; RF zincirinden neyi siler, neyi silmez
- Avantaj/bedel: mixer/LO kademeleri azalır ↔ jitter hassasiyeti, güç, veri hızı, filtre gereksinimi
- **Örnek cihaz aileleri** (blok şemalarıyla): AMD Zynq UltraScale+ RFSoC RF-ADC
  (Gen1/Gen3, entegre mixer/decimation, RF Data Converter IP), TI ADC12DJ serisi
  ve ADCxxRF serisi, ADI AD92xx ailesi ve MxFE (AD908x)
- Karşılaştırma tablosu: çözünürlük, max fs, analog giriş BW, NSD, SFDR, arayüz, entegre DSP
  → değerler §10 kurallarına göre datasheet'ten doğrulanır
- Direct sampling ile klasik süperhet+IF sampling'in aynı senaryoda yan yana blok şeması
- G-100 ADC mimarileri hız–çözünürlük haritası; G-101 jenerik direct RF-sampling ADC iç blok şeması; G-102 RFSoC RF-ADC tile yapısı; G-103 süperhet vs direct sampling yan yana

**Bölüm 11 · ADC'den FPGA'ya: Arayüz ve Saat**
- Paralel/seri LVDS, **JESD204B/C**: lane, link, frame/multiframe, 8b10b vs 64b66b,
  subclass 1, SYSREF, deterministik gecikme, çok çipli senkronizasyon
- RFSoC'da durum: ADC aynı silikonda, veri AXI-Stream olarak gelir
- Veri formatı: 2's complement / offset binary, MSB hizalama, real vs I/Q çıkış modları
- Saat mimarisi: örnekleme saati, referans, PLL/jitter cleaner, FPGA fabric saati;
  fs > fabric saati → **paralel örnek yolları (SSR)**; CDC
- Veri hızı hesabı: fs × bit × kanal → Gbps; referans senaryoda sayı
- G-110 JESD204 katmanları ve SYSREF zamanlaması; G-111 saat ağacı; G-112 SSR: tek hızlı akış → N paralel faz

### KISIM IV — FPGA'da DSP'nin Zemini

**Bölüm 12 · Sabit Noktalı Aritmetik ve DSP Yapıtaşları**
- Q formatı, işaretli sayılar, ölçekleme; **bit büyümesi** (toplama +1, çarpma N+M, akümülatör log2)
- Truncation vs rounding (DC bias etkisi), saturation vs wrap-around
- Headroom ve dBFS; kademeler arası kazanç/ölçek bütçesi
- DSP slice (çarp-topla), pipeline, latency vs throughput, kaynak türleri (LUT/FF/BRAM/DSP)
- Akış arayüzü: AXI-Stream tvalid/tready/tlast; gerçek zamanlı zincirde backpressure olmaz → taşma politikası
- Paralel (SSR) işleme ve polyphase fikri: GSPS veriyi birkaç yüz MHz fabric'te işlemek
- G-120 Q formatı bit haritası; G-121 bit büyümesi boyunca zincir (referans senaryonun bit genişliği yolculuğu); G-122 wrap vs saturate dalga şekli
- W-10 sabit nokta oyun alanı (bit sayısı, yuvarlama modu → hata ve spektrum)

**Bölüm 13 · MATLAB'dan FPGA'ya: Algoritmanın Yolculuğu**
- Roller: sistem/algoritma mühendisi (MATLAB), sayısal tasarımcı (RTL), gömülü yazılımcı (PS)
- Akış: floating-point model → fixed-point model → **bit-true referans** → HDL
  (elle RTL / HDL Coder / Vitis Model Composer / HLS) → simülasyon → donanım
- Test vektörü ve golden referans kavramı; bit-exact karşılaştırma
- Donanımdan veri yakalama (ILA, snapshot buffer, DMA) → MATLAB/Python'da doğrulama döngüsü
- Parametrelerin PS'e açılması: hangi büyüklükler register olur (eşik, FTW, katsayı, mod)
- G-130 uçtan uca geliştirme akışı (flowchart); G-131 doğrulama döngüsü
- `matlab-fpga` bileşeninin ilk kullanımı: basit bir FIR'ın iki dünyadaki hali

### KISIM V — Sayısal Almaç Zinciri (DDC)

**Bölüm 14 · NCO: Sayısal Osilatör**
- Faz akümülatörü; **FTW = f_out / fs · 2^N**; frekans çözünürlüğü = fs / 2^N
- Faz → genlik: LUT (çeyrek dalga simetrisi), CORDIC; sin ve cos birlikte
- Faz kırpma (phase truncation) spur'ları, genlik kuantizasyonu, dither; NCO SFDR'ı
- Faz sürekliliği, faz ofseti, frekans atlatma; çok kanallı koherentlik
- Negatif frekans = ters dönüş; evrik spektrumu düzeltme
- G-140 faz çarkı ve akümülatör taşması; G-141 NCO iç blok şeması
- W-11 NCO laboratuvarı (FTW hesabı, faz genişliği → spur)
- Yazılımcı: `ftw = (uint64_t)llround(f_hz / fs_hz * 2^N)` — taşma, işaret, yuvarlama tuzakları

**Bölüm 15 · Sayısal Mixing ve Quadrature Demodülasyon**
- Reel ADC verisi × e^(−jω₀n) → kompleks baseband; spektrumun kaydırılması adım adım
- Toplam-frekans bileşeni ve image → arkadan gelen filtrenin görevi
- **NCO çarpımı nerede yapılır:** ADC içindeki entegre DDC'de mi, FPGA'da mı; takas tablosu
- fs/4 hilesi: çarpansız mixing (1, 0, −1, 0 dizisi)
- Alternatif: Hilbert filtresi ile analitik sinyal
- Reel giriş / kompleks çıkış: veri hızı neden "iki katına" çıkıp decimation ile geri iner
- G-150 DDC'nin dört karelik spektrum hikâyesi (ADC çıkışı → mixing sonrası → filtre sonrası → decimation sonrası); G-151 DDC blok şeması
- W-12 DDC laboratuvarı (zincirin her noktasında canlı spektrum)

**Bölüm 16 · Filtreleme ve Decimation**
- FIR temelleri: tap, katsayı, konvolüsyon, lineer faz, grup gecikmesi; IIR neden nadir
- Filtre tasarım parametreleri: passband ripple, stopband zayıflatma, geçiş bandı, tap sayısı ilişkisi
- Tasarım yöntemleri: pencereli sinc, Parks-McClellan (kavram); katsayı kuantizasyonu
- **Decimation:** neden (veri hızı, işlem kazancı, kaynak), nasıl (önce filtre sonra at),
  alias'ın geri katlanması; decimation sonrası yeni fs ve yeni Nyquist
- Verimli yapılar: halfband, **CIC** (bit büyümesi, droop, kompanzasyon FIR'ı),
  polyphase decimator, çok kademeli zincir tasarımı
- Darbe gözüyle filtre: bant genişliği ↔ rise time ↔ TOA/PW doğruluğu; filtre geçici rejimi
- Interpolation (kısa not, simetri için)
- G-160 FIR yapısı (tapped delay line); G-161 decimation'da alias katlanması; G-162 CIC yanıtı ve kompanzasyon; G-163 çok kademeli decimation zinciri (referans senaryo: 2400 → 300 MSPS)
- W-13 filtre ve decimation laboratuvarı

**Bölüm 17 · Kanallaştırma**
- Geniş bandı eşzamanlı kanallara bölme ihtiyacı (EH: bilinmeyen frekans, eşzamanlı sinyaller)
- DDC bankası → polyphase filtre bankası + FFT: aynı işin verimli hali
- Kritik/aşırı örneklemeli kanallar, kanal bindirmesi, komşu kanal sızıntısı
- **"Rabbit ear" etkisi:** darbe kenarlarının komşu kanallarda sahte tespit üretmesi; kanal hakemliği
- G-170 DDC bankasından polyphase channelizer'a; G-171 kanal yanıtları ve bindirme; G-172 rabbit ear'ın zaman–kanal görünümü

### KISIM VI — Frekans Domaini: FFT

**Bölüm 18 · FFT'nin Temelleri**
- DFT sezgisi: sinyali N adet referans sinüsle korelasyon; FFT = hızlı DFT
- Bin, bin genişliği = fs/N; **frekans çözünürlüğü ↔ gözlem süresi** (Δf ≈ 1/T)
- Reel giriş (0…fs/2 anlamlı) vs kompleks giriş (−fs/2…+fs/2), fftshift
- Genlik/güç spektrumu, dBFS ölçekleme, N ile normalizasyon
- **FFT işlem kazancı** 10·log10(N/2) ve "gürültü tabanı neden N ile iniyor" —
  FFT tabanı ≠ SNR ≠ NSD; üçünü birbirine bağlayan tek şema
- Koherent örnekleme, spektral sızıntı, scalloping kaybı, picket fence
- Zero-padding: interpolasyon sağlar, çözünürlük sağlamaz
- Ortalama alma (Welch): gürültü tabanının varyansını düşürür, seviyesini değil
- G-180 DFT'nin korelasyon yorumu; G-181 bin ızgarası ve sızıntı; G-182 FFT tabanı / SNR / NSD ilişki şeması
- W-14 FFT laboratuvarı

**Bölüm 19 · Pencereleme**
- Sızıntının kökeni: sonlu gözlem = dikdörtgen pencere ile çarpım = sinc ile konvolüsyon
- Pencere ailesi: dikdörtgen, Hann, Hamming, Blackman-Harris, Kaiser, Chebyshev, flat-top
- Karşılaştırma tablosu: ana lob genişliği, en yüksek yan lob, yan lob düşüş hızı,
  **ENBW**, coherent gain, scalloping kaybı
- Seçim rehberi: yakın iki ton ayrımı ↔ güçlünün yanında zayıf sinyal ↔ genlik doğruluğu
- Overlap işleme ve pencere kaybının telafisi
- **İki ayrı "pencere" kullanımı karıştırılmasın:** FFT öncesi veri penceresi vs FIR katsayı tasarımında pencere
- FPGA'da: katsayı ROM'u, simetriden yararlanma, tek çarpıcı
- G-190 pencere zaman/frekans çiftleri galerisi; G-191 yan lobun zayıf sinyali maskelemesi
- W-15 pencere laboratuvarı

**Bölüm 20 · FPGA'da FFT ve Darbeli Sinyalde Frekans Ölçümü**
- Mimari seçenekleri: pipelined/streaming vs burst; FFT IP'nin temel ayarları; bit büyümesi ve ölçekleme takvimi
- STFT / spektrogram; overlap; gerçek zamanlılık ve latency
- **Kısa darbe problemi:** FFT penceresi darbeden uzunsa SNR kaybı, kısaysa çözünürlük kaybı; zaman–frekans takası
- Tepe bulma, eşikleme (frekans ekseninde CFAR — Bölüm 23'e köprü), eşzamanlı sinyal ayrımı
- Frekans kestirim yöntemleri: FFT tepe + interpolasyon (parabolik/Jacobsen), anlık frekans
  (faz farkı), sıfır geçişi; doğruluk ↔ SNR ↔ darbe süresi (CRLB sezgisi)
- G-200 streaming FFT veri akışı; G-201 darbe–FFT penceresi hizalanma durumları; G-202 spektrogramda referans darbe ve LFM varyantı
- W-16 spektrogram / zaman–frekans takası

### KISIM VII — Tespit: Eşik, Gürültü Tahmini, Yanlış Alarm

**Bölüm 21 · Tespit Teorisinin Temeli**
- İki hipotez: yalnız gürültü (H0) / sinyal + gürültü (H1); dört sonuç (tespit, kaçırma, yanlış alarm, doğru ret)
- I/Q'da Gauss gürültü → zarfta **Rayleigh**, güçte üstel; sinyal varken **Rician**
- **Pfa** ve **Pd** tanımı; eşiğin iki dağılımı kesmesi; ROC eğrisi; Neyman-Pearson yaklaşımı
- Kapalı form: Pfa = exp(−T²/2σ²) → T = σ·√(−2·ln Pfa); hedef Pd için gereken SNR (Albersheim yaklaşımı)
- **Pfa'dan yanlış alarm oranına:** FAR ≈ Pfa × saniyedeki bağımsız karar sayısı;
  300 MSPS'te 1e-6'nın pratikte ne demek olduğu
- G-210 iki PDF ve eşik (Pfa/Pd alanları taralı); G-211 ROC eğri ailesi; G-212 Pd–SNR eğrileri (Pfa parametreli)
- W-17 tespit laboratuvarı

**Bölüm 22 · Zarf Çıkarımı ve Entegrasyon**
- |I + jQ|, güç I²+Q² (karekök çoğu zaman gereksiz), log-zarf (dB ekseninde eşik)
- Ucuz yaklaşımlar: alpha-max-plus-beta-min, CORDIC; hata analizi
- Video filtre / kayan ortalama: gürültü varyansını düşürme ↔ kenar yumuşaması
- Koherent vs non-koherent entegrasyon; entegrasyon kazancı
- G-220 I/Q'dan zarfa; G-221 yaklaşım yöntemlerinin hata eğrisi; G-222 video filtre uzunluğunun darbe kenarına etkisi

**Bölüm 23 · Gürültü Tahmini, Adaptif Eşik ve CFAR**
- Sabit eşik neden yetmez: kazanç/sıcaklık/bant/ortam değişimi → gürültü tabanı oynar
- Gürültü tabanı kestirimi: ortalama, medyan, minimum istatistiği, histogram;
  **darbe varken kestirimi dondurma / gating**; güncelleme zaman sabiti
- **CFAR ailesi:** CA, GO, SO, OS; referans ve guard hücreleri; test hücresi
- CA-CFAR eşik çarpanı: α = N·(Pfa^(−1/N) − 1); CFAR kaybı; N seçimi
- Arıza modları: hedef maskeleme (yoğun darbe ortamı), kenar etkisi, uzun darbe/CW'nin tabanı şişirmesi
- Zaman ekseninde CFAR vs FFT bin'leri üzerinde CFAR
- **Eşik pratikleri:** histerezis (açma/kapama çift eşik), minimum darbe genişliği koşulu,
  M-of-N doğrulama, glitch reddi, eşiğin dBFS/dBm karşılığı ve kalibrasyon
- FPGA gerçeklemesi: kayan pencere toplayıcı, gecikme hattı, OS için sıralama ağı, bölmesiz karşılaştırma (x·N > α·Σ)
- G-230 CFAR penceresi anatomisi; G-231 sabit vs adaptif eşik değişen gürültüde; G-232 CA/GO/SO/OS'un aynı sahnede davranışı; G-233 CA-CFAR donanım blok şeması
- W-18 CFAR laboratuvarı

### KISIM VIII — PDW Üretimi

**Bölüm 24 · PDW Nedir**
- Tanım: bir darbenin ölçülmüş özelliklerinin sabit formatlı sayısal kaydı; ham örnekten
  PDW'ye veri indirgeme oranı (referans senaryoda hesapla)
- Tipik alanlar: **TOA, PW, PA (genlik), RF (frekans), AOA**, MOP bayrağı/tipi,
  bant genişliği, SNR/kalite, kanal no, durum bayrakları (CW, pulse-on-pulse, kırpılmış, doymuş)
- Her alanın birimi, çözünürlüğü, dinamik aralığı → bit sayısı seçimi
- Öğretici bir PDW formatı (ör. 128 bit) — bit alan haritası + C struct + parse örneği
  (format kurgusaldır; bunu açıkça belirt)
- G-240 PDW bit alan haritası; G-241 darbeden PDW'ye indirgeme infografiği

**Bölüm 25 · Parametre Ölçümü**
- **TOA:** eşik geçişi, %50 / −3 dB / −6 dB noktası tanımları, serbest koşan zaman sayacı,
  zaman damgası çözünürlüğü ve referansı (PPS/harici zaman), genliğe bağlı TOA kayması (time walk)
- **PW:** kenar tanımına bağımlılık, SNR ve filtre bant genişliği etkisi
- **PA:** tepe vs ortalama, kenar örneklerinin dışlanması, log ölçek, kalibrasyon tablosu
- **Frekans:** darbe içi ortalama anlık frekans veya FFT tepe; NCO ofsetinin geri eklenmesi; evrik bölge düzeltmesi
- **MOP:** darbe içi faz/frekans profili → chirp eğimi, faz atlaması tespiti (kavram + basit örnek)
- **AOA:** genlik karşılaştırma, faz interferometresi, TDOA (ilke düzeyi; çok kanallı koherentliğe bağ)
- Ölçüm hatası ↔ SNR ilişkileri, tekrarlanabilirlik
- G-250 tek darbe üzerinde tüm ölçü noktaları; G-251 time walk; G-252 darbe içi anlık frekans profili (sabit vs LFM)
- W-19 PDW üreteci

**Bölüm 26 · Darbe Durum Makinesi ve PDW Veri Yolu**
- FSM: IDLE → RISING → IN_PULSE → FALLING → EMIT; zaman aşımı (uzun darbe/CW → parçalı PDW)
- Çakışan darbeler (pulse-on-pulse), çok kısa aralıklı darbeler, kenarda gürültü çentiği
- Zaman ve frekans kollarının hizalanması (latency eşitleme) ve PDW'de birleştirilmesi
- PDW FIFO, paketleme, AXI-Stream → DMA → PS; kesme vs polling; taşma politikası ve drop sayaçları
- Darbe yoğunluğu (darbe/s) ↔ PDW bant genişliği bütçesi
- Tetiklemeli ham I/Q snapshot (darbe başına yakalama) — analiz ve doğrulama için
- G-260 darbe FSM diyagramı; G-261 PDW veri yolu (PL → PS); G-262 iki kolun latency hizalaması
- Yazılımcı: PDW okuma döngüsü C iskeleti, sıra numarası ile kayıp tespiti

**Bölüm 27 · PDW'den Sonrası — Ufuk Turu**
- Deinterleaving: karışık darbe akışını emiterlere ayırma; PRI histogram yöntemleri (kavram)
- Emiter takibi ve tanımlama, kütüphane eşleme; yazılımın PDW'yi nasıl tükettiği
- Bu kılavuzun bıraktığı yer ve ileri okuma
- G-270 karışık PDW akışından emiter izlerine

### KISIM IX — Sistem Bütünü ve Pratik

**Bölüm 28 · Uçtan Uca Referans Tasarım**
- Referans darbenin tüm zincir boyunca izlenmesi: her durakta zaman + frekans görünümü
- **Sinyal pasaportu büyük tablosu:** durak × (frekans konumu, real/kompleks, fs, bit, veri hızı, sinyal seviyesi, gürültü seviyesi, SNR)
- Seviye/SNR bütçesi, bit genişliği bütçesi, latency bütçesi, kaynak bütçesi (kaba)
- Tasarım kararlarının geri izlenmesi: "fs neden 2400, decimation neden 8, FFT neden 1024?"
- G-280 poster şemanın tam açıklamalı, sayılarla dolu hali
- **W-20 uçtan uca zincir oyun alanı (capstone)**

**Bölüm 29 · Doğrulama ve Hata Ayıklama**
- Test sinyalleri: CW ton, çift ton, darbe katarı, gürültü; sayısal loopback / dahili test üreteci
- Ölçüm teknikleri: ILA/snapshot ile yakalama, MATLAB/Python'da FFT, bit-true karşılaştırma
- **Belirti → neden → kontrol tablosu** (en az 15 satır), ör.: spektrum aynalı (I/Q swap / evrik bölge),
  DC'de çivi (offset / LO sızıntısı), fs/2 − f_in'de spur (interleaving), gürültü tabanı beklenenden
  yüksek (saat jitter'ı / kazanç planı), false alarm patlaması (gürültü kestirimi donmuş / eşik birimi
  yanlış), PW kısa ölçülüyor (histerezis / filtre BW), PA dalgalı (scalloping / kanal kenarı),
  TOA genliğe göre kayıyor (time walk), PDW kaybı (FIFO taşması), periyodik spur (NCO faz kırpma),
  harmonik görünüyor (clipping / ADC sürücü doyumu)
- G-290 hata ayıklama karar ağacı (flowchart)

**Bölüm 30 · Gömülü Yazılımcının Kontrol Yüzeyi**
- Tipik register haritası (kurgusal): NCO FTW, decimation/mod seçimi, filtre katsayı yükleme,
  pencere seçimi, CFAR parametreleri (N, guard, α), sabit eşik, histerezis, min PW, PDW FIFO
  durum/sayaç, snapshot tetikleme, ADC overrange sayaçları
- Birim dönüşümleri kütüphanesi: Hz ↔ FTW, dBFS ↔ lineer register, dBm ↔ dBFS (kalibrasyon sabiti),
  örnek ↔ ns, bin ↔ Hz
- Kalibrasyon: genlik/frekans düzeltme tabloları, sıcaklık, kanal eşleme
- Açılış sırası: saat → ADC/JESD link → kalibrasyon → DDC → tespit → PDW akışı
- C örnekleri seri kodlama stiline uygun; RTOS/bare-metal bağımsız
- G-300 PS–PL kontrol/veri yüzeyi şeması; G-301 açılış sırası flowchart'ı

### EKLER

- **Ek A · Sözlük:** TR–EN terimler ve kısaltmalar (ADC, AGC, AOA, CFAR, CIC, DDC, ENOB,
  FTW, IF, IFM, JESD, LFM, LO, MDS, MOP, NCO, NF, NSD, PA, PDW, Pd, Pfa, POI, PRI, PW, SFDR,
  SINAD, SNR, SSR, TOA, …); metindeki ilk kullanım sözlüğe bağlanır, üzerine gelince tanım baloncuğu
- **Ek B · Formül Kartı:** tüm kilit formüller tek sayfada, bölüm bağlantılı
- **Ek C · dB ve Hızlı Hesap Tabloları**
- **Ek D · Pencere Fonksiyonları Tablosu**
- **Ek E · Kaynakça ve İleri Okuma** (bkz. §10.3)
- **Ek F · Görsel ve Widget Dizini**

---

## 7. İnteraktif Widget Kataloğu

### 7.1 Ortak Kurallar

- **Saf vanilla JS + inline SVG/Canvas.** Harici kütüphane, CDN, framework yok.
- Tüm widget'lar tek bir ortak çekirdeği kullanır: **`dsp-core.js`** (§7.2).
  Hesap mantığı widget koduna gömülmez; çekirdek ayrıca test edilir.
- Standart kap: başlık · kontrol paneli (kaydırıcı + sayısal giriş birlikte, birimli) ·
  çizim alanı · **preset butonları** ("Referans senaryo", "Kötü durum", …) · sıfırla ·
  "Ne gözlemlemeliyim?" kutusu (2–4 yönlendirilmiş deney ve beklenen gözlem).
- **Deterministik:** tohumlu PRNG; aynı ayar aynı görüntüyü verir ("yeni gürültü" butonu ayrı).
- Tema-duyarlı (renkler CSS değişkeninden okunur, tema değişince yeniden çizilir).
- Performans: N ≤ 8192, `requestAnimationFrame`, girişte debounce; görünür değilken
  hesap yapma (IntersectionObserver). Tüm widget'lar aynı anda sayfadayken kaydırma akıcı kalmalı.
- Eksenler etiketli ve birimli; dB eksenlerinde referans (dBFS/dBm) yazılı.
- Klavye ile kullanılabilir; her kontrolün `label`'ı var; dokunmatik ekranda çalışır.
- JS kapalıysa / yazdırmada: referans senaryo preset'inin statik SVG anlık görüntüsü görünür.
- Her widget hesapladığı kilit sayıları metin olarak da gösterir (yalnızca grafik değil).

### 7.2 `dsp-core.js` — Ortak DSP Çekirdeği

Asgari API: tohumlu PRNG + Gauss gürültü (Box-Muller) · radix-2 kompleks FFT/IFFT ·
pencere üreteçleri (rect, Hann, Hamming, Blackman-Harris, Kaiser, Chebyshev, flat-top) +
ENBW/coherent gain/scalloping hesapları · sinyal üreteçleri (ton, çift ton, darbe
katarı, LFM darbe, faz kodlu darbe) · kuantizör (N-bit, clipping, dither) · jitter'lı
örnekleme modeli · NCO (faz akümülatörü, faz kırpma, LUT kuantizasyonu) · kompleks mixer ·
FIR tasarımı (pencereli sinc, halfband) + filtreleme + frekans yanıtı · CIC · decimator ·
zarf/güç, alpha-max-beta-min · kayan ortalama · CFAR (CA/GO/SO/OS) · histerezisli darbe
FSM'i + TOA/PW/PA/frekans ölçümü → PDW nesnesi · yardımcılar (dB dönüşümleri, Friis
kaskadı, Nyquist katlama, FTW hesabı, Rayleigh/Rician Pfa–Pd).

Çekirdek için **birim testleri** yazılır (§10.4 bilinen-cevap kontrolleri dahil).

### 7.3 Widget Listesi

| No | Ad | Bölüm | Kontroller → Gözlem |
|---|---|---|---|
| W-01 | dB dönüştürücü | 1 | dBm ↔ mW ↔ Vrms/Vpp (50 Ω) ↔ dBFS (tam ölçek girilerek); oran ↔ dB |
| W-02 | Fazör laboratuvarı | 2 | frekans (±), faz, I/Q gain/phase hatası → dönen vektör, I(t)/Q(t), spektrumda image; I/Q swap butonu |
| W-03 | Darbe katarı ↔ spektrum | 3 | PW, PRI, rise time, MOP tipi (yok/LFM/Barker) → zaman dalga şekli + spektrum (sinc zarfı, çizgi aralığı) |
| W-04 | Kaskad NF / hassasiyet | 4–5 | blok ekle/çıkar/sırala (kazanç, NF), bant genişliği, gereken SNR → toplam NF, gürültü tabanı, MDS; "LNA'yı sona al" deneyi; seviye diyagramı canlı |
| W-05 | Mixer frekans planı | 6 | RF, LO, high/low-side, IF filtre bandı → IF, image, evrilme, düşük mertebe spur'lar frekans ekseninde |
| W-06 | Mimari karşılaştırıcı | 7 | iki mimari seç → blok şemalar yan yana + özellik çubukları; "senaryoya göre öner" (öncelik: BW / hassasiyet / eşzamanlı sinyal / maliyet) |
| W-07 | Katlanma ve spur haritası | 8 | fs, f_in, sinyal BW → Nyquist bölgesi, alias konumu, evrilme, HD2/HD3 ve interleaving spur'larının katlandığı yerler; "temiz bant" göstergesi |
| W-08 | Kuantizasyon laboratuvarı | 9 | bit sayısı, giriş seviyesi (dBFS), dither, clipping → zaman dalga şekli, hata sinyali, FFT; ölçülen SNR/SFDR/ENOB vs teorik |
| W-09 | Jitter–SNR hesaplayıcı | 9 | f_in, σ_jitter, bit sayısı, termal SNR → bileşen bileşen toplam SNR, baskın terim vurgusu, eğri üzerinde çalışma noktası |
| W-10 | Sabit nokta oyun alanı | 12 | Q formatı, yuvarlama modu, taşma modu → dalga şekli, hata, spektrum; wrap felaketi demosu |
| W-11 | NCO laboratuvarı | 14 | fs, hedef frekans, akümülatör genişliği, LUT adres/genlik biti, dither → FTW (hex), gerçek frekans ve hata, çıkış spektrumu, spur seviyeleri |
| W-12 | DDC laboratuvarı | 15 | giriş tonu/darbesi, NCO frekansı, filtre BW, decimation → zincirin 4 noktasında spektrum (sekmeli veya alt alta); yanlış NCO işaretiyle evrik sonuç |
| W-13 | Filtre ve decimation lab. | 16 | tip (FIR/halfband/CIC+komp.), tap sayısı, kesim, katsayı biti, decimation oranı → frekans yanıtı, grup gecikmesi, katlanan alias bölgeleri taralı; darbe yanıtı (rise time) |
| W-14 | FFT laboratuvarı | 18 | N, ton frekansı (bin ortası/arası), ikinci ton, gürültü seviyesi, zero-padding, ortalama sayısı → spektrum; FFT tabanı vs gerçek SNR göstergesi; "N'i 4 katla, taban 6 dB insin" deneyi |
| W-15 | Pencere laboratuvarı | 19 | pencere tipi (+Kaiser β), iki ton (frekans farkı, seviye farkı) → zaman şekli, frekans yanıtı, ENBW/yan lob/scalloping sayıları; zayıf tonun maskelenmesi |
| W-16 | Spektrogram / zaman–frekans | 20 | FFT boyu, overlap, pencere, darbe tipi (sabit/LFM), PW → spektrogram; darbe–pencere hizalama etkisi |
| W-17 | Tespit laboratuvarı | 21 | SNR, eşik (veya hedef Pfa) → H0/H1 PDF'leri, taralı Pfa/Pd, ROC üzerinde nokta; saniyedeki yanlış alarm sayısı (örnek hızı girilerek); Monte Carlo sayacı ile teori karşılaştırması |
| W-18 | CFAR laboratuvarı | 23 | CFAR tipi, N, guard, hedef Pfa, gürültü tabanı profili (sabit/basamak/rampa), darbe yoğunluğu → zaman serisi + adaptif eşik eğrisi, tespit/yanlış alarm/kaçırma sayaçları; sabit eşikle yan yana; maskeleme demosu |
| W-19 | PDW üreteci | 25–26 | SNR, PW, PRI, MOP, eşik, histerezis, min PW, video filtre → zarf + FSM durumu renkli bant + canlı PDW tablosu (TOA, PW, PA, frekans, bayraklar); gerçek değerle hata sütunu; SNR düştükçe hata büyümesi |
| W-20 | **Uçtan uca zincir oyun alanı** | 28 | Senaryo paneli (RF, PW, PRI, seviye, ikinci emiter), ön uç (NF, kazanç), ADC (fs, bit, jitter), DDC (NCO, decimation), tespit (CFAR), FFT (N, pencere) → poster şema üzerinde her durakta mini zaman/frekans görünümü + canlı sinyal pasaportu + PDW çıktısı. W-01…W-19'un çekirdeklerini birleştirir; "bir parametreyi değiştir, etkisinin zincir boyunca yayılmasını izle" |

Widget sayısı bağlayıcı değil, kalite bağlayıcı: bir widget kavramı
netleştirmiyorsa sadeleştir veya komşusuyla birleştir; kapanış raporunda bildir.

---

## 8. Görsel Kuralları

### 8.1 Statik SVG

- Hepsi elle yazılmış inline SVG; renkler **yalnızca CSS değişkenleri** (sabit hex yok)
  → iki temada da doğru görünür. §5.3 renk dili zorunlu.
- Ortak **sembol kütüphanesi** (`<symbol>` + `<use>`): anten, LNA/yükselteç üçgeni, mixer (⊗),
  filtre (BPF/LPF), LO/osilatör, zayıflatıcı, ADC, NCO, FIR, decimator (↓M), FFT, karşılaştırıcı,
  FIFO, register bloğu, DMA. Tüm blok şemalar bu kütüphaneden kurulur.
- Her görselin `<title>`/`<desc>`'i ve altında numaralı, açıklayıcı bir alt yazısı var.
- Spektrum çizimleri gerçek orantıya sadık (eksen değerleri referans senaryo ile tutarlı);
  mümkünse çizim verisi build sırasında `dsp-core` eşdeğeri bir Python hesabından üretilir, elle uydurulmaz.
- Karmaşık şemalar kademeli açılır: önce sade hali, sonra detay katmanı (buton veya ardışık iki görsel).
- Mobilde yatay taşma yok: geniş şemalar `viewBox` ile ölçeklenir, çok genişler yatay kaydırılabilir kapta.
- Asgari görsel yoğunluğu: bölüm başına ≥ 3 statik görsel (kısa ufuk turu bölümleri hariç).

### 8.2 Mermaid / Flowchart

- **Runtime mermaid.js yok** (offline + tek dosya + tema tutarlılığı).
- Flowchart ve FSM'ler varsayılan olarak elle SVG. İstersen taslağı Mermaid ile yazıp
  build sırasında (araç yerelde mevcutsa) SVG'ye çevir ve renkleri CSS değişkenlerine
  dönüştüren bir son-işlemden geçir; araç yoksa build kırılmamalı (SVG'ler repoda commit'li durur).

### 8.3 Formüller

- Önce referans repoda formüllerin nasıl çözüldüğüne bak ve aynı yöntemi kullan.
- Orada yerleşik bir çözüm yoksa: build-time render edilmiş, fontları gömülü, offline
  çalışan bir çözüm seç (ör. vendored KaTeX çıktısı + base64 woff2, ya da MathML Core +
  okunaklı fallback). Kararı ve gerekçesini `PLAN.md`'ye yaz.
- Her formül `formul-karti` içinde: sembol tablosu, birimler, sayısal örnek.

---

## 9. Repo Yapısı ve Build

```
almac-saha-kilavuzu/
├── KICKOFF.md                  # bu dosya
├── CLAUDE.md                   # kısa çalışma kuralları, KICKOFF'a referans
├── PLAN.md                     # Faz 0 çıktısı: keşif notları, kararlar, bölüm takibi
├── src/
│   ├── template.html           # iskelet: head, TOC, tema, ilerleme çubuğu
│   ├── styles/                 # tokens.css, components.css, print.css
│   ├── chapters/               # 00-buyuk-resim.html … 30-kontrol-yuzeyi.html, ekler
│   ├── svg/                    # symbols.svg + bölüm görselleri (G-xx adlarıyla)
│   ├── js/
│   │   ├── dsp-core.js
│   │   ├── widget-kit.js       # ortak kap, kontrol, çizim yardımcıları
│   │   ├── widgets/            # w01-db.js … w20-zincir.js
│   │   └── site.js             # TOC, tema, sözlük baloncuğu, rota filtresi
│   └── data/                   # glossary.json, formulas.json, scenario.json
├── tools/
│   ├── build.py                # yalnızca Python stdlib → dist/index.html
│   ├── check.py                # kalite kapıları (§12.2)
│   └── gen_figures.py          # spektrum/eğri verilerini hesaplayıp SVG path üretir
├── tests/                      # dsp-core birim testleri + bilinen-cevap kontrolleri
└── dist/index.html             # TEK dosya, tüm CSS/JS/SVG/font inline
```

- Build hattı yalnızca Python stdlib kullanır (seri standardı). `python3 tools/build.py`
  tek komutla `dist/index.html` üretir.
- `scenario.json` referans senaryonun tek doğruluk kaynağıdır; bölüm metinlerindeki sayılar,
  preset'ler ve üretilen şekiller buradan beslenir (sayı bir yerde değişirse her yerde değişsin).
- `dist/index.html` çift tıklamayla `file://` üzerinden, internetsiz, air-gapped bir
  makinede eksiksiz çalışmalı. Hiçbir dış URL isteği olmamalı.
- Boyut hedefi: tek dosya makul kalsın (hedef < 8 MB); aşarsa nedenini raporla.

---

## 10. Doğruluk, Kaynak ve Gizlilik Kuralları

### 10.1 Gizlilik ve Kapsam Disiplini

- İçerik **yalnızca açık literatür** düzeyindedir: ders kitapları, üretici datasheet'leri
  ve uygulama notları, açık akademik yayınlar.
- Gerçek bir sistemin, platformun veya tehdidin parametresi, şirket içi tasarım bilgisi,
  proje adı **yer almaz.** Tüm sayısal örnekler kurgusal/öğreticidir ve dokümanda böyle etiketlenir.
- PDW formatı ve register haritası açıkça "kurgusal, öğretici" olarak işaretlenir.

### 10.2 Teknik Doğruluk

- Her formül birim ve tanım kümesiyle verilir; farklı kaynaklardaki tanım farkları
  (ör. PW'nin −3 dB / −6 dB / %50 tanımı, SFDR'ın dBc / dBFS hali, tek/çift taraflı bant
  genişliği) açıkça belirtilir.
- Cihazlara ait değerler (çözünürlük, fs, giriş BW, NSD, SFDR) üretici datasheet'inden
  doğrulanır (internet erişimi varsa). Doğrulanamayan değer tabloya **"yaklaşık / doğrulanmadı"**
  işaretiyle girer ve kapanış raporunda listelenir. Değer uydurma.
- Emin olmadığın bir iddiayı kesin dille yazma; ya doğrula ya yumuşat ya çıkar.
- Widget sonuçları ile metindeki formüller ve statik şekiller **aynı sayıyı** vermeli.

### 10.3 Kaynakça Omurgası (Ek E)

Tsui — *Digital Techniques for Wideband Receivers* · Tsui — *Microwave Receivers with EW
Applications* · Richards — *Fundamentals of Radar Signal Processing* · Skolnik — *Introduction
to Radar Systems* · Wiley — *ELINT: The Interception and Analysis of Radar Signals* · Pace —
*Detecting and Classifying LPI Radar* · Lyons — *Understanding Digital Signal Processing* ·
harris — *Multirate Signal Processing for Communication Systems* · Kester (ed.) — ADI *Data
Conversion Handbook* ve MT-serisi tutorial'lar · harris — "On the Use of Windows for Harmonic
Analysis with the DFT" · AMD RF Data Converter ürün kılavuzu · JEDEC JESD204B/C özetleri ·
ilgili TI/ADI RF-sampling uygulama notları. Künyeleri doğrula; bölüm sonlarında "ileri okuma"
olarak ilgili kaynağa işaret et. Kaynaklardan uzun alıntı yapma; kendi anlatımınla yaz.

### 10.4 Bilinen-Cevap Kontrolleri (test olarak yazılır)

| Kontrol | Beklenen |
|---|---|
| kTB, T = 290 K, 1 Hz | −174.0 dBm/Hz |
| Gürültü tabanı: B = 300 MHz, NF = 6 dB | ≈ −83.2 dBm |
| İdeal SNR, 14 bit | 86.04 dB |
| Jitter SNR: f = 1 GHz, σ = 100 fs | ≈ 64.0 dB |
| Alias: fs = 2400, f = 1800 MHz | 600 MHz, evrik |
| FTW: f = 600 MHz, fs = 2400 MHz, N = 32 | 0x40000000 |
| NCO çözünürlüğü: fs = 2400 MHz, N = 32 | ≈ 0.559 Hz |
| İşlem kazancı: 1200 → 300 MHz | 6.02 dB |
| FFT bin: fs = 300 MSPS, N = 1024 | ≈ 293 kHz |
| Hann ENBW | 1.50 bin |
| Rayleigh eşik, Pfa = 1e-6 | 5.26 σ |
| CA-CFAR α: N = 16, Pfa = 1e-6 | ≈ 21.9 |
| Friis: LNA (G = 20 dB, NF = 2 dB) + mixer (NF = 10 dB) | ≈ 2.2 dB toplam |
| Monte Carlo Pfa (W-17/W-18 çekirdeği; hedef Pfa = 1e-3, ≥ 1e7 örnek) | teorik değerin ±%5'i içinde |

---

## 11. Çalışma Fazları

Tüm üretim **tek oturumda**, kesintisiz yürütülür. Kullanıcıya yalnızca (a) çözülemeyen
ortam sorunu veya (b) veri kaybı riski taşıyan karar için dönülür. Diğer tüm kararları
kendin ver, `PLAN.md`'ye gerekçesiyle yaz.

**Faz 0 — Keşif ve Plan**
1. Referans repoyu (ve erişilebilen diğer seri repolarını) incele: token'lar, bileşen
   sınıfları, TOC/tema mekaniği, build hattı, formül çözümü, RF örnekleme içeriğinin kapsamı.
2. `PLAN.md` yaz: devralınanlar, yeni bileşenler, formül kararı, bölüm takip tablosu,
   RF Örnekleme kılavuzuyla örtüşme haritası.

**Faz 1 — İskelet ve Dikey Dilim**
1. Repo iskeleti, tasarım sistemi, sembol kütüphanesi, `widget-kit`, `dsp-core` + testler, build + check.
2. **Dikey dilim:** Bölüm 0 (poster şema dahil) + Bölüm 14 (NCO) tam kalite üretilir —
   şablonun her maddesi, ≥ 3 görsel, W-11, iki temada kontrol. Bu dilim sonraki tüm bölümlerin
   kalite referansıdır; zayıf kaldıysa ilerlemeden önce düzelt.

**Faz 2 — İçerik Üretimi (Kısım sırasıyla)**
Kısım I → IX. Her Kısım bitince: build + check + bölümler arası tutarlılık (terim, sembol,
sayı, köprü paragrafları) + `PLAN.md` güncelle + commit.

**Faz 3 — Capstone ve Ekler**
W-20 zincir oyun alanı, Bölüm 28 pasaport tablosu, sözlük baloncukları, formül kartı, dizinler.

**Faz 4 — Kalite Turu**
Baştan sona okur gözüyle geçiş: bağımlılık ihlali (anlatılmadan kullanılan kavram) avı,
tuzak/özet/kendini-sına eksikleri, iki temada tüm görseller, mobil genişlik, yazdırma,
offline test, performans, bilinen-cevap testleri, §12 kabul kriterleri. Ardından kapanış raporu.

---

## 12. Kabul Kriterleri

### 12.1 İçerik

- [ ] §6'daki tüm bölümler şablona uygun ve dolu; hiçbir bölüm "madde listesi" düzeyinde bırakılmamış
- [ ] Hiçbir kavram tanıtılmadan kullanılmıyor; her bölümde ön koşul / açtığı bölümler satırı var
- [ ] Referans senaryo baştan sona tutarlı; sinyal pasaportu her durakta mevcut
- [ ] Her bölümde ≥ 1 tuzak, özet kartı, kendini sına; uygun bölümlerde `uc-goz`
- [ ] Almaç mimarilerinin her biri blok şemalı; karşılaştırma tablosu tam
- [ ] Direct RF-sampling ADC örnekleri blok şemalı ve doğrulanmış/işaretlenmiş değerli
- [ ] Sözlük tüm kısaltmaları kapsıyor; ilk kullanımlar bağlı
- [ ] §10.1 gizlilik kurallarına tam uyum

### 12.2 Teknik (`tools/check.py` otomatik denetler)

- [ ] `dist/index.html` tek dosya; dış URL / ağ isteği **sıfır**
- [ ] Tüm `id`'ler benzersiz; tüm iç bağlantılar çözülüyor; TOC eksiksiz
- [ ] SVG'lerde sabit renk yok (yalnızca CSS değişkeni); her SVG'de `<title>`
- [ ] Her G-xx ve W-xx §6/§7 ile eşleşiyor; eksik/fazla raporlanıyor
- [ ] `dsp-core` testleri ve §10.4 kontrolleri geçiyor
- [ ] Konsolda hata yok; iki temada ve ~380 px genişlikte kırılma yok
- [ ] Yazdırma görünümünde widget'lar statik görüntüye düşüyor

### 12.3 Kapanış Raporu (tek mesaj)

Üretilen bölüm/görsel/widget sayıları · dosya boyutu · verilen önemli kararlar ·
KICKOFF'tan sapmalar ve gerekçeleri · eklenen "sayılmamış ama önemli" konular ·
doğrulanamayan cihaz değerleri listesi · bilinen eksikler ve önerilen v2 işleri.

---

## 13. Başlatma Promptu

Aşağıdaki metin, repo klasöründe Claude Code'a verilecek ilk mesajdır:

```
Bu klasörde KICKOFF.md var; projenin tek başlangıç talimatı o. Baştan sona oku.
Ardından referans repoyu incele:
/Users/mpcukur/Projects/claude/rf-sampling-saha-kilavuzu (çıktı: dist/index.html)
Tasarım sistemini, bileşenleri ve build yaklaşımını oradan devral.

KICKOFF §11'deki fazları sırayla, tek oturumda yürüt: önce PLAN.md, sonra iskelet
ve dikey dilim (Bölüm 0 + Bölüm 14), ardından Kısım Kısım tüm içerik, capstone
widget, kalite turu. Her Kısım sonunda build + check çalıştır ve commit at.

Bana yalnızca çözemediğin bir ortam sorunu veya veri kaybı riski olan bir karar
için dön; diğer tüm kararları kendin ver ve PLAN.md'ye gerekçesiyle yaz.
Kalite çıtası: serinin en iyi üyesi. Acele etme; bir bölüm şablonu tam
karşılamıyorsa sonrakine geçme. En sonda KICKOFF §12.3 formatında tek bir
kapanış raporu ver.
```
