# Araştırma Dosyası — Lokal LLM Manzarası (12 Temmuz 2026)

> Web araştırması dossier'i. Bölüm 10, 11, 12, 13 tabloları buradan beslenir.
> Fiyatlar USD ve Temmuz 2026 itibarıyla; bellek krizi nedeniyle oynak.
> ⚠️ işaretli değerler düşük güvenilirlikli, yayın öncesi teyit edilmeli.

## 1. Açık modeller (Temmuz 2026 güncel)

### Alibaba Qwen — lokal dünyanın varsayılan ailesi
- Qwen3 (Nis 2025): dense 0.6/1.7/4/8/14/32B + MoE 30B-A3B, 235B-A22B. Apache 2.0.
- Qwen3.5 (Şub 2026): dense 0.8/2/4/9/27B + MoE 35B-A3B, 122B-A10B, 397B-A17B. Apache 2.0, 256K ctx (YaRN ile 1M).
- Qwen3.6 (Nis 2026) — r/LocalLLaMA'nin fiilen kullandığı: Qwen3.6-27B (dense) ve Qwen3.6-35B-A3B (multimodal, hybrid sparse MoE). 262K ctx. Apache 2.0. Hybrid-thinking.
- MTP (multi-token prediction): llama.cpp Mayıs 2026'da native destek ekledi (PR #22673); ~1.4-2.2x hız. Qwen3.6-27B ~160 tok/s, 35B-A3B ~240 tok/s (RTX 6000 sınıfı, MTP ile).
- 4-bit boyutlar (Unsloth): 0.8B/2B ~3.5GB, 4B ~5.5GB, 9B ~6.5GB, 27B ~17GB, 35B-A3B ~22GB, 122B-A10B ~70GB, 397B-A17B ~214GB (UD-Q4_K_XL). 397B: 24GB GPU + 256GB RAM MoE offload ile 25+ tok/s.
- Ün: en iyi çok yönlü aile; Qwen3.6-27B "lokal geliştirme tatlı noktası".

### Zhipu / Z.ai GLM
- GLM-5 (11 Şub 2026): ~745B MoE. GLM-5.1 (27 Mar). GLM-5.2 (13 Haz 2026): 744B toplam / ~40B aktif, MIT lisans, 1M ctx, "IndexShare" sparse attention; SWE-bench Pro %62.1.
- GLM-5.2 BF16 ~1.51TB; Unsloth Dynamic 2-bit ~238GB (~%82 doğruluk), 256GB Mac'te çalışır.
- GLM-4.7-Flash: 30B-A3B MoE (~3.6B aktif), 200K ctx, 24GB'de çalışır; "30B sınıfının en güçlüsü", kodda çok iyi.
- ⚠️ "GLM-5-Air" (orta boy) bulunamadı — lokal GLM ya Flash (30B) ya dev (744B). HF'den teyit et.

