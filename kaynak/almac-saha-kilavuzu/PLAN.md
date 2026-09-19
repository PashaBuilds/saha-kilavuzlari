# PLAN.md — almac-saha-kilavuzu

> Faz 0 çıktısı. KICKOFF.md tek talimat kaynağıdır; bu dosya keşif notlarını,
> verilen kararları (gerekçeleriyle) ve bölüm takibini tutar. KICKOFF'un
> geçersiz kılınan yerleri: §1 Mac referans-repo yolu, §9 bağımsız repo yapısı,
> §13 başlatma promptu → yerine bu repodaki (saha-kilavuzlari) seri konvansiyonu.

## 0. Ortam

- Windows 10, Python 3.14 (`python` / `py`), Node 24 (yalnızca dsp-core
  testlerini koşturmak için, build'e bağımlılık değil). Tüm dosya G/Ç
  `encoding="utf-8"`, yol birleştirme `pathlib`.
- Repo kökü `D:\Projects\saha-kilavuzlari`, `core.autocrlf=true`; depoda LF,
  çalışma kopyasında CRLF. Gürültülü diff olmasın diye `.gitattributes`
  (`* text=auto`) eklendi.

## 1. Seri keşfi — beş belgenin güçlü/zayıf yanları

| Belge | En güçlü 3 | En zayıf 3 |
|---|---|---|
| **RF Örnekleme** (Node, 2,1 MB) | (1) Her bölüm "ne öğreneceksin" ile açılıp gerçek sayısal hesapla kapanıyor (lane rate, NSD, jitter bütçesi). (2) clk=amber / SYSREF=camgöbeği renk kodu CSS token'dan wavedrom'a kadar tutarlı. (3) Saha vakaları, semptom→sebep tablosu, karar ağacı; belirsizlik `[DOĞRULA:]` ile dürüstçe işaretli. | (1) Sıfır etkileşim: hesap makinesi/quiz yok. (2) Görsel dağılımı dengesiz: ADC metrikleri ve faz gürültüsü bölümlerinde hiç şekil yok. (3) Formüller `text` kod bloğu; kesir/kök kod gibi görünüyor, spektral evrilme tek paragrafta. |
| **Ethernet** (Python, 302 KB) | (1) Build kalite kapıları: eksik SVG / `<title>` yok / sabit hex → derleme durur. (2) Bölümler arası geri-ileri referans zinciri ve 17/17 özet tutarlılığı. (3) Şemalar için ayrı `--dia-*` zemin token'ları; çift temada şema kontrastı gerçekten çalışıyor. | (1) Hiç widget yok. (2) Ok marker'ları her SVG'de kopyalı, `<symbol>/<use>` yok. (3) Öz-test yok, pekiştirme yalnızca özet kutusu. |
| **Lokal LLM** (Python, 255 KB) | (1) `:::hesap` kutusu + 3 canlı hesaplayıcı: "hesaplayarak öğretme". (2) SVG stili tamamen CSS sınıflarına taşınmış; paylaşılan marker defs. (3) `gallery.py` ile çift temalı şema QA sayfaları. | (1) Yerleşim ölçüleri token değil, sabit. (2) Build doğrulaması gevşek (eksik SVG yalnızca uyarı, hex denetimi yok). (3) Print stili yok; analoji kutusu az ve dengesiz. |
| **Vivado-PS** (Python, 5,2 MB) | (1) Her iddia gerçek Tcl dökümüne dayanıyor. (2) "Yazılıma yansıması" kutusu: ayarı okurun dünyasına çeviren köprü. (3) BD pan/zoom görüntüleyici + lightbox + kalıcı checkbox'lar. | (1) Öz-değerlendirme yok; `:::deneme` cevabı hemen altında. (2) `ekran-*.svg` sabit renkli; açık temada uyum bozuluyor. (3) Sözlük düz `dl`, metin içi terimlere tooltip/bağ yok. |
| **Oryantasyon** (Python, 567 KB) | (1) Görev kartı + ipucu merdiveni + gerçek lab kodu: ölçülebilir öğrenme döngüsü. (2) SVG disiplini kusursuz (sabit 740 viewBox, ortak sınıflar, zorunlu `<title>`). (3) Kalıcı ilerleme panosu, reduced-motion güvenli hareket katmanı. | (1) Bölüm sonu özeti yok. (2) İçerik genişliği ayrı sınırlandırılmamış, geniş ekranda satır uzunluğu kontrolsüz. (3) Print CSS'te `details{open:true}` geçersiz; basılıda çözümler kaybolur. |

**Seride hiç olmayanlar (bu kılavuzun üstüne çıkacağı yerler):** gerçek
parametrik widget'lar, "kendini sına" açılır cevaplı sorular, sözlük
baloncuğu, formül kartı, okuma rotası filtresi, `<symbol>/<use>` sembol
kütüphanesi, senaryo tek-doğruluk-kaynağı, birim testleri, otomatik
bağımlılık/bağlantı denetimi.

## 2. İskelet referansı ve devralınanlar

**İskelet referansı: Ethernet derleyicisi** (`kaynak/ethernet-saha-kilavuzu/build/build.py`)
— en sıkı token disiplini + kalite kapıları; üstüne Vivado-PS'ten
(`:::` direktif attr'ları, kalıcı checkbox, lightbox fikri) ve Lokal-LLM'den
(paylaşılan SVG defs, `wide` figür, gallery QA) alınanlar eklenir.

Devralınan token seti (KICKOFF §5.1 ile birebir aynı palet): `--bg #0E1116`,
`--bg-2 #161B22`, `--accent #4DA3FF`, `--gold #E8B84B`, `--green #5BB0A6`,
`--red #F0716B`; açık tema Ethernet değerleri. Aynı font stack (sistem sans +
ui-monospace), 17px/1.7, `--toc-w 292px`, `--icerik-w 760px`, `--sema-w 900px`
(≥1240 px'te şema sütundan taşar). Tema düğmesi, FOUC önleyici head script,
ilerleme çubuğu, iki seviyeli scroll-spy TOC, mobil `<details>` TOC, kopyala
düğmesi, `@media print`.

md sözdizimi seri ile aynı çekirdek: `# Bölüm N — Ad`, `##`/`###`,
`:::saha-notu|tuzak|analoji|derin-dalis|ozet`, `` ``` `` kod → `komut`,
`{{svg:dosya.svg|altyazı}}`, tablolar, listeler, alıntı.

## 3. Klasör düzeni (KICKOFF §9'un seri konvansiyonuna uyarlanmış hali)

```
kaynak/almac-saha-kilavuzu/
├── KICKOFF.md  CLAUDE.md  PLAN.md
├── content/            00-buyuk-resim.md … 30-kontrol-yuzeyi.md, 31-ek-a … 36-ek-f
├── assets/
│   ├── css/kilavuz.css         token'lar + bileşenler + widget + print
│   ├── svg/symbols.svg         ortak sembol kütüphanesi (<symbol>), belgeye bir kez gömülür
│   ├── svg/g-XX-*.svg          statik görseller (G-xx adlarıyla)
│   └── js/  dsp-core.js  widget-kit.js  site.js  widgets/wNN-*.js
├── data/   scenario.json  glossary.json
├── build/  build.py  check.py  gen_figures.py  gallery.py
├── tests/  dsp-core.test.js (node --test)  test_bilinen_cevap.py (stdlib unittest)
└── dist/index.html     (gitignore'da; guncelle.py rafa taşır)
```

- `build.py` yalnızca stdlib; `python build/build.py` → `dist/index.html`.
- `gen_figures.py` (stdlib `math`/`cmath`) spektrum/eğri verilerini hesaplayıp
  `assets/svg/g-*.svg` içindeki `<!--GEN:ad-->…<!--/GEN-->` bloklarına path
  yazar; sayılar `scenario.json`'dan gelir. Üretilmiş SVG'ler repoda commit'li
  durur (build gen çağırmaz; gen ayrı adım) → build her makinede deterministik.
- `check.py`: §12.2 kapıları (tek dosya, dış URL sıfır, benzersiz id, iç
  bağlantı çözümü, SVG sabit renk/`<title>`, G-xx/W-xx eşleşmesi, konsol
  hatası yerine JS sözdizimi denetimi için `node --check` varsa), ayrıca
  `tests/` koşar (node yoksa uyarı, build kırılmaz).

## 4. Kararlar (gerekçeli)

| # | Karar | Gerekçe |
|---|---|---|
| K1 | **Formüller: build-time HTML** (`formul-karti` içinde `<span class="f">` + `<sup>/<sub>` + CSS kesir `.kesir`), KaTeX/MathML yok | Seride yerleşik çözüm yok (RF: text kod bloğu). Font gömmek boyutu şişirir; MathML Core tarayıcı desteği değişken. HTML+CSS kesir/kök offline, fontsuz, iki temada ve baskıda sorunsuz; metin aranabilir. Basit bir mini-dil: `x^2`, `x_j`, `{a}/{b}` kesir, `sqrt{…}`. |
| K2 | **Widget'lar inline SVG'ye çizer** (Canvas değil) | Tema değişiminde CSS değişkenleri otomatik uygulanır; baskıda son çizilen kare statik SVG olarak kalır (§7.1 "statik snapshot" gereği JS'siz ek üretim gerektirmez); eksen metni seçilebilir. Ağır spektrogram (W-16) için tek istisna: Canvas + tema-uyumlu renk okuma. |
| K3 | **scenario.json → üç kanala** | (a) build `{{s:anahtar}}` yer tutucularını metne yazar, (b) `window.SENARYO` olarak dist'e gömülür (preset'ler), (c) gen_figures.py okur. Sayı bir yerde değişirse her yerde değişir. |
| K4 | **Testler**: dsp-core için `node --test`; Python tarafı için `unittest` (gen_figures'taki formüller + §10.4 bilinen-cevaplar) | Seri standardı "build stdlib" → build Node'a bağımlı değil; ama JS çekirdeğini JS'te test etmek dürüst yol. Node yoksa check.py uyarır, geçer. |
| K5 | **Sözlük baloncuğu JS'siz**: build, her bölümde terimin ilk geçişini `<a class="terim" data-tanim>` ile sarar; CSS `::after` baloncuk, odaklanınca da açılır | Erişilebilir, baskıda bağlantı olarak kalır, JS kapalıyken çalışır. |
| K6 | **Okuma rotaları**: bölüm meta'sındaki `rota=` etiketleri TOC `<li data-rota>` olur; site.js üç düğmeyle filtreler, seçim localStorage'da | KICKOFF §4.3. |
| K7 | **`zincirdeki-yerim`** mini şeması build tarafından üretilir (14 duraklık yatay zincir, `blok=` meta ile aktif durak vurgulu, her durak ilgili bölüme bağlı) | Elle 30 kopya SVG yerine tek üretici → sembol dili garantili tutarlı. |
| K8 | **Kart**: `slug: almac`, `renk: 340` (kayıt dosyasının "boşta" dediği gül tonu), `motif: "analog"` | Yeni motif index.html'e SVG path eklemeyi gerektirir; index.html dokunulmaz → mevcut en uygun motif (sinüs + spektrum çubukları) seçildi. |
| K9 | **Kaskad NF farkı**: senaryo tablosundaki blok listesi Friis ile ≈2.6 dB verir; "sistem NF = 6 dB" bütçe değeri olarak tutulur | KICKOFF hem bloklu türetim hem 6 dB istiyor; ikisi birden ancak "kayıplar + ADC eşdeğer NF + pay" açıklamasıyla tutarlı olur. Bölüm 4 ve 9 bunu açıkça anlatır. |
| K10 | **Cihaz değerleri**: internet doğrulaması bu oturumda yapılmadı → Bölüm 10 tablosundaki tüm cihaz sayıları "≈ / doğrulanmadı" işaretli, kapanış raporunda listeli | KICKOFF §10.2: uydurma yok. |
| K11 | **Widget ölçeği**: 20 widget'ın hepsi kurulur; W-06 (mimari karşılaştırıcı) veri odaklı, W-20 capstone W-04/07/08/11/12/17/18/19 çekirdeklerini birleştirir | §7.3 "sayı bağlayıcı değil, kalite bağlayıcı" — birleştirme gerekirse raporda. |
| K12 | Bölüm dosyaları `content/NN-ad.md`; başlık `# Bölüm N — Ad`; ikinci satır `::meta` (okuma süresi build'de kelime sayısından, ön koşul/açtığı bölümler/blok/rota elle) | Seri sözdizimiyle uyumlu, guncelle.py'nin bölüm sayımıyla tutarlı. |

| K13 | **Bölüm üretimi paralel alt-ajanlarla** (7 ajan, Kısım bazlı), YAZIM-REHBERI.md + Bölüm 14 referansıyla; ortak dosyalara dokunmaları yasak, ihtiyaçlar raporla toplanır | 31 bölüm + 90 şema + 20 widget tek oturumda; tutarlılık için tek rehber + tek referans bölüm + merkezî tutarlılık turu (Faz 4) |
| K14 | **W-20 tespit zinciri kapılı gürültü kestirimi kullanır** (`DSP.kapiliGurultuKestirimi`), pencereli CA-CFAR değil | 300 örneklik darbe N=16'lık CA penceresini doldurup kendini maskeliyordu (B23'teki uzun darbe arıza modu); capstone'da öğretici olan "kestirimi darbe varken dondur" pratiğidir. W-18 CA/GO/SO/OS'u ayrıca gösterir. |
| K15 | Referans darbenin **çıkış SNR'ı 23 dB** (−60 − (−83.2)), 44 değil; B28 tablosu ve poster buna göre düzeltildi | İlk taslakta hesap hatası; W-20 hesabı doğruyu verince metin düzeltildi (widget–metin–şekil üçlüsü tutarlılığı). |
| K16 | KICKOFF envanterine **ek şekiller**: g-142 (NCO spur spektrumu, hesaplanmış), g-281/g-282 (seviye merdiveni, latency çizgisi), g-291/g-292 (test noktaları, spur kimliği), g-302 (register bit haritası) | "≥3 görsel/bölüm" kuralı ve bölümlerin gerçek ihtiyacı; kapanış raporunda listelenir. |
| K17 | **Ekler otomatik**: Ek A sözlük glossary.json'dan, Ek B formül dizini kartlardan, Ek F görsel/widget dizini derleme sırasında üretilir | Metin ile dizin kopamaz; yeni terim/şekil eklenince elle güncelleme gerekmez. |
| K18 | Önizleme için yerel `python -m http.server` (`.claude/launch.json`, gitignore'da); `file://` ile büyük dist'te tarayıcı paneli açılamıyordu | Yalnızca geliştirme kolaylığı; belge `file://` üzerinden de çalışır (kapanış turunda ayrıca doğrulanır). |

## 5. RF Örnekleme kılavuzuyla örtüşme haritası

Bağlantı biçimi: `../rf-sampling/index.html#<id>` (id'ler derlenmiş çıktıdan doğrulandı).

| Konu | RF'te nerede / derinlik | Bu kılavuzda |
|---|---|---|
| Örnekleme teoremi, aliasing | `#ornekleme-surekli-dunyadan-sayilara` (orta) | Bölüm 8: 1 paragraf hatırlatma + bağlantı |
| Nyquist bölgeleri, undersampling | `#nyquist-bolgeleri-ve-undersampling` (derin) | Bölüm 8: kısa hatırlatma + **bu kılavuza özgü**: harmonik/interleaving spur katlanması, temiz bant, evrilmenin NCO/IQ ile düzeltilmesi (RF'te yüzeysel kalan yer) |
| Frekans planlama & folding (HD2–HD5) | `#frekans-planlama-ve-folding` (orta-derin) | Bölüm 8 W-07 bunu etkileşimli yapar; metin tekrar etmez, bağlar |
| SNR/ENOB/SFDR/NSD | `#metrik-ormaninda-yol-bulmak` (derin) | Bölüm 9 kendi anlatımını yapar (temel kavram, atlanamaz) ama NSD türetimi için bağlantı verir |
| Aperture jitter | `#jitter-snr-in-sessiz-katili` (derin) | Bölüm 9: formül + W-09; "faz gürültüsü → jitter" için RF'e bağlantı |
| Interleaving spur'ları | `#interleaved-adc-hiz-hilesi-ve-bedeli` | Bölüm 9 kısa + G-93; bağlantı |
| JESD204B/C, subclass, SYSREF, deterministik gecikme | Bölüm 5–7, 9, 10 (çok derin) | **Bölüm 11 yalnızca 1 sayfalık özet** + G-110; her alt konu RF'e bağlı |
| Clocking / PLL / jitter cleaner | Bölüm 8 (çok derin) | Bölüm 11 saat ağacı şeması + bağlantı |
| DDC/NCO/decimation | `#ddc-bandi-sec-hizi-dusur`, `#nco-mekanik-ve-ilk-koherens-sorusu` (derin ama çip-içi DDC gözüyle) | Kısım V burada **çok daha derin** (FPGA gerçeklemesi, spur, bit büyümesi); RF'e "çip içi DDC" için bağlantı |
| SSR / paralel örnek yolları | RF'te yok | Bölüm 11–12 burada anlatır |
| RFSoC RF Data Converter | RF'te yok | Bölüm 10 burada anlatır |

## 6. Bölüm takip tablosu

Durum: ☐ yok · ◐ taslak · ● tam (şablon 12 madde, ≥3 görsel, widget, iki tema OK)

| B | Ad | Görseller | Widget | Durum |
|---|---|---|---|---|
| 0 | Bu Kılavuz ve Büyük Resim | G-00 G-01 G-02 | — | ● |
| 1 | Sinyalin Dili | G-10 G-11 | W-01 | ● |
| 2 | Kompleks Sinyal ve I/Q | G-20 G-21 G-22 | W-02 | ● |
| 3 | Darbeli Sinyalin Anatomisi | G-30 G-31 G-32 | W-03 | ● |
| 4 | Gürültü, SNR, Hassasiyet | G-40 G-41 | W-04 | ● |
| 5 | RF Zincirinin Yapıtaşları | G-50 G-51 G-52 | — | ● |
| 6 | Frekans Dönüştürme | G-60 G-61 G-62 | W-05 | ● |
| 7 | Almaç Mimarileri Kataloğu | G-70…G-79 G-7A G-7B | W-06 | ● |
| 8 | Örnekleme ve Frekans Planlama | G-80 G-81 | W-07 | ● |
| 9 | Kuantizasyon ve ADC Metrikleri | G-90 G-91 G-92 G-93 | W-08 W-09 | ● |
| 10 | ADC Mimarileri, Direct RF ADC | G-100…G-103 | — | ● |
| 11 | ADC'den FPGA'ya | G-110 G-111 G-112 | — | ● |
| 12 | Sabit Nokta ve DSP Yapıtaşları | G-120 G-121 G-122 | W-10 | ● |
| 13 | MATLAB'dan FPGA'ya | G-130 G-131 | — | ● |
| 14 | NCO | G-140 G-141 +G-142 | W-11 | ● |
| 15 | Sayısal Mixing | G-150 G-151 | W-12 | ● |
| 16 | Filtreleme ve Decimation | G-160…G-163 | W-13 | ● |
| 17 | Kanallaştırma | G-170 G-171 G-172 | — | ● |
| 18 | FFT Temelleri | G-180 G-181 G-182 | W-14 | ● |
| 19 | Pencereleme | G-190 G-191 | W-15 | ● |
| 20 | FPGA'da FFT, Frekans Ölçümü | G-200 G-201 G-202 | W-16 | ● |
| 21 | Tespit Teorisi | G-210 G-211 G-212 | W-17 | ● |
| 22 | Zarf ve Entegrasyon | G-220 G-221 G-222 | — | ● |
| 23 | Gürültü Tahmini ve CFAR | G-230…G-233 | W-18 | ● |
| 24 | PDW Nedir | G-240 G-241 | — | ● |
| 25 | Parametre Ölçümü | G-250 G-251 G-252 | W-19 | ● |
| 26 | Darbe FSM ve PDW Veri Yolu | G-260 G-261 G-262 | — | ● |
| 27 | PDW'den Sonrası | G-270 | — | ● |
| 28 | Uçtan Uca Referans Tasarım | G-280 | W-20 | ● |
| 29 | Doğrulama ve Hata Ayıklama | G-290 | — | ● |
| 30 | Kontrol Yüzeyi | G-300 G-301 | — | ● |
| A–F | Ekler | — | — | ● (A sözlük, B formül dizini, F görsel dizini otomatik) |

## 7. Yürütme günlüğü

- Faz 0: repo çekildi, seri tarandı, KICKOFF taşındı, scenario.json yazıldı, bu plan.
- Faz 1: iskelet (CSS, build.py, check.py, dsp-core + 34 test, widget-kit, site.js, symbols.svg) + dikey dilim Bölüm 0 ve Bölüm 14 (W-11) — commit 94650f6.
- Faz 2 (paralel): Kısım I–VIII yedi alt-ajana dağıtıldı (ilk deneme Fable kota limitine takıldı, ikinci deneme tamamlandı). Bu arada Bölüm 28–30, Ekler A–F, W-20, gen_figures ve raf kaydı yazıldı — commit'ler ce31ba1, 2bf4ce4.
- Faz 3: W-20 capstone, Bölüm 28 büyük pasaport tablosu, sözlük 94 → 129 terim (ajan raporlarından), formül/görsel dizinleri otomatik.
- Faz 4 (kalite turu): check.py tam geçiş (dış URL 0, id benzersiz, iç bağlantı tam, SVG sabit renk 0, G/W envanteri tam, 34 JS + 16 Python testi); üç-göz id tekrarı ve altyazı içi makro hataları derleyicide düzeltildi; mobil 380 px yatay taşma (sözlük baloncuğu) giderildi; iki temada ve 20 widget'ta konsol hatası yok; raf kartı doğrulandı; guncelle.py'ye Windows konsol UTF-8 asgari düzeltmesi.
- Faz 4b (kapsamlı QA turu, kullanıcı talebi): 6 paralel denetçi ajan her şekli iki temada headless Chrome ile render edip inceledi; 104 şeklin ~85'inde etiket çakışması/taşma/renk dili düzeltmesi (üreteçlerde kalıcı), 3 içerik hatası (g-52 kTB bandı, g-81 Nyquist bölge genişliği, g-232 altyazı–şekil uyumu, g-261 PDW/descriptor) giderildi; 20 widget preset preset kontrol edildi (w14 FFT tabanı ölçümü, w15 flat-top yan lob, w20 iki emiter preset'i düzeltildi). Kritik ortak hata: `<use>` gölge ağacına belge CSS'i uygulanmıyordu → symbols.svg sınıfları satır içi `var()` niteliklerine çevrildi. Dil turu: zorlama Türkçe türetmeler "İngilizce (Türkçe)" kalıbına çekildi; "örtüşme" belirsizliği (aliasing/overlap) giderildi; yanlış ileri köprüler (B17/18, B25/26, B27/30) düzeltildi. Araçlar: build/gallery.py, build/svg_lint.py. FIFO derinliği scenario.json'a alındı (1024).
- Toplam: 31 bölüm + 6 ek, 104 şekil (13'ü KICKOFF envanterine ek), 20 widget, 83 formül kartı, ≈109 500 kelime (kod/tablo dahil), dist 3,7 MB.
