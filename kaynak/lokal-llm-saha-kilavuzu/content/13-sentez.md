# Bölüm 13 — Sentez: Kendi Kurulumunu Tasarla

On üç bölümün bilgisi tek karara akıyor: **senin** makinene, **senin** işine
uygun kurulum. Önce karar ağacı, sonra üç gerçek persona üzerinden uçtan uca
reçeteler. Reçetelerdeki model adları Temmuz 2026'nındır; süreç (bellek
hesabı → sınıf seçimi → kurulum → test) her dönemde aynen çalışır.

{{svg:22-karar-agaci.svg|Karar ağacı: önce kullanılabilir bellek (Bölüm 5 hesabı), sonra amaç, sonra dil ve lisans kontrolleri. Kararsızlıkta 20 dakikalık yan yana test her tartışmayı bitirir.|wide}}

## Reçete A — "Elimde sadece laptop var"

**Profil:** 16 GB RAM'li sıradan bir laptop (M-serisi MacBook Air ya da
GPU'suz Windows makine). Bütçe: 0 TL. Beklenti: lokal LLM'i tanımak, günlük
yazı-çizi ve özet işleri.

**Bellek hesabı (Bölüm 5):** Mac'te 16 × 0,7 ≈ 11 GB; Windows'ta 16 − 6 ≈
10 GB kullanılabilir. Hedef sınıf: 9-12B Q4 (~6-7,5 GB) — context payıyla
rahat sığar.

```bash
# macOS
brew install ollama
ollama run gemma4:12b        # ~7,5 GB; ilk indirme birkaç dakika

# Windows (PowerShell)
winget install Ollama.Ollama
ollama run gemma4:12b
```

Hız beklentisi: Apple Silicon'da ~15-25, DDR5 CPU'da ~7-10 token/s (Bölüm 5
formülü). Arayüz istersen üzerine Jan ya da LM Studio kur; ikisi de aynı
modeli kullanabilir.

**İlk test promptu** (modelin karakterini 2 dakikada gösterir):

```text
Şu üç cümleyi tek paragraf hâlinde, daha akıcı Türkçeyle birleştir ve
ardından 3 maddelik bir özet çıkar: [kendi metninden üç cümle yapıştır]
```

Kabul kriteri: akıcı Türkçe + talimatın iki parçasını da yapması. Bunu
geçiyorsa özet/taslak/çeviri işlerin için hazırsın; geçemiyorsa
`qwen3.5:9b` ile aynı testi tekrarla (Bölüm 2: kendi işinle test).

## Reçete B — "Orta bütçeyle kurulum yapacağım"

**Profil:** Mevcut masaüstü PC + ~$700-900 bütçe. Beklenti: akıcı kod
yardımcısı + aile sohbet sunucusu; günlük ciddi kullanım.

**Donanım (Bölüm 6):** ikinci el RTX 3090 (24 GB, 936 GB/s, ~$700). PSU'nun
850W+ olduğunu kontrol et; kart üç yuva kaplar. Alternatif: bütçe $500 ise
RTX 5060 Ti 16 GB (sınıf bir küçülür: 14B/20b modeller).

**Yazılım yığını (Bölüm 8+12):**

