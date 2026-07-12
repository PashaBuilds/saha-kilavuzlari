# Bölüm 6 — Donanım II: Ne Alınır, Neyle Yetinilir

Bölüm 5'in iki sorusunu (kapasite + bant) cebimize koyduk; şimdi vitrine
çıkabiliriz. Bu bölüm cihaz sınıflarını tek tek gezer: her sınıfın neye
yettiğini, neye yetmediğini ve 2026 ortası itibarıyla kaça mal olduğunu
dürüstçe söyler. Önemli çerçeve notu: **fiyatlar bu bölümün en çabuk eskiyen
bilgisidir** — 2026'daki bellek/GPU fiyat krizi (AI talebi DRAM arzını yuttu,
üst sınıf kartlar çıkış fiyatının iki katına satılıyor) rakamları aydan aya
oynatıyor. Sınıf mantığı kalıcıdır, etiketler dönemseldir.

## Sıfırıncı kural: önce eldekiyle dene

Tek bir lira harcamadan önce şunu iç rahatlığıyla bil: **bu kılavuzdaki her
şey, bugün elindeki makinede denenebilir.** 8 GB RAM'li mütevazı bir laptop
bile 4B sınıfı bir modeli (Q4'te ~2,5 GB) çalıştırır; 16 GB'lik sıradan bir
makine 7-9B sınıfını, aktif parametresi küçük MoE'leri rahat döndürür.
Hız, üst sınıf donanımdaki gibi olmaz — ama "lokal LLM bana ne verir?"
sorusunun cevabını almak için fazlasıyla yeter. Donanım parası, ancak bu
deneme sana "evet, bunu daha hızlı/daha büyük istiyorum" dedirtirse anlamlıdır.

{{svg:12-cihaz-harita.svg|2026 ortası cihaz haritası: yatay eksen kullanılabilir bellek, dikey eksen bant genişliği, etiketler yaklaşık sokak fiyatı. İki yıldızlı nokta (ikinci el 3090 ve Strix Halo) dönemin fiyat/performans şampiyonlarıdır.|wide}}

Haritanın öğrettiği üç şey: (1) sağ üst köşe — hem geniş hem hızlı — boştur;
para o köşeye yaklaşmak için ödenir. (2) Ayrık GPU'lar yukarıda (hızlı-dar),
unified memory cihazları sağda (geniş-orta) kümelenir; hangi kümeye gideceğin
"hangi modelleri koşturacağım" sorusunun cevabıdır. (3) Aynı paraya çok farklı
profiller alınabilir: ~$2.000, ister 4090 (24 GB, çok hızlı) ister Strix Halo
(128 GB, orta hızlı) demektir.

## Sınıf sınıf gezinti

### (a) Eldeki laptop/PC — 8-16 GB RAM, GPU'suz

CPU çıkarımı DDR4/DDR5 bandıyla (~50-90 GB/s) sınırlıdır; formülü uygula:
8B-Q4 (5 GB) → ~6-11 token/s. Yavaş ama okunabilir hız. Bu sınıfın gerçek
kahramanları küçük modeller (Phi-4-mini, Gemma küçükleri, Qwen 4B) ve
**aktif parametresi minik MoE'lerdir** — 30B-A3B sınıfı bir model 24 GB
RAM'li GPU'suz bir makinede bile ~10-15 token/s verebilir, çünkü token başına
yalnızca ~2 GB okunur. Beklentiyi "hızlı asistan" değil "sabırlı yardımcı"
olarak kur.

### (b) Oyuncu GPU'ları — 12/16/24/32 GB VRAM

Lokal LLM'in klasik yolu. Sınıf içi merdiven (Temmuz 2026 sokak fiyatlarıyla):

| Kart | VRAM | Bant | ~Fiyat | Rahat sınıfı (Q4) |
|---|---|---|---|---|
| RTX 3060 12GB (2.el) | 12 GB | 360 GB/s | ~$250-330 | 7-9B akıcı, 12-14B idare |
| RTX 5060 Ti 16GB | 16 GB | 448 GB/s | ~$490-530 | 12-14B akıcı |
| RTX 5070 Ti | 16 GB | 896 GB/s | ~$820-900 | 14B çok hızlı |
| **RTX 3090 (2.el)** | **24 GB** | **936 GB/s** | **~$600-800** | **27-32B akıcı** |
| RTX 4090 (2.el) | 24 GB | 1.008 GB/s | ~$2.300 | 27-32B hızlı |
| RTX 5090 | 32 GB | 1.792 GB/s | ~$4.300+ | 32B uçar; 70B-Q3 sınırda |
| Intel Arc Pro B60 | 24 GB | ~456 GB/s | ~$650 | 27-32B idare; ekosistem genç |

Tablonun yıldızı yıllardır değişmedi: **ikinci el RTX 3090.** 24 GB VRAM +
936 GB/s bandı bugün hâlâ ancak 3-6 kat parayla geçebiliyorsun. 2026 fiyat
krizinde 40/50 serisi fırlarken 3090'ın $600-800 bandında kalması, onu
fiyat/performansta rakipsiz bıraktı. Riski: yaşı (garanti yok, madencilik
geçmişi olabilir) ve 350W+ tüketimi.

İkinci dikkat çeken satır: Intel'in Arc Pro B60/B70 kartları (24-32 GB'yi
$650-950'ye veriyor) "ucuz bol VRAM" kapısını araladı; yazılım desteği
NVIDIA olgunluğunda değil ama llama.cpp/Vulkan tarafında çalışıyor ve
sıkı bütçede izlenmeyi hak ediyor.

### (c) Apple Silicon — unified memory'nin rahatlığı

Mac'lerde bellek havuzu tek olduğundan "VRAM'e sığdırma" stresi yoktur;
128 GB'lik bir MacBook/Studio, 60-100 GB'lik model dosyalarını doğal
karşılar. Bant genişliği çip katmanıyla belirlenir — satın almada asıl
bakılacak yer burasıdır:

| Çip | Azami RAM | Bant | LLM karakteri |
|---|---|---|---|
| M4 / M5 | 32 GB | 120-153 GB/s | küçük modeller; "laptop sınıfı" his |
| M4 Pro / M5 Pro | 64 GB | ~273-307 GB/s | 14-32B ve orta MoE'ler akıcı |
| M4 Max / M5 Max | 128 GB | 410-614 GB/s | 70B sınıfı ~20 token/s; büyük MoE'ler |
| M3 Ultra | 96 GB* | 819 GB/s | *512 GB opsiyonu 2026'da RAM krizine kurban gitti |
| M5 Ultra (beklenen) | 512 GB+ | ~1,2 TB/s? | Ekim 2026'da bekleniyor — dev MoE sınıfı |

Artıları: sessizlik, 40-90W tüketim, taşınabilirlik, MLX ekosistemi (Bölüm 8)
ve M5 neslinin GPU çekirdeklerine eklenen Neural Accelerator'ların getirdiği
~%28'lik ek hız. Eksileri: fiyat (aynı belleğin PC karşılığından pahalı),
bant/dolar oranında GPU'lara yetişememesi ve Bölüm 7'de göreceğin **prefill
yavaşlığı** — uzun prompt'larda ilk cevabın gecikmesi Mac'lerin bilinen
zaafıdır.

### (d) "AI mini PC" sınıfı — Strix Halo, DGX Spark

2025-26'nın yeni kategorisi: 128 GB unified memory'yi kompakt kutuda sunan
makineler.

- **AMD Strix Halo (Ryzen AI Max+ 395):** 128 GB LPDDR5X, teorik 256 GB/s
  (ölçülen ~215). GMKtec, Framework gibi üreticilerden ~$2.000-2.300.
  Sahada gpt-oss-120B'yi ~55 token/s, 30B-A3B sınıfını ~100 token/s
  döndürüyor — fiyatına göre olağanüstü. Linux/ROCm-Vulkan kurulumu biraz
  el ister; "kutudan çıkar çalışır" değil, "bir hafta sonu kurcalarım" cihazı.
- **NVIDIA DGX Spark:** 128 GB @ 273 GB/s + CUDA ekosistemi, $4.699 (2026
  zamlı fiyatı). Tek akış üretimde Strix Halo'dan bile yavaş (~39 token/s,
  gpt-oss-120B) ama prefill'de 5-10 kat önde ve CUDA gerektiren her şeyle
  (fine-tuning, görüntü modelleri, ajan yığınları) uyumlu. "Ucuz token
  makinesi" değil, "masaüstü AI geliştirme kutusu".