### Moonshot Kimi ("evde 1T" ailesi)
- K2.5 (27 Oca 2026): 1T / 32B aktif MoE, multimodal (MoonViT), Modified MIT.
- K2.6 (20 Nis 2026): 1T / 32B aktif, 384 expert, 256K ctx; SWE-Bench Pro'da GPT-5.5 ile berabere (%58.6); "Agent Swarm".
- K2.7 Code (12 Haz 2026): aynı mimari, native INT4 MoE ağırlıkları + BF16 attention — Q8 GGUF (~595GB) Q4'ten (~577GB) sadece ~10GB büyük. Unsloth 2-bit ~325GB.
- Evde: Unsloth Dynamic 1-bit ~240GB (240GB VRAM/RAM'de >40 tok/s iddiası; 256GB RAM kutularda ~10 tok/s; 2-bit kod testlerini geçen en düşük quant).

### DeepSeek
- V4 ailesi (24 Nis 2026), MIT (⚠️ bir kaynak Apache 2.0 dedi — HF'den teyit): V4-Pro 1.6T / 49B aktif; V4-Flash 284B / 13B aktif; ikisi de 1M ctx, multimodal.
- V4-Flash 128-256GB makineler için pratik hedef; V4-Pro veri merkezi işi.
- R2: resmî olarak YOK (Haz 2026 itibarıyla). "32B dense, 4090'a sığar" spekülasyonu doğrulanmamış söylenti. Reasoning V4'ün modlarında.

### Meta Llama — lokal sahneden çekiliyor
- Llama 4 Scout (109B-A17B) & Maverick (400B-A17B, Nis 2025) son açık sürümler; Behemoth (~2T) rafa kalktı; 2026'da yeni Llama yok. Meta kapalı "Muse Spark"a döndü (8 Nis 2026, API-only); Llama 5 ("Avocado") ~2027. Llama 3.1/3.3 (8B/70B) ekosistem sayesinde hâlâ kullanılıyor ama topluluk Qwen/GLM/Gemma'ya geçti.

### Google Gemma 4
- 2 Nis 2026. Boyutlar: E2B (~2.3B etkin), E4B (~4.5B), 12B, 26B-A4B (MoE, 4B aktif), 31B dense. Multimodal, 140+ dil. Ctx: 128K (küçük), 256K (26B/31B). Lisans Apache 2.0'a geçti (büyük değişiklik).
- Ollama'nın Haziran 2026 MLX motoru Gemma 4'ü Apple Silicon'da MTP ile ~%90 hızlandırdı.

### Mistral
- Large 3 (2 Ara 2025): Batı'nın en büyük açık MoE'si, Apache 2.0. Medium 3.5 ve Small 4 (16 Mar 2026): Small 4 = 119B MoE / ~6B aktif (Magistral+Pixtral+Devstral birleşimi). Devstral 2 (devstral-2512) + Devstral Small 2 kod ajanları için. Açık sürümler Apache 2.0.

### OpenAI GPT-OSS
- gpt-oss-120b (117B / 5.1B aktif) ve gpt-oss-20b (21B / 3.6B aktif), 5 Ağu 2025, Apache 2.0, native MXFP4 (120B ~63GB; 20B 16GB'de çalışır). 128K ctx. v2 YOK (2026 ortası) — orijinal ağırlıklar güncel. 64-128GB makinelerde en çok çalıştırılanlardan.

### Microsoft Phi
- Phi-5 YOK. Phi-4 varyantları: Phi-4 (14B), Phi-4-mini (3.8B), Phi-4-multimodal, Phi-4-reasoning(+), Phi-4-reasoning-vision-15B (Mar 2026). MIT. Phi-4-mini "8GB RAM'de döner" seçeneği (~3.5GB Q4_K_M).

### Yeni/diğer önemli oyuncular
- NVIDIA Nemotron 3: Nano Omni 30B-A3B (Mamba2-Transformer hibrit MoE, video/ses/görüntü/metin) ve Super 120B-A12B (11 Mar 2026; LatentMoE Mamba-2, MTP, 1M ctx, NVFP4 ön-eğitim; NVIDIA Open Model License). Super 120B tek Strix Halo'da 18.4 tok/s (UD-IQ4_XS).
- IBM Granite 4.1: 3B/8B/30B hibrit (Mamba), Apache 2.0, 512K ctx, kurumsal/RAG odaklı.
- MiniMax M2.5 (Şub 2026) / M2.7 (Nis 2026): 230B / 10B aktif MoE, açık ağırlık, "Claude Sonnet sınıfı" ajan kodlama (M2.5 SWE-Bench Verified %80.2); Ollama'da.
- Tencent Hunyuan Hy3 (6 Tem 2026): 295B / 21B aktif MoE, Apache 2.0 (kısıtsız), reasoning/ajan, 256K ctx.
- Baidu ERNIE: 4.5 serisi açık (ERNIE-4.5-21B-A3B, Apache 2.0); Ernie 5.0/5.1 (May 2026) API-only.
- Ant Group Ling 2.5: 1T MoE, MLA hibrit attention.
- LG EXAONE 4.0: hibrit reasoning; lokalde niş.

### Q4_K_M GGUF boyut kuralı (~0.57-0.62 GB / B parametre)
4B ~2.5GB · 8-9B ~5-5.5GB · 12B ~7.5GB · 14B ~9GB · 27B ~17GB · GLM-4.7-Flash ~18-19GB · 32B ~20GB · Qwen 35B-A3B ~22GB · 70B ~40-43GB · gpt-oss-120b MXFP4 ~63GB · Qwen 122B-A10B ~70GB · Qwen3-235B-A22B ~130-135GB · Qwen3.5-397B UD-Q4_K_XL ~214GB · Kimi 1T Q4 ~577-605GB (2-bit ~325GB; 1-bit ~240GB) · GLM-5.2 2-bit ~238GB.

## 2. Donanım (2026 ortası)

### Bağlam: 2026 GPU/DRAM fiyat krizi
AI talebi bellek arzını kuruttu; RTX 50 fiyatları %15-20+ arttı, üretim H1 2026'da %20-40 kısıldı. Yüksek VRAM'li kartlar en çok etkilenen.

### NVIDIA tüketici GPU'ları (VRAM / bant genişliği / Tem 2026 sokak fiyatı)
| Kart | VRAM | Bant | Fiyat (Tem 2026) |
|---|---|---|---|
| RTX 3060 12GB | 12GB GDDR6 | 360 GB/s | ~$250-330 2.el ⚠️ |
| RTX 4060 Ti 16GB | 16GB GDDR6 | 288 GB/s (zayıf!) | ~$450-500 ⚠️ |
| RTX 5060 Ti 16GB | 16GB GDDR7 | 448 GB/s | $489-530+ (MSRP $429) |
| RTX 4070 / Super | 12GB | 504 GB/s | ~$550-650 ⚠️ |
| RTX 5070 | 12GB GDDR7 | 672 GB/s | ~$600-700 ⚠️ |
| RTX 5070 Ti | 16GB GDDR7 | 896 GB/s | $820-900 |
| RTX 4080 / Super | 16GB | 717/736 GB/s | ~$1,000+ ⚠️ |
| RTX 5080 | 16GB GDDR7 | 960 GB/s | ~$1,100-1,400 ⚠️ |
| RTX 3090 (2.el) | 24GB GDDR6X | 936 GB/s | $600-800 tipik |
| RTX 4090 | 24GB GDDR6X | 1,008 GB/s | sıfır ~$2,755; 2.el ort ~$2,270 |
| RTX 5090 | 32GB GDDR7 | 1,792 GB/s | ~$4,300+ (çıkış $1,999 idi!) |

Konsensüs: 2.el RTX 3090 hâlâ en iyi $/VRAM (24GB @ 936 GB/s, $600-800).

### Intel (ucuz VRAM'in karanlık atı)
- Arc Pro B60: 24GB, $600-800; 48GB çift-GPU ~$1,200.
- Arc Pro B70 (25 Mar 2026): 32GB VRAM, $949 — doğrudan lokal AI hedefli.

### Apple Silicon (unified memory / bant)
| Çip | Maks RAM | Bant |
|---|---|---|
| M4 | 32GB | 120 GB/s |
| M4 Pro | 64GB | 273 GB/s |
| M4 Max | 128GB | 410-546 GB/s |
| M3 Ultra (Studio) | 512GB opsiyonu Mar 2026'da kalktı (RAM krizi); şimdi 96GB'a kadar | 819 GB/s |
| M5 (base, 2025 sonu) | 32GB | ~153 GB/s |
| M5 Pro (2026) | 64GB ⚠️ | ~307 GB/s ⚠️ |
| M5 Max (2026) | 128GB | 460-614 GB/s |
| M5 Ultra (Studio) | 768GB'a kadar test edildi; Eki 2026 bekleniyor, ~$4,299+ | ~1.2TB/s bekleniyor ⚠️ |

- GPU varsayılan olarak unified memory'nin ~%70-75'ini kullanır (`iogpu.wired_limit_mb` ile artar); 128GB'de ~104-112GB kullanılabilir.
- M5 nesli: her GPU çekirdeğinde Neural Accelerator, M4 Max'a göre ~%28 daha yüksek tok/s; en büyük kazanç prefill'de.

### AMD Strix Halo (Ryzen AI Max+ 395)
- 128GB LPDDR5X-8000, 256-bit: teorik 256 GB/s, ölçülen ~215 GB/s (Linux). Radeon 8060S iGPU.
- Fiyat 2026 ortası: 128GB mini PC (GMKtec EVO-X2 vb.) ~$1,999-2,299; 64GB ~$1,499'dan. AMD resmî "Ryzen AI Halo" dev platformu $3,999.
- Gerçek dünya: gpt-oss-120B ~55 tok/s; Qwen3-30B-A3B sınıfı ~100 tok/s; Nemotron Super 120B ~18 tok/s; 235B sınıfı MoE düşük quant'ta yüklenebiliyor.
- Medusa Halo (Ryzen AI MAX 500, Zen 6 + RDNA 5, LPDDR6): ~460-690 GB/s sızıntısı, ama 2027.

### NVIDIA DGX Spark
- GB10, 128GB unified LPDDR5X @ 273 GB/s, ~240W, CUDA. Eki 2025'te $3,999; Şub 2026'da $4,699'a zam.
- Gerçek dünya: gpt-oss-120B MXFP4 → prefill ~1,723 tok/s, decode ~38.6 tok/s (decode Strix Halo'dan yavaş, prefill çok hızlı). Değerlendirme: CUDA + büyük unified memory + batch için iyi dev kutusu, tek akış decode zayıf.

## 3. Gerçek dünya performansı (decode, aksi belirtilmedikçe)

| Kombo | tok/s |
|---|---|
| 8B Q4_K_M @ RTX 3060 12GB | 42-65 (tipik ~50) |
| Qwen3.6-27B Q4 @ RTX 3090 | ~40 |
| Qwen3.6-27B Q4 @ RTX 4090 | ~70 (spekülatif decode ile 154) |
| Qwen 35B-A3B Q4 @ RTX 4090 | ~68-120 |
| RTX 5090, küçük-orta modeller | 140-240 |
| Llama-70B Q4 @ M4 Max 128GB | 19-22 (MLX), 17-19 (llama.cpp); laptop'ta 5 dk sonra termal ~10 |
| gpt-oss-120B @ M4 Max (MLX) | 40-50 raporlanan; 80-90 iddiası var ⚠️ (çelişkili — aralık ver) |
| gpt-oss-120B @ Strix Halo | ~55 |
| gpt-oss-120B @ DGX Spark | ~38.6 (prefill 1,723) |
| Nemotron Super 120B IQ4 @ Strix Halo | ~18.4 |
| Qwen3-30B-A3B sınıfı @ Strix Halo | ~100 |
| Kimi 1T @ M3 Ultra 512GB (tek) | ~5-15 (quant'a göre); 4×M3 Ultra küme ~28 |
| Kimi K2.5 1-bit (240GB) ≥240GB RAM+VRAM | ~10 (swap'a düşerse <2) |
| Qwen3.5-397B, 24GB GPU + 256GB RAM (MoE offload) | 25+ |
| DeepSeek 671B sınıfı @ M3 Ultra, uzun prompt | prefill ~14 dk sürebilir (prefill acısı) |

Prefill vs decode: prefill compute-bound, decode bandwidth-bound. Apple Silicon: bant yüksek, compute mütevazı → decode iyi, uzun promptta time-to-first-token acı verici (M5 Max 7B'de: prefill ~350-450 vs decode ~95-110 tok/s). NVIDIA prefill'de 1.5-2x+ önde. EXO 1.0: DGX Spark prefill + Mac Studio decode ayrıştırması ~4x hızlanma demosu.

## 4. Yazılım katmanı (2026 ortası)

- **Ollama** v0.30.x (v0.30.8, 12 Haz 2026): VRAM'e göre değişen varsayılan context (<24GiB → 4K; 24-48GiB → 32K; ≥48GiB → 256K); `OLLAMA_CONTEXT_LENGTH`; Apple Silicon'da MLX motoru (Gemma 4 MTP ile ~%90 hızlı); Windows ARM64; `ollama launch`; bulut model proxy'si. `localhost:11434`, OpenAI-uyumlu `/v1`.
- **llama.cpp**: yeni yerleşik WebUI (llama-server içinde); WebUI artık MCP host (lokal GGUF modeller MCP araçları çağırabiliyor); sunucudan dinamik model yükle/boşalt; Qwen3.6 için native MTP (May 2026).
- **LM Studio** 0.4.x (0.4.13, May 2026): birleşik multimodal MLX motoru; KV-cache checkpointing (%80'e kadar az ek RAM, uzun-context ajan döngülerinde 2x). `localhost:1234`.
- **MLX / mlx-lm**: Apple Silicon'da llama.cpp Metal'den %5-15 hızlı; Mac standardı.
- **vLLM**: çok kullanıcılı/prod self-hosting standardı; **SGLang** yakın, prefix-cache ağırlıklı ajan işlerinde %30-50 hızlı.
- **Open WebUI**: Ollama/OpenAI-uyumlu her backend üstüne standart ChatGPT-tarzı arayüz. **Jan**: açık kaynak masaüstü alternatifi.
- Portlar: Ollama :11434, LM Studio :1234, llama-server :8080; hepsi OpenAI-uyumlu /v1/chat/completions.

## 5. Kılavuz için temalar

1. **1T sınıfı açık modeller gerçek ve (zar zor) evde çalıştırılabilir.** Unsloth Dynamic 1-2 bit ile 240-325GB'ye iniyor → 256GB Mac'lerde ~10 tok/s. 2026'da evde FİİLEN çalıştırılanlar: gpt-oss-120b, Nemotron Super 120B-A12B, Mistral Small 4 (119B-A6B), Qwen3.5-122B-A10B, MiniMax M2.5, DeepSeek V4-Flash (128GB unified kutularda); GLM-4.7-Flash / Qwen3.6-35B-A3B / Gemma 4 26B-A4B (24-32GB GPU'larda). Dense >32B artık nadir — **2026 küçük-aktif-parametreli MoE'nin yılı.**
2. **Quant konvansiyonları:** Q4_K_M hâlâ varsayılan isim, ama topluluk standardı Unsloth Dynamic 2.0 (UD-Q4_K_XL) ve imatrix quant'lara (Bartowski) kaydı — UD-Q4_K_XL düz Q4'ten küçük ve daha iyi; imatrix düşük bitlerde en çok kazandırıyor.
3. **Native düşük hassasiyet eğitim geliyor:** gpt-oss MXFP4; Kimi K2.7 native INT4 MoE; Nemotron 3 NVFP4. "Quantization kaybı" laboratuvarlar 4-bit'te eğittikçe küçülüyor.
4. **KV cache:** modern modeller GQA/MLA kullanıyor, KV eskiye göre küçük — ama 256K-1M context'ler KV'yi yine bütçe kalemi yaptı. Kaba kural: 8B GQA model ~1-2GB KV @ 32K ctx (fp16), context ile lineer. Ollama'nın kademeli context varsayılanları bu yüzden.
5. **2026 donanım anlatısı:** (a) VRAM fiyatları patladı — 2.el 3090 ($600-800) ve Intel Arc Pro B60/B70 değer oyunları; (b) 128GB unified kutular (Strix Halo ~$2,000, M4/M5 Max, DGX Spark $4,699) "evde büyük MoE" katmanının varsayılanı; (c) artık kapasite değil bant genişliği konuşuluyor (215/273/546/614/819/1,792 GB/s merdiveni); (d) M5 Ultra Studio (768GB) Eki 2026 bekleniyor.
6. **Meta'nın geri çekilişi** ile açık ekosistemin lideri Çinli laboratuvarlar (Qwen, DeepSeek, Zhipu, Moonshot, MiniMax, Tencent) + OpenAI gpt-oss (tek seferlik) + Google Gemma + Mistral + NVIDIA/IBM.

### Tablo B için 12+1 model kısa listesi
Qwen3.6-27B · Qwen3.6-35B-A3B · Qwen3.5-122B-A10B · GLM-4.7-Flash (30B-A3B) · GLM-5.2 (744B-A40B) · Kimi K2.7 (1T-A32B) · DeepSeek V4-Flash (284B-A13B) · gpt-oss-20b · gpt-oss-120b · Gemma 4 26B-A4B · Mistral Small 4 (119B-A6B) · Nemotron 3 Super (120B-A12B) · Phi-4-mini ("8GB laptop" girişi).

### Editör uyarıları
- Tem 2026 fiyatları oynak (bellek krizi) — her fiyata tarih damgası koy.
- M4 Max gpt-oss-120b tok/s çelişkili (40-50 vs 80-90; muhtemelen llama.cpp vs MLX farkı) — aralık olarak ver.
- DeepSeek V4 lisansı (MIT vs Apache 2.0) ve "GLM-5-Air" varlığı yayın öncesi HF'den teyit edilmeli.