```bash
# 1) Motor + modeller
ollama pull qwen3.6:27b           # genel iş atı, ~17 GB
ollama pull glm-4.7-flash          # kod/ajan, ~18 GB (tag'i depodan doğrula)
ollama pull qwen3.5:4b             # hızlı küçük işler

# 2) Context'i ciddi işe göre aç (Bölüm 7)
setx OLLAMA_CONTEXT_LENGTH 32768   # Windows; macOS/Linux: launchctl/env

# 3) Aile arayüzü (Docker ile Open WebUI)
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

Editöre bağlamak için VS Code'a Continue eklentisini kur, model olarak
`glm-4.7-flash`'ı göster. Hız beklentisi: 27B dense ~40 token/s; A3B MoE
~80-120 token/s. KV bütçeni unutma: 27B + 32K context ≈ 17 + 8 = 25 GB
sınırı zorlar — uzun context işinde MoE modele geç (22 GB + küçük KV).

**İlk test promptu** (kod tarafı):

```text
Şu Python fonksiyonunu oku, bir hata var, bul ve düzeltilmiş hâlini yaz;
sonra iki satırlık test öner: [50-100 satırlık gerçek kodundan bir parça]
```

Kabul kriteri: hatayı bulması + çalışır düzeltme + makul test. 20 dakika
içinde GLM-Flash ve Qwen-27B'ye aynı beş görevi verip kazananı seç.

## Reçete C — "Ciddi bir lokal AI istasyonu istiyorum"

**Profil:** ~$2.000-4.500 bütçe, hedef "evde büyük model": 100B+ MoE sınıfı,
uzun dokümanlar, ajan deneyleri, ailece kullanım.

**Donanım kararı (Bölüm 6 haritası):** üç aday, üç karakter —

- **Strix Halo 128 GB mini PC (~$2.000):** fiyat/bellek şampiyonu;
  gpt-oss-120b ~55 token/s. Linux/kurcalama toleransı ister.
- **M4 Max 128 GB Mac Studio (~$4.000):** en yüksek bant (546 GB/s), sessiz,
  MLX ekosistemi; prefill GPU'lardan yavaş (Bölüm 7).
- **DGX Spark ($4.700):** CUDA gerekiyorsa (fine-tuning, görüntü modelleri)
  tek gerekçesi bu; salt sohbet hızı için değmez.

**Yazılım (Strix Halo/Mac ortak iskelet):**

```bash
ollama pull gpt-oss:120b           # ~63 GB; 128 GB sınıfının standardı
ollama pull qwen3.6:35b-a3b        # hızlı günlük işler için yanına
OLLAMA_HOST=0.0.0.0 ollama serve   # ev ağına aç (Bölüm 12 güvenlik notu!)
```

Üzerine Open WebUI (Reçete B'deki komut) ve istersen embedding modeli
(`ollama pull nomic-embed-text`) ile doküman/RAG akışı. Çok kullanıcılı
yoğun kullanımda vLLM'e geçiş yolunu Bölüm 8'den hatırla.

**İlk test promptu** (büyük model farkını gösterir):

```text
Ekte 30 sayfalık bir rapor var [yapıştır ya da WebUI'den dosya yükle].
1) Yönetici özeti çıkar (5 madde). 2) Rapordaki en zayıf üç argümanı
gerekçeleriyle eleştir. 3) Verilere dayanarak sorulmamış ama sorulması
gereken iki soru öner.
```

Kabul kriteri: ikinci ve üçüncü maddelerde "özetin ötesine geçen" gerçek
akıl yürütme. 120B MoE'nin 12B'den farkı tam bu tür işlerde görünür —
ve prefill süresini de ilk elden ölçmüş olursun.

:::saha-notu Kurulumun bakımı
Üç aylık ritim yeter: (1) r/LocalLLaMA ya da HF trendlerinden "benim
sınıfımda yeni ne var?" diye bak (Bölüm 11'deki beş soruyla değerlendir).
(2) Motoru güncelle — motor güncellemeleri bedava hız getirir (MTP gibi;
Bölüm 8). (3) Eski modelleri temizle: `ollama list` → `ollama rm` —
her biri onlarca GB disk. Modeli sırf "yeni çıktı" diye değiştirme;
kendi 5 görevlik testinde kazanamayan yeniliğin hükmü yok.
:::

:::ozet
- Süreç her dönem aynı: kullanılabilir bellek → sınıf → amaç → dil/lisans
  → 20 dakikalık yan yana test.
- Reçete A (0 TL): eldeki 16 GB laptop + Gemma 4 12B — lokal LLM'i tanı.
- Reçete B (~$700): 2.el 3090 + Qwen-27B/GLM-Flash — kod + aile sunucusu.
- Reçete C ($2-4,5k): 128 GB unified (Strix Halo / M4 Max) + gpt-oss-120b —
  evde büyük model.
- Bakım ritmi: üç ayda bir model manzarası + motor güncellemesi; testi
  geçemeyen yenilik alınmaz.
:::
