# YAZIM REHBERİ — almac-saha-kilavuzu bölüm yazarları için

Bu dosya, bir bölümü (md + SVG + widget) üretirken uyulacak somut kuralları
toplar. İçerik ve pedagoji kararları KICKOFF.md'de; burada "nasıl yazılır"
var. **Referans bölüm: `content/14-nco.md`** — ton, yoğunluk, bileşen
kullanımı ve şablon sırası için onu örnek al. Referans görseller:
`assets/svg/g-140-*.svg`, `g-141-*.svg`, `g-00-poster.svg`. Referans widget:
`assets/js/widgets/w11-nco.js`.

## 1. Dosya ve başlık

- `content/NN-kisa-ad.md` (NN iki haneli bölüm no; ekler `31-ek-a-sozluk.md` …).
- İlk satır: `# Bölüm N — Başlık` (uzun tire `—`). Ekler: `# Ek A — Sözlük`.
- Kısmın ilk bölümünde ikinci satır: `::kisim I — Temeller: Sinyal, Spektrum, Gürültü`
- Meta satırı (zorunlu): `::meta onkosul=1,2 acar=5,9 blok=nco rota=yazilimci,sayisal`
  - `onkosul`/`acar`: bölüm numaraları (virgül); RF Örnekleme için `rf:anchor` da yazılabilir.
  - `blok`: zincir durak id'leri (`anten onuc mixer if adc arayuz nco mixing filtre zarf esik fft olcum pdw ps`), birden çoksa virgül.
  - `rota`: `yazilimci` ve/veya `sayisal` (KICKOFF §4.3 listesine göre). Boş → yalnız tam yolculuk.

Kısım adları (KICKOFF §6): 0 Yön Bulma · I Temeller: Sinyal, Spektrum, Gürültü ·
II RF Ön Uç ve Almaç Mimarileri · III Analogdan Sayısala: ADC · IV FPGA'da DSP'nin
Zemini · V Sayısal Almaç Zinciri (DDC) · VI Frekans Domaini: FFT · VII Tespit:
Eşik, Gürültü Tahmini, Yanlış Alarm · VIII PDW Üretimi · IX Sistem Bütünü ve Pratik · Ekler.

## 2. Bölüm şablonu (KICKOFF §4.2) — bu sırayla

