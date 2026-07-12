# Bölüm 11 — Büyük Tablo: Hangi Model Hangi Cihazda

Kılavuzun referans zirvesi. Önceki on bölümün bütün kavramları — B, MoE,
A'lı sayılar, Q4, bant genişliği, KV cache — burada iki tabloya ve bir
matrise damıtılıyor. Tarih damgası: **Temmuz 2026**; token/s değerleri
topluluk ölçümlerinden derlenmiş decode hızlarıdır (Bölüm 7), aralıklar
motor/quant/context farklarını yansıtır.

{{svg:20-uyum-matrisi.svg|Uyum matrisi: satırlar donanım sınıfı, sütunlar model sınıfı. Yeşil rahat bölge, sarı taviz isteyen sınır bölgesi. Yıldızlı not, MoE offload'un 24 GB kartlara açtığı sürpriz kapıyı anlatır.|wide}}

## Tablo A — Donanım katmanından bakış

"Elimde şu makine var, ne koşarım?" tablosu:

| Donanım sınıfı | Örnek cihaz | Kullanılabilir bellek | Rahat sınıf (Q4) | Örnek modeller | Beklenen hız | His |
|---|---|---|---|---|---|---|
| Giriş laptop | 8-16 GB RAM, GPU'suz | 4-10 GB | 3-9B dense | Phi-4-mini, Gemma 4 E4B, Qwen3.5-4B | 5-12 token/s | Yavaş ama çalışır; sabırlı yardımcı |
| Oyuncu PC alt | RTX 3060 12GB / 5060 Ti 16GB | 11-15 GB | 7-14B dense | Qwen3.5-9B, Gemma 4 12B, Phi-4, gpt-oss-20b (16GB) | 30-65 token/s | Akıcı; günlük işlerin atı |
| Oyuncu PC üst | RTX 3090/4090 24GB | ~23 GB | 27-35B dense + A3B MoE | Qwen3.6-27B (40-70 t/s), GLM-4.7-Flash, Gemma 4 26B-A4B | 40-120 token/s | Hızlı; "ciddi iş" katı |
| Mac orta | M4 Pro 48-64GB | ~34-45 GB | 14-32B + orta MoE | Qwen3.6-27B (~9-12 t/s), 35B-A3B (~40-60), GLM-4.7-Flash | 10-60 token/s | Akıcı (MoE'de), sessiz, 40W |
| Mac üst / AI mini PC | M4 Max 128GB, Strix Halo 128GB, DGX Spark | 96-112 GB | 70-120B MoE (+70B dense) | gpt-oss-120b (39-55 t/s), Nemotron Super 120B (~18), Mistral Small 4, Qwen3.5-122B-A10B, Llama 3.3 70B (~20 M4 Max) | 15-55 token/s | Sunucu hissi; "evde büyük model" |
| Çoklu GPU / istasyon | 2×24GB+, M3 Ultra, 256GB RAM sunucu | 48 GB VRAM / 256 GB+ havuz | 200-400B MoE quant | DeepSeek V4-Flash 284B-A13B, Qwen3.5-397B (MoE offload 25+ t/s), GLM-5.2 2-bit (~10 t/s) | 10-30 token/s | Frontier'e yakın; hobi eşiği aşılır |

Okuma notları: (1) MoE satırlarında hız, aktif parametreyle geldiği için
"boyuta göre şaşırtıcı yüksek"tir — 120B'lik gpt-oss'un 12B dense gibi akması
tasarım gereğidir. (2) "Beklenen hız" kısa-orta context içindir; 32K+
context'te prefill süresi (özellikle Mac/mini PC'lerde) ve KV cache maliyeti
devreye girer. (3) 2.el 3090, tablo boyunca fiyat/performansın referans
noktası olmayı sürdürüyor.

## Tablo B — Model tarafından bakış

"Şu modeli merak ediyorum, neyle koşar?" tablosu — 2026 ortasının en çok
konuşulan 13 açık modeli:

| Model | Parametre (toplam/aktif) | Mimari | Q4 boyutu | Asgari bellek | Tatlı nokta donanım | Lisans | Güçlü olduğu iş |
|---|---|---|---|---|---|---|---|
| Phi-4-mini | 3,8B | dense | ~2,5 GB | 6 GB | herhangi bir laptop | MIT | özet, sınıflandırma, 8GB makineler |
| Gemma 4 12B | 12B | dense | ~7,5 GB | 10 GB | 12-16GB GPU / 16GB Mac | Apache 2.0 | çok dilli sohbet, görüntü, genel iş |
| gpt-oss-20b | 21B / 3,6B | MoE (MXFP4) | ~13 GB | 16 GB | 16GB GPU / 24GB Mac | Apache 2.0 | reasoning, ajan; verimli orta boy |
| Gemma 4 26B-A4B | 26B / 4B | MoE | ~16 GB | 20 GB | 24GB GPU / 32GB Mac | Apache 2.0 | hızlı çok kipli genel iş |
| Qwen3.6-27B | 27B | dense | ~17 GB | 20 GB | 24GB GPU | Apache 2.0 | kod + genel; 24GB sınıfının tatlı noktası |
| GLM-4.7-Flash | 30B / 3,6B | MoE | ~18 GB | 22 GB | 24GB GPU / 32GB Mac | MIT | kod ve ajan; 30B sınıfının kralı |
| Qwen3.6-35B-A3B | 35B / 3B | MoE | ~22 GB | 26 GB | 24-32GB GPU / 48GB Mac | Apache 2.0 | hız/kalite dengesi; multimodal |
| gpt-oss-120b | 117B / 5,1B | MoE (MXFP4) | ~63 GB | 80 GB | 128GB unified sınıfı | Apache 2.0 | 128GB sınıfının standardı; reasoning |
| Mistral Small 4 | 119B / 6B | MoE | ~68 GB | 85 GB | 128GB unified | Apache 2.0 | metin+görüntü+kod tek modelde |
| Nemotron 3 Super | 120B / 12B | hibrit MoE | ~65 GB (IQ4) | 85 GB | 128GB unified | NVIDIA OML | 1M context, uzun doküman, ajan |
| Qwen3.5-122B-A10B | 122B / 10B | MoE | ~70 GB | 90 GB | 128GB unified | Apache 2.0 | büyük işlerin dengeli oyuncusu |
| DeepSeek V4-Flash | 284B / 13B | MoE | ~160 GB | 190 GB | 256GB istasyon; 24GB GPU + 256GB RAM offload | MIT | 1M context; frontier'e en yakın "ev" modeli |
| Kimi K2.7 Code | 1T / 32B | MoE (native INT4) | ~577 GB (2-bit ~325) | 240 GB (1-2 bit) | çoklu GPU / Mac kümesi | Modified MIT | ajan kodlama; açık frontier |

:::saha-notu Tablo eskidiğinde nasıl güncellenir?
Bu tabloların satırları eskir ama sütunları eskimez. Yeni bir model
duyduğunda aynı beş soruyu sor: toplam/aktif parametre? → Q4 boyutu
(B × 0,6) → asgari bellek (boyut + %20 + context) → token/s tahmini
(bant ÷ aktif × 0,6) → lisans. Beş cevap, modeli bu tablolardaki yerine
kendi elinle oturtur — kılavuzun asıl öğretmek istediği beceri buydu.
:::

## Dürüstlük kutusu: 1T sınıfı neden hâlâ ev dışı

Kimi K2.7 ya da DeepSeek V4-Pro gibi 1T sınıfı modeller "açık" ve teknik
olarak evde çalıştırılabilir — ama gerçekçi olalım. Q4 dosyaları yarım
terabayt; özenli 1-2 bit dinamik quant'larla bile 240-325 GB bellek
gerekir. Bu da ya 256GB+ RAM'li bir sunucu (~10 token/s, sabır işi) ya
birden çok 128GB makineyi ağda kümelemek (kurulum karmaşası) ya da
~$10.000+ donanım demektir. Çalışır; ama "ev kullanıcısının modeli"
değil, "meraklının Everest'i"dir. 2026'nın asıl kazanımı bu zirve değil,
bir alt kat: 128 GB'lik makinelerde akıcı çalışan 70-120B MoE sınıfının
iki yıl önceki frontier kaliteyi eve getirmesi.

Bir orta yol daha var: **açık modeli API'den kullanmak.** DeepSeek, GLM,
Kimi gibi modeller, üreticilerinin ya da üçüncü taraf sağlayıcıların
(OpenRouter benzeri toplayıcılar dahil) API'lerinden, kapalı muadillerinden
çok daha ucuza sunulur. Gizlilik avantajını kaybedersin ama açık ekosistemin
diğer meyvelerini (model çeşitliliği, fiyat rekabeti, istediğinde lokale
taşınabilirlik) korursun. "Günlük iş lokalde küçük model, ayda bir zor iş
API'de dev açık model" karışımı, 2026'da gayet aklı başında bir düzendir.

:::tuzak
Tablolardaki token/s değerlerini "garanti" okumak hayal kırıklığı üretir.
Aynı model + aynı donanımda hız; motora (llama.cpp/MLX/vLLM), quant'a,
context doluluğuna, hatta laptop'ın termal durumuna göre ±%50 oynar
(M4 Max'in 5 dakika yük sonrası hız düşürmesi belgelenmiş bir örnektir).
Aralıkların ortasını beklenti, alt ucunu plan varsayımı yap.
:::

:::ozet
- Uyum matrisi ezberi: 12-16GB → 7-14B; 24GB → 27-35B; 128GB unified →
  70-120B MoE; 256GB+ → 200-400B MoE; 1T = meraklı Everest'i.
- MoE çağında "kaç B koşarım?" sorusu ikiye ayrıldı: bellek toplamı,
  hız aktifi izler — 120B'lik model 12B gibi akabilir.
- Yeni model = beş soru: toplam/aktif → Q4 boyutu → asgari bellek →
  token/s → lisans. Tablolar eskir, bu beş soru eskimez.
- Değerler Temmuz 2026 damgalıdır; token/s aralıklarının alt ucuyla plan yap.
- Dev açık modelleri API'den kullanmak meşru bir orta yoldur: lokalin
  gizliliği gider, açık ekosistemin esnekliği kalır.
:::