### (e) Çoklu GPU ve sunucu tarafına pencere

2×3090 (48 GB, ~$1.500) uzun süredir ev sunucularının klasiğidir; llama.cpp
ve vLLM modeli kartlara bölebilir. Daha üstü — 4-8 GPU'lu iş istasyonları,
Intel'in 8×B60 "Battlematrix" (192 GB) gibi kurulumlar — artık ev değil,
küçük şirket ölçeğidir: anakart/PSU/soğutma maliyeti kart parasına yaklaşır,
elektrik 1-2 kW bandına çıkar. Bu kılavuzun kapsamı tek makinede biter;
oraya adım atacaksan aradığın anahtar kelimeler vLLM, tensor parallelism
ve 240V priz.

:::hesap Aynı $2.000'a üç farklı profil (Temmuz 2026)
>> 2.el 3090 + mevcut PC: 24 GB @ 936 GB/s → 27B-Q4 ~30-40 token/s; 70B'ye kapı kapalı
>> Strix Halo 128 GB: 96+ GB kullanılabilir @ ~215 GB/s → 27B-Q4 ~7-8 t/s ama 120B MoE ~50 t/s
>> M4 Pro 64 GB Mac mini: 44 GB @ 273 GB/s → 27-32B ~9-10 token/s, sessiz, 40W
=> "En iyi cihaz" yok; koşturacağın model sınıfına göre en iyi cihaz var
Dense orta boy modellerde GPU ezici; dev MoE'lerde geniş havuz kazanır;
sessizlik/tüketim öncelikse Mac. Önce Bölüm 11'deki tablodan modelini seç,
cihazı ona göre al — tersi değil.
:::

