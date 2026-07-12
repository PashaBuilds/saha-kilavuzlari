# Bölüm 5 — Donanım I: Bellek Her Şeydir

Bu bölüm kılavuzun kalbidir. Ekran kartı ya da bilgisayar seçerken herkesin
baktığı şeyler — çekirdek sayısı, saat hızı, işlemci nesli — lokal LLM için
**ikincil** önemdedir. Belirleyici olan iki soru vardır ve ikisi de bellekle
ilgilidir:

1. **Kapasite:** model (+ çalışma payı) belleğe sığıyor mu?
2. **Bant genişliği:** o bellek, veriyi işlemciye saniyede kaç GB akıtabiliyor?

Birincisi "çalışır mı?"yı, ikincisi "kaç token/s?"i belirler. Bu ikisini
kavradığında, hiç görmediğin bir cihaz + model ikilisinin davranışını kabaca
tahmin edebilir hâle geleceksin — kılavuzun vaadi olan beceri tam da bu.

## Modelin oturacağı yer: bellek katmanları

Bilgisayarında hızları ve boyutları çok farklı birkaç bellek katmanı var.
Model, çıkarım (inference — modeli çalıştırıp cevap üretme) sırasında bu
katmanlardan birinde oturur:

{{svg:09-bellek-hiyerarsisi.svg|Bellek hiyerarşisi: VRAM en hızlı ama dar, unified memory hızlı ve geniş, sistem RAM yavaş ama bol, disk ise fiilen kullanım dışı. Model + context hangi katmana sığıyorsa hız o katmandan gelir.|wide}}

Sığma hesabı yaparken "toplam bellek" değil **kullanılabilir bellek** üzerinden
düşün:

:::hesap Kullanılabilir bellek kestirimi
>> Ayrık GPU: VRAM − ~1 GB (ekran/sürücü payı) → 24 GB kartta ~23 GB
>> Mac (unified): RAM × ~0,70 (varsayılan GPU tavanı) → 48 GB Mac'te ~34 GB
>> CPU-only: RAM − işletim sistemi ve uygulamalar (~6 GB) → 32 GB PC'de ~26 GB
=> Model dosyası + context payı (Bölüm 7; kabaca 1-4 GB) bu sayının altında kalmalı
Mac'te GPU tavanı bir sistem ayarıyla (%75-80'e) yükseltilebilir; planlamayı
yine de %70 ile yap ki nefes payın kalsın.
:::

:::tuzak
En pahalı hatalardan biri: "32 GB RAM'im var, 27B-Q4 (17 GB) rahat sığar"
deyip **swap'a düşmek.** Bellek dolunca işletim sistemi taşan kısmı diske
(swap) yazar; disk bant genişliği RAM'in 20-50'de biri olduğundan hız token/s
cinsinden değil, **token başına saniye** cinsinden ölçülür hâle gelir. Sistem
"çalışıyor" görünür ama kullanılamaz. Belirti: ilk birkaç token normal gelir,
sonra her şey taş gibi durur. Çözüm: daha küçük model/quant ya da kapasiteyi
context dahil dürüst hesaplamak.
:::

## Bant genişliği: token hızının tek büyük belirleyicisi

