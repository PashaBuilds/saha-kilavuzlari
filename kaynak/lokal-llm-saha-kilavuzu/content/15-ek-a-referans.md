# Ek A — Hızlı Referans Kartı

Kılavuzun tamamı, tek ekranlık başvuru hâlinde. Yazdır, yer imle, yanında tut.

## Formüller

| Ne hesaplıyorsun? | Formül | Örnek |
|---|---|---|
| Dosya boyutu | GB ≈ B × bit ÷ 8 × 1,1 | 27B Q4: 27 × 4,5 ÷ 8 × 1,1 ≈ 17 GB |
| Q4 ezberi | GB ≈ B ÷ 2 + biraz | 8B → ~5 GB; 70B → ~40 GB |
| Rahat bellek | dosya × 1,2 + context payı | 17 GB model → ~22 GB (kısa ctx) |
| Kullanılabilir bellek | VRAM−1 · Mac RAM×0,7 · PC RAM−6 | 24 GB kart → 23; 48 GB Mac → 34 |
| Token hızı | token/s ≈ bant ÷ aktif GB × 0,6 | 936 ÷ 17 × 0,6 ≈ 33 t/s (3090+27B) |
| KV cache | (ctx ÷ 8K) × sınıf katsayısı | katsayı: 7-9B≈1 · 27-32B≈2 · 70B≈3 GB |

## Quantization cetveli

| Düzey | ~bit | Boyut çarpanı (×B) | Ne zaman? |
|---|---|---|---|
| FP16 | 16 | ×2,0 | lokal çıkarımda gereksiz |
| Q8_0 | 8,5 | ×1,1 | bellek bolsa; kayıpsıza en yakın |
| Q6_K | 6,6 | ×0,85 | titiz işler için güvenli üst |
| **Q4_K_M** | 4,5 | **×0,6** | **varsayılan başlangıç** |
| Q3_K_M | 3,4 | ×0,45 | dar bellek; kayıp sezilir |
| Q2_K | 2,6 | ×0,35 | son çare (büyük MoE'lerde UD 2-bit hariç) |

## Donanım sınıfı → model sınıfı

| Donanım | Rahat sınıf (Q4) | Beklenen his |
|---|---|---|
| 8-16 GB RAM (GPU'suz) | 3-9B | 5-12 t/s; sabırlı yardımcı |
| 12-16 GB GPU | 7-14B | 30-65 t/s; akıcı |
| 24-32 GB GPU | 27-35B (+A3B MoE) | 40-120 t/s; hızlı |
| 48-64 GB Mac / 2×GPU | 32B + orta MoE | 10-60 t/s; dengeli |
| 128 GB unified | 70-120B MoE | 15-55 t/s; evde büyük model |
| 256 GB+ | 200-400B MoE | 10-30 t/s; frontier'e yakın |

## Temel komutlar

```bash
# Ollama — günlük dörtlü
ollama pull <model>            # indir (tag ile quant seç: :27b-q4_K_M)
ollama run <model>             # çalıştır / sohbet
ollama list                    # diskteki modeller
ollama show <model>            # parametre, quant, context künyesi

# Ayarlar
OLLAMA_CONTEXT_LENGTH=32768    # context'i aç (varsayılana güvenme!)
OLLAMA_HOST=0.0.0.0            # ev ağına aç (internete DEĞİL)

# llama.cpp — çıplak motor
llama-server -m model.gguf -c 32768 --port 8080   # yerleşik WebUI ile sunucu
llama-cli -m model.gguf -p "..."                  # tek atımlık soru

# API testi (her motor, aynı kalıp)
curl http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"selam"}]}'
```

## Portlar ve adresler

| Araç | Varsayılan adres |
|---|---|
| Ollama | `localhost:11434` (OpenAI-uyumlu: `/v1`) |
| LM Studio | `localhost:1234` |
| llama-server | `localhost:8080` |
| Open WebUI | `localhost:3000` (Docker kurulumunda) |

## Beş soruluk model değerlendirme (yeni model çıktığında)

1. Toplam / aktif parametre? (bellek / hız kimden?)
2. Q4 boyutu ≈ B × 0,6 — belleğime sığar mı?
3. token/s ≈ bantım ÷ aktif boyut × 0,6 — bana yeter mi?
4. Lisans ticari işime uyuyor mu?
5. Kendi 5 görevlik testimde mevcut modelimi geçiyor mu?

## Sorun giderme kısa listesi

| Belirti | Muhtemel sebep → bölüm |
|---|---|
| İlk token'lar geldi, sonra taş kesildi | swap'a düştün → B5 |
| Uzun prompt'ta dakikalarca sessizlik | prefill/TTFT (özellikle Mac) → B7 |
| "Az önce söylediğimi unuttu" | context bütçesi/motor varsayılanı → B7, B8 |
| Uzun prompt'ta bellek hatası | KV cache taştı → B7 |
| Çıktıda `<|end|>` gibi artıklar | chat template sorunu → B9 |
| Soru sordum, soru üretti, susmuyor | yanlışlıkla base model indirdin → B9 |
| Model "bozuk" gibi kalitesiz | aşırı düşük quant (Q2) ya da yanlış tag → B4, B8 |