:::tuzak
"Pahalıysa hızlıdır" bu pazarda çalışmaz. $4.699'luk DGX Spark, token üretiminde
$2.000'lık Strix Halo'nun gerisinde kalabilir (273 vs ~215 GB/s ama yazılım
farkları; ikisi de tek akışta 128 GB sınıfının "orta hız" karakterindedir).
Benzer şekilde 16 GB'lik yeni nesil bir kart, 24 GB'lik yaşlı 3090'ın
koşturduğu modeli hiç koşturamaz. Fiyat etiketi yerine hep aynı iki sayıya
dön: kullanılabilir bellek + bant genişliği.
:::

:::saha-notu Elektrik, ısı, gürültü — faturanın görünmeyen satırları
Sürekli çalışan bir lokal AI kutusu ev ortamında yaşar; üç gerçeği baştan bil.
**Elektrik:** 3090 tek başına yük altında ~350W çeker; günde 8 saat kullanım,
yerel tarifeye göre ayda hissedilir bir fatura kalemidir. Mac mini/Studio ve
mini PC'ler 40-140W bandındadır. **Isı:** 350W'lık kart küçük bir odayı
kışın ısıtır, yazın çileden çıkarır. **Gürültü:** üfleyici fanlı eski
kartlar yük altında duyulur; yatak odası sunucusu planlıyorsan Mac/mini PC
sınıfının sessizliği başlı başına satın alma gerekçesidir. Ölçmek için:
akıllı priz ($15) + bir hafta gerçek kullanım, tüm tahminlerden iyidir.
:::

:::ozet
- Önce eldeki makineyle dene; para, deneme "daha fazlasını istiyorum"
  dedirtirse anlamlı.
- Oyuncu GPU merdiveni: 12 GB giriş → 16 GB orta → 24 GB (2.el 3090, fiyat/perf
  şampiyonu) → 32 GB (5090, pahalı zirve). Ölçüt hep VRAM × bant.
- Apple: bellek bol, bant çip katmanına bağlı (base→Ultra: 120→819 GB/s);
  sessiz ve verimli, prefill zayıf karnı.
- 128 GB unified mini PC sınıfı (Strix Halo ~$2k) "evde büyük MoE" çağının
  en ucuz bileti; DGX Spark aynı sınıfın CUDA'lı, pahalı, geliştirici odaklı hâli.
- Fiyatlar (Tem 2026, kriz dönemi) dönemseldir; sınıf mantığı ve "bellek × bant"
  ölçütü kalıcıdır. Cihazı modele göre seç, modeli cihaza göre değil.
:::