Şimdi kılavuzun en önemli kavrayışı. Bölüm 1'de gördük: model her token'ı
üretirken ağın (MoE'de: aktif dilimin) **tüm parametrelerini** hesaba sokar.
Bunun donanım karşılığı şudur: **her token için, aktif ağırlıkların tamamı
bellekten işlemciye taşınır.** 5 GB'lik bir model, token başına ~5 GB okuma
demektir. Saniyede 40 token istiyorsan bellek 200 GB/s akıtabilmelidir.

Modern işlemciler bu ölçekteki çarpma işlemlerini veriyi taşıyabildiklerinden
çok daha hızlı yaparlar; yani token üretiminde dar boğaz hesap değil,
**veri taşımadır.** İşlemci çoğu zaman belleği bekler. Bu yüzden token hızı
kaba ama şaşırtıcı isabetli bir formüle oturur:

{{svg:10-bant-genisligi-hiz.svg|Her token üretimi, aktif ağırlıkların tamamının bellekten okunmasını gerektirir. Bu yüzden token/s, kabaca bant genişliğinin aktif model boyutuna oranıdır.|wide}}

:::analoji
Bellek bir su deposu, bant genişliği deponun borusudur. Her token'da deponun
tamamı borudan bir kez akmak zorunda. Token hızını depo ne kadar dolu olduğun
değil, **borunun çapı** belirler. Modeli küçültmek (quantization) depoyu
küçültür — aynı borudan daha sık tur atar. MoE, deponun yalnızca bir bölmesini
akıtır. GPU almak, boruyu kalınlaştırmaktır.
:::

:::hesap Üç gerçek kestirim
>> RTX 3060 (360 GB/s) + 8B-Q4 (~5 GB): 360 ÷ 5 × 0,6 ≈ 43 token/s — saha: 40-60 ✓
>> M4 Max (546 GB/s) + 27B-Q4 (~17 GB): 546 ÷ 17 × 0,6 ≈ 19 token/s — saha: ~20 ✓
>> DDR5 PC (90 GB/s) + 8B-Q4 (~5 GB): 90 ÷ 5 × 0,6 ≈ 11 token/s — saha: 8-12 ✓
=> Okuma hızında rahat kullanım ~15-20 token/s; 5'in altı sabır işidir
Verim çarpanı (~0,6) motor ve modele göre 0,5-0,7 arasında oynar; MTP gibi
hızlandırıcılar (Bölüm 8) bu tavanı aşabilir. Kestirim yine de yol gösterir.
:::

<div class="calc" data-calc="hiz">
  <span class="calc-title">Canlı hesap: token/s kestirimi</span>
  <div class="calc-row">
    <label>Bellek bandı (GB/s):</label>
    <input type="number" name="bant" value="360" min="1" step="1">
    <label>Aktif model boyutu (GB):</label>
    <input type="number" name="aktif" value="5" min="0.1" step="0.1">
  </div>
  <div class="calc-row">
    <span>Beklenen hız: <span class="calc-out" data-out="hiz">—</span></span>
  </div>
  <p class="calc-note">Aktif boyut: dense modelde dosya boyutunun kendisi; MoE'de dosya × (aktif ÷ toplam parametre). Örn. 35B-A3B Q4 (22 GB): 22 × 3/35 ≈ 1,9 GB.</p>
</div>

Sık karşılaşacağın bant genişliği mertebeleri (ayrıntılı cihaz rehberi
Bölüm 6'da): çift kanal DDR5 masaüstü ~90 GB/s, Apple M4 ~120, M4 Pro ~273,
Strix Halo ~256 (ölçülen ~215), RTX 3060 ~360, M4 Max ~546, M3 Ultra ~819,
RTX 3090/4090 ~940-1.008, RTX 5090 ~1.792 GB/s. Aradaki 20 katlık fark,
aynı modelin cihazlar arasında neden 20 kat farklı hızda çalıştığının
bütün açıklamasıdır.

## Üç makine mimarisi

Bu iki kavramı (kapasite + bant) cihaz dünyasına yerleştirelim:

{{svg:11-uc-mimari.svg|Ayrık GPU: dar ama çok hızlı VRAM. Unified memory: büyük ve orta-hızlı ortak havuz. CPU-only: bol ama yavaş RAM. Hepsinde aynı formül geçerlidir.|wide}}

**Ayrık GPU** dünyasında altın kural: model VRAM'in içinde kalmalı. VRAM'e
sığan model uçar; sığmayan modelin taşan katmanları PCIe köprüsünden geçip
sistem RAM'ine yaslanır ve hız keskin düşer. **Unified memory** (Apple
Silicon, AMD Strix Halo) bu duvarı kaldırır: CPU ve GPU aynı büyük havuzu
kullanır, "sığmadı" eşiği çok yukarı taşınır; bedeli, bandın üst sınıf
GPU'lardan düşük olmasıdır. **CPU-only** ise herkesin elindeki seçenektir:
küçük modeller (ve aktif parametresi küçük MoE'ler!) DDR5 bandıyla bile
kullanılabilir hızda döner.

## GPU offload: ikisinin arası

Model VRAM'e tam sığmıyorsa her şey bitmiş değildir. Çıkarım motorları
**GPU offload** yapabilir: katmanların bir kısmı VRAM'de (hızlı), kalanı
sistem RAM'inde CPU tarafından (yavaş) çalışır. Toplam hız, iki dünyanın
ağırlıklı ortalamasına yaklaşır — katmanların yarısı GPU'daysa hız GPU
hızının yarısına bile ulaşmaz, çünkü kervan en yavaş deve hızında yürür.

Yine de offload iki durumda kıymetlidir. Birincisi "az taşan" modeller:
katmanların %80'i VRAM'deyse kayıp katlanılabilir düzeyde kalır. İkincisi ve
2026'da asıl önemlisi **MoE offload**: MoE modellerde sık kullanılan ortak
katmanlar + aktif yol VRAM'de tutulup dev expert havuzu RAM'e yatırılabilir;
token başına RAM'den yalnızca küçük bir dilim okunduğu için (altın kural!)
24 GB'lik bir GPU + bol RAM ile 100B+ toplam parametreli modeller sürpriz
biçimde kullanılabilir hızda çalışır. Bölüm 11'de bu sınıfın örneklerini
göreceksin.

:::saha-notu
Ekran kartı karşılaştırırken önce **VRAM miktarı × bellek bandı** ikilisine
bak; FLOPS, çekirdek sayısı ve oyun benchmark'ları LLM çıkarımı için yanıltır.
Klasik örnek: RTX 4060 Ti 16GB, adı "40 serisi" olduğu hâlde 288 GB/s bandıyla
eski 3060'ın (360 GB/s) altındadır — LLM'de 16 GB'lik VRAM avantajına rağmen
token hızında geri kalır. İkinci el pazarındaki 3090 (24 GB, 936 GB/s) tam da
bu iki sayı yüzünden yıllardır lokal LLM'cilerin gözdesidir.
:::

:::derin-dalis Neden hesap değil de veri dar boğaz? Küçük bir aritmetik
8B-Q4 model token başına ~8 milyar çarpma-toplama ister; RTX 3060 sınıfı bir
GPU saniyede ~10 trilyon işlemi rahat yapar — kâğıt üstünde 1.000+ token/s.
Ama aynı token için 5 GB veri taşınmalı ve 360 GB/s'lik boru bunu saniyede
en fazla 72 kez yapabilir. 1.000'e karşı 72: işlemci zamanının çoğunu bekleyerek
geçirir. Bu dengesizliğe **memory-bound** (bellek-sınırlı) çalışma denir.
Tersi durum — verinin bir kez taşınıp üzerinde çok hesap yapılması — prompt
işlemede yaşanır (compute-bound); o hikâye Bölüm 7'de. Bu ayrım, "GPU'lar
prompt'u yutar, Mac'ler üretimde parlar" gibi saha gözlemlerinin de anahtarıdır.
:::

:::ozet
- İki soru her şeyi belirler: sığıyor mu (kapasite), kaç token/s (bant genişliği).
- Kullanılabilir bellek: VRAM−1 GB / Mac RAM×0,7 / PC RAM−6 GB; swap'a düşen
  kurulum kullanılamaz.
- **token/s ≈ bant ÷ aktif boyut × 0,6** — kılavuzun tek formülle en çok iş
  gören satırı. MoE'de "aktif boyut" küçüktür; hız avantajının kaynağı bu.
- Ayrık GPU dar-hızlı, unified memory geniş-dengeli, CPU-only bol-yavaş;
  offload ikisinin ortalamasıdır, MoE offload ise 2026'nın sürpriz kozudur.
- Kart seçerken VRAM × bant ikilisine bak; FLOPS ve oyun skorları yanıltır.
:::
