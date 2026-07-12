# Bölüm 14 — Sözlük ve Model Kartı Okuma Antrenmanı

Önce kılavuzun açılışındaki vaadi tahsil edelim. Şu ifadeyle başlamıştık:
**"26B-A4B Q4_K_M 128K"**. Artık her parçası konuşuyor:

- `26B` → toplam 26 milyar parametre (Bölüm 2); Q4 dosyası ≈ 26 × 0,6 ≈ 16 GB
  (Bölüm 4 formülü).
- `A4B` → MoE mimarisi, token başına ~4 milyar aktif parametre (Bölüm 3);
  bellek 26B'ye, hız 4B'ye bakar — 360 GB/s'lik bir kartta ~60-80 token/s
  beklersin (Bölüm 5).
- `Q4_K_M` → 4-bit k-quant, medium karışım; tatlı nokta quantization (Bölüm 4).
- `128K` → context penceresi 131.072 token (Bölüm 7); tamamını açarsan KV
  cache için ayrıca ~8-16 GB isteyeceğini de biliyorsun.

Tek satırlık bir künyeden dosya boyutu, donanım sınıfı, hız tahmini ve bellek
bütçesi çıkardın. Antrenmana devam: aşağıda üç gerçekçi model kartı özeti ve
adım adım okuması var; sonrasında alfabetik sözlük.

## Antrenman 1: orta sınıf MoE

```text
Qwen3.6-35B-A3B-Instruct
Architecture: MoE (hybrid thinking, multimodal)
Parameters: 35B total · ~3B active
Context: 262,144 tokens
License: Apache 2.0
Files: GGUF → Q4_K_M (22.1 GB), Q6_K (29.8 GB), Q8_0 (38.5 GB)
```

