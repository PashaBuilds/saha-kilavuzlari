# Bölüm 4 — Quantization: Sıkıştırma Sanatı

Bölüm 2'de hesapladık: 27B'lik bir modelin orijinal FP16 ağırlıkları 54 GB
tutar. Ev donanımının belleği buna yetmez — ve yetseydi bile, Bölüm 5'te
göreceğimiz gibi, bu boyut hızı süründürürdü. Lokal LLM dünyasını mümkün kılan
teknik tam burada devreye girer: **quantization (nicemleme — ağırlıkları daha
az bitle temsil etme).** Bu bölümün sonunda hem `Q4_K_M` gibi kodları
okuyabilecek hem de herhangi bir modelin dosya boyutunu kafadan tahmin
edebileceksin.

## Fikir: sayıları kabaca yuvarlamak

Her parametre bir ondalıklı sayıdır ve eğitimden FP16 (16 bit = 2 byte)
hassasiyetle çıkar: `-0.03742818...` gibi. Quantization bu sayıları daha kaba
bir cetvele yuvarlar — 8 bite, 4 bite, hatta 2 bite. Sayı başına bit azaldıkça
dosya küçülür; yuvarlama hatası büyüdükçe modelin "keskinliği" azalır.

{{svg:06-precision-cetveli.svg|Precision cetveli: parametre başına byte FP32'den Q2'ye doğru küçülür. Lokal kullanımın tatlı noktası Q4 civarıdır.|wide}}

Şaşırtıcı olan şu: LLM'ler bu kabalaştırmaya karşı **olağanüstü dayanıklıdır.**
Milyarlarca parametrenin her biri biraz yuvarlanınca hatalar büyük ölçüde
birbirini dengeler; Q8'de fark ölçüm cihazıyla bile zor bulunur, Q4'te günlük
kullanımda nadiren sezilir. Asıl kırılma Q3 altında başlar: Q2'ye inen model
hâlâ akıcı konuşur ama incelikli akıl yürütmede, keskin bilgide ve uzun
tutarlılıkta gözle görülür kayıp verir.

{{svg:07-quant-boyutlari.svg|Aynı 7B modelin farklı quant düzeylerinde dosya boyutu. Q8→Q4 arası "bedavaya yakın" küçülmedir; Q4 altı kaliteden yer.|wide}}

:::analoji
Quantization, fotoğrafı JPEG'e çevirmeye benzer. RAW (FP16) dosya devasadır;
kaliteli JPEG (Q8) onda birine iner ve farkı kimse görmez; agresif
sıkıştırılmış JPEG (Q4) hâlâ gayet iyi bir fotoğraftır; ama sıkıştırmayı
sonuna kadar zorlarsan (Q2) yüzler tanınmaz olmaya başlar. Ve tıpkı JPEG
gibi: bir kez sıkıştırılmış dosyayı geri açmak orijinali geri getirmez.
:::

## Kafadan boyut hesabı

Kılavuzun en çok kullanacağın formülü:

:::hesap Dosya boyutu kestirimi
>> dosya boyutu (GB) ≈ parametre (B) × bit ÷ 8 × 1,1
>> Q4_K_M fiilen ~4,5 bit kullanır; ×1,1 üstbilgi ve karışık katman payıdır
>> Örnek: 27B × 4,5 ÷ 8 × 1,1 ≈ 16,7 GB → gerçek dosya: ~17 GB ✓
>> Örnek: 8B × 4,5 ÷ 8 × 1,1 ≈ 5,0 GB → gerçek dosya: ~5 GB ✓
=> Ezber hâli: Q4'te GB ≈ B sayısının yarısı + biraz
Belleğe sığma hesabı bundan ibaret değil — çalışma anında context için ek
bellek gerekir (Bölüm 7'de KV cache) ve pratik kural Bölüm 5'te gelecek.
:::

<div class="calc" data-calc="boyut">
  <span class="calc-title">Canlı hesap: model boyutu kestirimi</span>
  <div class="calc-row">
    <label>Parametre (B):</label>
    <input type="number" name="param" value="27" min="0.1" step="0.1">
    <label>Quant:</label>
    <select name="quant">
      <option value="16">FP16 (16 bit)</option>
      <option value="8.5">Q8_0 (~8,5 bit)</option>
      <option value="6.6">Q6_K (~6,6 bit)</option>
      <option value="5.7">Q5_K_M (~5,7 bit)</option>
      <option value="4.5" selected>Q4_K_M (~4,5 bit)</option>
      <option value="3.4">Q3_K_M (~3,4 bit)</option>
      <option value="2.6">Q2_K (~2,6 bit)</option>
    </select>
  </div>
  <div class="calc-row">
    <span>Tahmini dosya: <span class="calc-out" data-out="dosya">—</span></span>
    <span>· Rahat çalışma için bellek: <span class="calc-out" data-out="bellek">—</span></span>
  </div>
  <p class="calc-note">Bellek tahmini, dosya + %20 çalışma payı + ~1,5 GB context içindir; kaba kestirimdir. MoE modellerde parametre alanına toplam sayıyı yaz.</p>
</div>

## GGUF: lokal dünyanın ortak kabı

Quantize edilmiş modeller ekosistemde neredeyse her zaman **GGUF** formatında
dolaşır (llama.cpp projesinin dosya formatı — Bölüm 8). GGUF tek dosyada her
şeyi taşır: quantize ağırlıklar, tokenizer sözlüğü, mimari bilgisi, sohbet
şablonu. İndir, motora göster, çalıştır. Hugging Face'te bir modelin
"orijinali" `safetensors` formatında durur; topluluk (Unsloth, Bartowski gibi
quant üreticileri ya da üreticinin kendisi) bunlardan GGUF setleri türetip
ayrı depolarda yayımlar.

Bir GGUF deposunda aynı modelin onlarca dosyası seni karşılar; ad kalıbını
söktüğünde hangisini indireceğin netleşir:

{{svg:08-gguf-anatomi.svg|GGUF dosya adı anatomisi: aile, boyut, eğitim aşaması, quantization düzeyi ve format. Q4_K_M kodunun açılımı sağ altta.|wide}}

Sık göreceğin düzeylerin saha rehberi:

| Kod | ~bit | 7B örneği | Ne zaman? |
|---|---|---|---|
| `Q8_0` | 8,5 | 7,7 GB | Bellek boldaysa; "kayıpsıza en yakın" |
| `Q6_K` | 6,6 | 5,9 GB | Titiz işler (kod, uzun akıl yürütme) için güvenli üst orta |
| `Q5_K_M` | 5,7 | 5,1 GB | Q4 ile Q6 arası denge noktası |
| `Q4_K_M` | 4,5 | 4,4 GB | **Varsayılan başlangıç** — kalite/boyut tatlı noktası |
| `Q3_K_M` | 3,4 | 3,5 GB | Bellek dardaysa; kayıp sezilmeye başlar |
| `Q2_K` | 2,6 | 2,8 GB | Son çare; "hiç çalışmamasından iyi" |

:::saha-notu
Karar felç olmasın: **Q4_K_M ile başla.** Bellek fazlası varsa Q6_K'ya çık;
sığmıyorsa bir küçük quant'a inmeden önce şunu dene: **bir boyut küçük modelin
Q4'ü, aynı modelin Q2'sinden neredeyse her zaman daha iyidir.** Örnek: 24 GB
belleğe 70B'nin Q2'sini zorlamak yerine 27-32B'nin Q4'ünü koy. İstisna, çok
büyük modellerde (Bölüm 11'deki 200B+ MoE sınıfı) özenle hazırlanmış dinamik
2-3 bit quant'lardır — onlar bu ezberin dışında değerlendirilir.
:::

:::tuzak
"Orijinal FP16'yı indireyim, en iyisi o" refleksi lokalde neredeyse her zaman
hatadır: 4 kat dosya, 4 kat bellek trafiği (= dörtte bir hız, Bölüm 5) ve
günlük kullanımda ayırt edilemeyecek kalite farkı. FP16 ağırlıkların yeri
eğitim/fine-tuning dünyasıdır. Bir de tersi tuzak var: sırf sığıyor diye
dev modelin Q1-Q2'sine balıklama atlamak — önce aynı bellekteki bir üst
sınıf Q4 alternatifiyle karşılaştır.
:::

:::derin-dalis Perplexity, imatrix, dinamik quant'lar ve diğer formatlar
Quant kalitesi **perplexity** ile ölçülür (modelin metin karşısındaki
"şaşkınlığı" — düşük olan iyidir); quant üreticileri Q4 dosyanın FP16'ya göre
perplexity artışını raporlar. **imatrix** (importance matrix) tekniği,
örnek metinlerle hangi ağırlıkların kritik olduğunu ölçüp yuvarlamayı ona
göre dağıtır — özellikle düşük bitlerde belirgin kazanç sağlar. **Unsloth
Dynamic (UD)** gibi güncel yaklaşımlar katman katman farklı bit derinliği
seçer; "UD-Q4_K_XL" gibi adlar taşıyan bu dosyalar çoğu zaman düz Q4'ten hem
küçük hem iyidir — depoda varsa onları tercih et. GGUF dışındaki adlar da
şunlardır: **AWQ/GPTQ** (GPU sunucu dünyasının 4-bit formatları, vLLM
tarafında yaşar), **MLX** (Apple'ın kendi formatı, Bölüm 8). Son eğilim:
üreticiler modeli baştan düşük hassasiyetle eğitiyor (gpt-oss'un MXFP4'ü,
native INT4 MoE'ler) — "quantization kaybı" kavramının kendisi eriyor,
çünkü 4-bit hâli orijinalin ta kendisi oluyor.
:::

:::ozet
- Quantization ağırlıkları daha az bitle yuvarlar; LLM'ler buna çok dayanıklı:
  Q8 farksız, Q4 tatlı nokta, Q2 son çare.
- Formül: **GB ≈ B × bit/8 × 1,1**; ezber: Q4'te GB ≈ B'nin yarısı + biraz.
- GGUF, lokal ekosistemin tek dosyalık kabı; ad kalıbı: aile-boyut-aşama-quant.
- Varsayılan seçim Q4_K_M; bellek varsa Q6_K; dara düşünce küçük modelin
  Q4'ü, büyük modelin Q2'sine genelde tercih edilir.
- FP16 lokal çıkarım için gereksiz yüktür; imatrix/dinamik (UD) quant'lar
  varsa düz karşılıklarına tercih edilir.
:::