1. `:::neden-onemli` … `:::` — 3–5 cümle, **sahadan bir soruyla açılır**.
2. `## Sezgi: …` — analoji (`:::analoji Başlık`) burada ya da hemen sonra.
3. `## Kavram: …` başlıkları (birkaç tane) — görsellerle iç içe (`{{svg:…}}`).
4. Matematik: `:::formul` kartları; formül **asla ilk cümle olmaz**, her formülün altında `o:` satırıyla referans senaryodan sayı.
5. `:::pasaport durak="…" alan=…` — sinyal zincirinde durağı olan bölümlerde (5, 6, 8, 9, 11, 14, 15, 16, 22, 23, 26; 28'de büyük tablo).
6. `## FPGA'da nasıl gerçeklenir` → `:::uc-goz` (rf / fpga / yazilim) ve/veya `:::matlab-fpga`.
7. `## Yazılımcıya dokunan yer` — register, birim dönüşümü, C snippet (```c).
8. En az bir `:::tuzak Başlık` (tercihen 2–3; sahada gerçekten yapılan hata).
9. `:::ozet` — 5–7 madde (`-` listesi; build numaralı karta çevirir).
10. `:::kendini-sina` — 3–5 `S:`/`C:` çifti.
11. `:::kopru` — sonraki bölüme tek paragraf.
12. `:::widget` kavram tanıtıldıktan **hemen sonra** (gör → oyna → anla); gövdesi 2–4 maddelik "Ne gözlemlemeliyim?" listesi, her madde "şunu yap → şunu gör" biçiminde ve **sayı içerir**.

Şablon maddesi bölüme uymuyorsa atlanır (Bölüm 1'de FPGA gerçeklemesi yok gibi) ama
tuzak / özet / kendini sına / köprü her bölümde zorunlu. Bölüm başına **≥ 3 statik görsel**
(ufuk turu bölümleri 27 hariç). Hedef uzunluk 1800–3200 kelime (Bölüm 7, 9, 23 daha uzun olabilir).

## 3. Dil ve ton

- Türkçe anlatım; teknik terim İngilizce aslıyla. İlk geçişte `Türkçe karşılık (English term)` ya da `**FTW** (Frequency Tuning Word — frekans ayar sözcüğü)`.
- İkinci tekil şahıs, sıcak ama gevşek değil ("teknik blog" tonu). Okur: register yazan gömülü yazılımcı.
- **Bağımlılık kuralı:** Bölüm N, N'den sonra anlatılan hiçbir kavrama yaslanamaz. İleriye yalnızca "köprü" niteliğinde `{{bolum:15}}` bağlantısı verilebilir ("ayrıntı Bölüm 15'te").
- Her formülün her sembolü `s:` satırında tanımlı ve birimli. Tanım farkları açıkça söylenir (PW −3/−6 dB/%50, SFDR dBc/dBFS, tek/çift taraflı BW).
- Kaynaklar: yalnızca açık literatür; gerçek sistem/tehdit parametresi, proje adı yok. Cihaz sayısı yazarken emin değilsen `≈` ve "(doğrulanmadı)" ekle.
- Kurgusal formatlar (PDW, register haritası) "kurgusal, öğretici" diye işaretlenir.
- Referans senaryo sayıları **elle yazılmaz**: `{{s:adc.fs_msps}}` gibi makro (anahtarlar `data/scenario.json`). Türetilmiş sayılar için `{{s:turetilmis_beklenen.…}}`.
- Sayılar: ondalık nokta (6.02), binlik boşluk (4 294 967 296), birimler SI (MSPS, dBm, µs, ns).

## 4. md sözdizimi (özet — tam liste build/build.py başında)

```
{{svg:g-160-fir.svg|Altyazı cümleleri.}}          {{svg:…|…|kaydir}} geniş şema
{{s:ddc.nco_mhz}}  {{bolum:15}}  {{bolum:15|Bölüm 15'teki DDC}}  {{ek:a}}  {{rf:nyquist-bolgeleri-ve-undersampling|RF Örnekleme}}
$x^2$ $e^{-jωt}$ $frac{f_s}{2^N}$ $sqrt{I^2+Q^2}$   → satır içi formül (Cambria Math)
:::formul id=snr-q baslik="Kuantizasyon SNR'ı"
f: SNR_q = 6.02 · N + 1.76  dB
s: N | çözünürlük | bit
o: N = {{s:adc.bit}} → **{{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB**
:::
:::uc-goz
::rf::  …  ::fpga::  …  ::yazilim::  …
:::
:::matlab-fpga
::matlab::  ```matlab … ```  ::fpga::  ```verilog … ```
:::
:::pasaport durak="DDC çıkışı" alan=sayisal      (alan: analog | sayisal | yazilim)
Alan: sayısal (FPGA)
!Frekans: baseband ±150 MHz        ← "!" = önceki durağa göre değişti (altın)
:::
:::kendini-sina
S: Soru?
C: Cevap (birkaç cümle).
:::
:::mimari no=3 ad="Zero-IF / homodyne" sema=g-72-zero-if.svg
::ilke:: … ::arti:: - … ::eksi:: - … ::kullanim:: … ::ozellik::
Anlık BW: 4        (0–5 ölçek; satırlar: Anlık BW, Hassasiyet, Dinamik aralık, Eşzamanlı sinyal, Frekans doğruluğu, POI, Karmaşıklık)
:::
:::widget id=w13 ad="Filtre ve decimation laboratuvarı"
- Deney 1 → beklenen gözlem (sayı ile)
:::
{{tablo: genis belirti-neden}}      ← hemen ardından gelen tabloya sınıf
```

Formül mini-dili: `x^2`, `x^{ab}`, `x_j`, `x_{out}`, `frac{a}{b}`, `sqrt{a}`, `**kalın**`;
Unicode serbest (· × − ≈ ≤ ≥ √ π σ Δ ∑ ∫ ∞ °). `\` yok, LaTeX yok.

## 5. SVG kuralları

- Dosya adı `assets/svg/g-XXX-kisa-ad.svg` (KICKOFF §6 numarası: `g-10`, `g-7a`, `g-100` …).
- `<svg viewBox="0 0 860 H" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t-gXXX">` + `<title id="t-gXXX">…</title>` (uzun, açıklayıcı). Geniş şemalar 900–1180 genişlik + `|kaydir`.
- **Renk yalnızca CSS değişkeni**: `var(--gold) --accent --green --red --purple --ink --ink-2 --ink-3 --line --line-2 --dia-panel --dia-blok --dia-blok-2 --dia-grid --dia-noise --gold-soft --accent-soft --green-soft --red-soft`. Sabit hex → build uyarır, check.py hata verir.
- Hazır sınıflar (kilavuz.css): metin `s-baslik s-metin s-metin2 s-kucuk s-mono s-mono2`, renk `s-vurgu s-altin s-yesil s-kirmizi s-mor`; yollar `yol-analog yol-sayisal yol-kontrol yol-saat yol-gurultu`; bloklar `blok blok-aktif blok-analog blok-kontrol`; spektrum `spk-sinyal spk-image spk-gurultu spk-filtre`; `eksen izgara`.
- Ok uçları belgeye bir kez gömülü: `marker-end="url(#ok-analog)"` `#ok-sayisal #ok-kontrol #ok-saat #ok-gurultu #ok-ince`. Kendi marker'ını tanımlama.
- Semboller (`assets/svg/symbols.svg`, 60×40 kutu, giriş sol orta / çıkış sağ orta):
  `<use href="#sym-anten" x=".." y=".." width="60" height="40"/>` — mevcutlar: anten, amp, mixer, mixer-d, bpf, lpf, fir, dec, lo, nco, att, limiter, adc, fft, cmp, fifo, reg, dma, cpu, zarf, blok, topla, gecikme, saat, diyot. Blok şemalar bunlardan kurulur; etiketi altına `<text>` ile yaz.
- Şema renk dili (KICKOFF §5.3) zorunlu: analog altın / sayısal mavi / kontrol yeşil / saat gri kesikli / istenmeyen kırmızı; spektrumda sinyal mavi, image/spur kırmızı, gürültü gri dolgu, filtre altın kesikli.
- Spektrum/eğri çizimlerinde eksen değerleri referans senaryoyla tutarlı; eğri noktalarını kafadan değil hesapla (kısa Python ile üretip path'e yapıştır; hesabı `build/gen_figures.py`'ye fonksiyon olarak eklemek tercih edilir).
- Metin boyutu 10–14 px; mobilde okunur kalsın. Tıklanabilir bloklar `<a href="#bolum-N">`.
- **Zaman ve frekans yan yana**: sinyal gösteren görselde mümkünse iki panel.

## 6. Widget kuralları (`assets/js/widgets/wNN-ad.js`)

```js
WK.kaydet("w13", function (w) {
  var S = w.S;                                   // scenario.json
  WK.kaydirici(w, { ad:"fc", etiket:"kesim", min:1e6, max:150e6, adim:1e6, deger:100e6, olcek:1e6, birim:"MHz" });
  WK.secim(w, { ad:"tip", etiket:"filtre", secenekler:[["fir","FIR"],["cic","CIC"]], deger:"fir", metin:true });
  WK.onay(w, { ad:"dither", etiket:"dither", deger:true });
  var kapat = WK.grup(w, "Grup adı"); /* kontroller */ kapat();
  var p1 = WK.panel(w, 240);                     // inline SVG paneli
  function ciz() {
    WK.temizle(p1);
    var g = WK.grafik(p1, { W:640, H:240, xmin:0, xmax:150, ymin:-100, ymax:5 });
    g.eksenler({ xAd:"frekans (MHz)", yAd:"dB", baslik:"…", xAdet:6, yAdet:5 });
    g.cizgi(xs, ys, "w-cizgi-sinyal"); g.alan(xs, ys, -100, "w-dolgu-sinyal"); g.yatay(-6, "w-cizgi-kirmizi", "etiket"); g.dikey(75, "w-cizgi-gri", "fs/2"); g.nokta(x, y); g.bant(xa, xb, "w-dolgu-altin");
    WK.sonucYaz(w, { "etiket": "değer", "uyarı": "!kötü", "iyi": "+iyi" });
  }
  return { ciz: ciz, presetler: [ { ad:"Referans senaryo", param:{…} }, { ad:"Kötü durum", param:{…} } ] };
});
```

- Hesap `DSP.*` (assets/js/dsp-core.js) ile; widget dosyasında yalnızca çizim ve küçük yardımcılar. Eksik fonksiyon gerekiyorsa widget dosyasının başına yerel yardımcı olarak ekle ve raporunda belirt (çekirdeğe ben taşırım).
- İlk preset her zaman "Referans senaryo" ve `w.S`'ten beslenir. Deterministik: `DSP.prng(sabit)`.
- N ≤ 8192; çizgi noktaları ≤ ~2000 (gerekirse seyrelt). Tema-uyumlu: yalnızca `w-*` sınıfları / CSS değişkenleri; sabit renk yok.
- Kilit sayılar `WK.sonucYaz` ile metin olarak da gösterilir; "!" uyarı (kırmızı), "+" iyi (yeşil).
- Kontrol etiketleri Türkçe, birimli. Frekansları `olcek:1e6, birim:"MHz"` ile göster.
- Sayfa yüklenmeden hesap yapmaz (kit hallediyor); 100 ms'den uzun süren hesap varsa N'i küçült.

## 7. Kalite kapıları (bölüm bitince)

```
python build/build.py      # kelime/şema/widget/tuzak/özet/ks sayacı; EKSİK SVG ve UYARI listesi boş olmalı (kendi bölümün için)
python build/check.py --hizli
```
Kendi bölümünle ilgili: kırık `#` bağlantısı yok (henüz yazılmamış bölümlere `{{bolum:N}}` bağlantısı normaldir),
sabit renk yok, her SVG'de `<title>`, şablon uyarısı yok, widget konsol hatası yok
(`node --check assets/js/widgets/wNN.js`). Formüllerdeki sayıları `node -e` ile dsp-core'dan hesaplayıp doğrula.

## 8. Dokunma

`assets/css/kilavuz.css`, `build/*.py`, `assets/js/dsp-core.js`, `assets/js/widget-kit.js`,
`assets/js/site.js`, `data/*.json`, `assets/svg/symbols.svg`, başka bölümlerin dosyaları.
İhtiyaç (yeni sözlük terimi, yeni sembol, çekirdek fonksiyonu, CSS) → raporunda listele.