Okuma sırası (Bölüm 2'deki dört kontrol): **parametre** — 35B/3B: bellek 35'e,
hız 3'e göre; kalite beklentisi ~30B sınıfı, akıcılık küçük model gibi.
**Lisans** — Apache 2.0: ticari dahil serbest. **Context** — 262K: bol; ama
tamamını açmak KV cache'te onlarca GB demek, ihtiyacın kadarını aç.
**GGUF** — Q4_K_M 22 GB: 24 GB karta context payıyla ancak sığar (offload
gerekebilir); 32 GB+ Mac'te rahat. `Instruct` = sohbete hazır; "hybrid
thinking" = reasoning kipi açılıp kapanır (Bölüm 9). Karar: 24-48 GB
sınıfının dengeli günlük atı.

## Antrenman 2: quant satırı olmayan model

```text
gpt-oss-120b
Architecture: MoE
Parameters: 117B total · 5.1B active
Precision: native MXFP4 (~63 GB)
Context: 128K · License: Apache 2.0
```

Dikkat: "Files" bölümünde Q4/Q8 seçenekleri yok — model **baştan 4-bit
(MXFP4) eğitilmiş** (Bölüm 4 derin dalışı); 63 GB'lik dosya "orijinalin"
kendisi, quantization kaybı diye bir şey yok. 117B/5,1B: bellekte 80 GB
civarı ister (dosya + context payı) → 128 GB unified sınıfının işi;
hızı A5.1B sayesinde ~40-55 token/s. Kılavuz boyunca bu modelin neden
"128 GB sınıfının standardı" olduğunu artık üç sayıdan görebiliyorsun.

## Antrenman 3: tuzaklı kart

```text
NVIDIA-Nemotron-3-Super-120B-A12B-BF16
Architecture: Hybrid Mamba-Transformer MoE
Parameters: 120B total · ~12B active
Context: 1M tokens
License: NVIDIA Open Model License
```

Üç tuzak birden. (1) İsimdeki `BF16`: bu depo **ham 16-bit ağırlıklar** —
~240 GB; senin arayacağın GGUF quant'ları ayrı bir depoda (Bölüm 4:
topluluk quant'ları orijinalden türetilir; IQ4 sürümü ~65 GB). (2) Lisans
Apache/MIT değil, NVIDIA'nın kendi metni: genelde serbest ama ticari işte
o metni okumadan geçme (Bölüm 10). (3) "1M context" büyüleyici ama KV
bütçesi (Bölüm 7) 1M'de yüzlerce GB'ye koşar — pratikte bu kapasitenin
dilimlerini kullanırsın. Kart heyecanlı, okuma soğukkanlı: model 128 GB
unified sınıfına iyi bir aday, ama "1M context'li 240 GB'lik dev" olarak
değil, "IQ4'ü ~65 GB olan, uzun-context'te sınıfının en iyisi" olarak.

:::saha-notu Antrenmanı sürdürecek yerler
Kart okuma kası kullanıldıkça güçlenir. Düzenli uğrak üç yer: Hugging Face'in
"Trending" sekmesi (yeni kartları bu bölümün yöntemiyle sök), model
üreticilerinin duyuru sayfaları (ilk elden künye) ve r/LocalLLaMA
(sahadan token/s raporları — Bölüm 11 tablolarını tazelemenin ham verisi).
Her yeni kartta aynı dört adım: parametre → lisans → context → dosyalar.
:::

## Alfabetik sözlük

| Terim | Tanım |
|---|---|
| aktif parametre (A-B) | MoE'de bir token için fiilen hesaplanan parametre miktarı; hızı belirler (B3) |
| Apache 2.0 / MIT | Ticari dahil serbest kullanım veren iki yaygın lisans (B10) |
| attention | Modelin, yeni token üretirken önceki token'larla ilişki kurma mekanizması (B7) |
| bant genişliği | Belleğin işlemciye veri akıtma hızı (GB/s); token/s'in ana belirleyicisi (B5) |
| base model | Yalnızca ön eğitim görmüş ham tamamlama modeli; asistan değildir (B9) |
| batch | Birden çok isteğin aynı ağırlık okumasıyla birlikte işlenmesi (B7) |
| chat template | Diyaloğu modelin eğitildiği özel ayraç kalıbına saran şablon (B9) |
| compute-bound | Hızı işlem gücünün sınırladığı durum (prefill böyledir) (B7) |
| context window | Modelin tek seferde görebildiği azami token penceresi (B7) |
| decode | Cevabın token token üretildiği faz; bandwidth-bound (B7) |
| dense | Her token'ın tüm parametrelerden geçtiği klasik mimari (B3) |
| distillation | Büyük modelin çıktılarıyla küçük model eğitme; "damıtma" (B9) |
| embedding | Metni anlam taşıyan sayı vektörüne çevirme; RAG'in motoru (B9, B12) |
| expert | MoE'de router'ın seçtiği alt-ağ parçalarından her biri (B3) |
| fine-tuning | Hazır modeli kendi verinle ek eğitme (B9) |
| FP16 / BF16 | 16-bit "orijinal" ağırlık hassasiyeti; parametre başına 2 byte (B4) |
| GGUF | llama.cpp ekosisteminin tek dosyalık, quantize model formatı (B4) |
| GPU offload | Katmanların bir kısmını GPU'da, kalanını CPU/RAM'de çalıştırma (B5) |
| GQA | Grouped-query attention; KV cache'i küçülten yaygın mimari tercihi (B7) |
| halüsinasyon | Modelin özgüvenle yanlış bilgi üretmesi (B1) |
| Hugging Face | Açık modellerin dağıtıldığı merkezi depo (B2) |
| imatrix | Önem matrisiyle yönlendirilen, düşük bitte kayıp azaltan quant tekniği (B4) |
| instruct model | Talimat izlemek üzere SFT/RLHF görmüş asistan modeli (B9) |
| KV cache | Görülen token'ların attention verilerinin bellekte tutulması; context ile büyür (B7) |
| LoRA | Küçük ek matrislerle ucuz fine-tuning; "yama" dosyası üretir (B9) |
| MLX | Apple'ın Apple Silicon'a özel ML çatısı ve model formatı (B8) |
| MoE | Mixture of Experts; router + expert'lerden oluşan seyrek mimari (B3) |
| MTP | Multi-token prediction; tek adımda birden çok token üreten hızlandırıcı (B8) |
| open weights | Ağırlıkları indirilebilir ama eğitim verisi/kodu kapalı model (B10) |
| parametre (B) | Modelin öğrenilmiş sayıları; B = milyar (B1, B2) |
| perplexity | Modelin metin karşısındaki "şaşkınlık" ölçüsü; quant kalitesi kıyasında kullanılır (B4) |
| prefill | Prompt'un paralel işlendiği ilk faz; TTFT'yi belirler (B7) |
| quantization | Ağırlıkları daha az bitle temsil ederek küçültme (B4) |
| RAG | Belgelerden anlamca ilgili parçaları bulup context'e ekleyerek cevaplatma (B12) |
| reasoning model | Cevaptan önce görünür düşünme adımları üreten model (B3, B9) |
| RLHF | İnsan tercihine göre pekiştirmeli inceltme (B9) |
| router | MoE'de her token için hangi expert'lerin çalışacağını seçen bileşen (B3) |
| safetensors | Orijinal (genellikle FP16/BF16) ağırlıkların güvenli dosya formatı (B4) |
| SFT | Örnek diyaloglarla denetimli ince ayar (B9) |
| spekülatif decoding | Küçük taslak modelin önerilerini büyük modelin toplu doğrulaması (B8) |
| swap | Belleğe sığmayanın diske taşması; LLM'de felç demektir (B5) |
| temperature | Örnekleme cüreti ayarı; 0 = tutucu, yükseldikçe savruk (B1) |
| token | Modelin metin birimi; TR'de kelime başına ~2-3 (B1) |
| tokenizer | Metni token'lara bölen bileşen (B1) |
| tool calling | Modelin araç çağrısı için yapılandırılmış çıktı üretmesi (B12) |
| TTFT | Time to first token; ilk token'a kadar geçen süre, prefill'in ölçüsü (B7) |
| unified memory | CPU ve GPU'nun paylaştığı tek bellek havuzu (Apple, Strix Halo) (B5) |
| vLLM | Çok kullanıcılı, batch'li sunucu sınıfı çıkarım motoru (B8) |
| VRAM | Ayrık GPU'nun kendi yüksek bantlı belleği (B5) |

:::ozet
- "26B-A4B Q4_K_M 128K" artık dört bilgiye açılıyor: boyut+dosya, mimari+hız,
  quant düzeyi, context+KV bütçesi — vaat yerine geldi.
- Kart okuma refleksi: parametre (toplam/aktif) → lisans → context → dosyalar;
  isimdeki BF16/MXFP4 gibi ekler dosyanın "ham mı, hazır mı" olduğunu söyler.
- Şüpheli üç yer: quant deposunun ayrı olması, aile-dışı lisans metinleri,
  pazarlama parlaklığındaki dev context sayıları.
- Sözlük buradadır; kılavuzun geri kalanını unutmak serbest, "B + GB + token/s"
  üçgenini unutmak yasak.
:::
