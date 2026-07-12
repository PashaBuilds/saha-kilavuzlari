# KICKOFF — lokal-llm-saha-kilavuzu

> Bu dosya, projenin tek başlangıç talimatıdır. Claude Code bu dosyayı okuyarak
> üretime başlar. Repo kökünde durur; CLAUDE.md bu dosyaya referans verir.

---

## 1. Proje Kimliği

- **Klasör / repo adı:** `lokal-llm-saha-kilavuzu`
- **Doküman adı:** *Lokal LLM Dünyası — Saha Kılavuzu*
- **Seri:** "Saha Kılavuzu" serisi (önceki üyeler: Bellek Mimarisi, RF Örnekleme,
  Ethernet). Aynı ruh: tek başına literatür oluşturacak kapsamda, pedagojik,
  "çok kaliteli bir blog okuyorum" hissi veren tek self-contained HTML.
- **Hedef kitle:** Yapay zekâyı sadece ChatGPT/Claude arayüzünden bilen, "kendi
  bilgisayarımda model çalıştırmak" fikrine yeni ısınan **teknik meraklı**.
  ML araştırmacısı değil; bilgisayarı olan, terminalden ürkmeyen, "hangi model
  benim makinemde döner ve neden" sorusunun cevabını arayan kişi.
- **Misyon:** Okuyan kişi bittiğinde şunları yapabilmeli:
  1. Bir model kartındaki "70B, MoE 26B-A4B, Q4_K_M, 128K context" ifadelerinin
     her parçasını okuyup çözebilmeli.
  2. Kendi donanımına bakıp hangi boyut/format modelin, kaç token/s civarında
     çalışacağını kabaca öngörebilmeli.
  3. Ollama veya LM Studio ile bir modeli indirip çalıştırabilmeli, OpenAI-uyumlu
     lokal API endpoint'i ayağa kaldırabilmeli.
  4. "Yeni model çıktı" haberini okuduğunda parametre sayısı, mimari ve lisansına
     bakıp kendisi için anlamlı olup olmadığına karar verebilmeli.
- **Dil:** Türkçe gövde; teknik terimler İngilizce korunur, ilk geçtiği yerde
  parantez içinde Türkçe açıklama verilir. Örn: "quantization (nicemleme —
  ağırlıkları daha az bitle temsil etme)". Kısaltmalar ilk kullanımda açılır.

---

## 2. Repo Yapısı

```
lokal-llm-saha-kilavuzu/
├── KICKOFF.md              ← bu dosya
├── CLAUDE.md               ← kısa yönlendirme: "KICKOFF.md'yi oku, kurallara uy"
├── content/                ← kaynak markdown, bölüm başına bir dosya
│   ├── 00-onsoz.md
│   ├── 01-llm-nedir.md
│   ├── ...
├── assets/
│   ├── svg/                ← el yapımı inline SVG şemalar
│   └── css/
│       └── kilavuz.css
├── build/
│   └── build.py            ← md → tek self-contained HTML derleyici
└── dist/
    └── index.html          ← ÇIKTI: tek dosya, bağımlılıksız, offline çalışır
```

**Kural:** `dist/index.html` tamamen self-contained: CSS inline, SVG inline,
JS minimum ve inline. CDN, harici font, internet bağımlılığı YOK.

---

## 3. Tasarım Sistemi

Önceki saha kılavuzlarıyla aynı görsel aile. "Teknik blog premium" hissi.

### 3.1 Tema ve Renk

- **Çift tema:** koyu (varsayılan) + açık; sağ üstte toggle,
  `prefers-color-scheme` ile başlar, tercih localStorage'a yazılır.
- Koyu tema paleti: zemin `#0E1116`, kart `#161B22`, gövde metin `#E6EDF3`,
  ikincil `#8B949E`, vurgu `#4DA3FF`, altın uyarı `#E8B84B`, yeşil `#5BB0A6`.
- SVG'ler CSS değişkenleri kullanmalı (`var(--ink)`, `var(--accent)`);
  SVG içinde hard-coded renk yasak — tema değişince şemalar da uyum sağlar.

### 3.2 Tipografi ve Yerleşim

- Gövde: sistem font stack'i, 16–18px, satır yüksekliği 1.7.
  Kod: `ui-monospace, SFMono, Consolas`.
- İçerik sütunu ~760px; şemalar ve büyük tablolar 900px'e taşabilir.
- **Sticky içindekiler:** geniş ekranda solda sabit TOC, aktif bölüm scroll'a
  göre vurgulanır. Dar ekranda üstte `<details>` içinde.
- Her H2 numaralı; başlıklarda hover'da kopyalanabilir anchor. Üstte okuma
  ilerleme çubuğu.

### 3.3 İçerik Bileşenleri

- `saha-notu` (altın): pratik, hemen uygulanabilir bilgi.
- `tuzak` (kırmızı): yaygın hata/yanılgı. Örn: "70B modeli 16GB RAM'e
  sığdırmaya çalışmak", "parametre sayısı = zekâ sanmak".
- `derin-dalis` (mavi, katlanabilir `<details>`): meraklısına derinlik;
  ana akış bunlar okunmadan da tamamlanabilmeli.
- `analoji` (yeşil): kavramı günlük hayattan benzetmeyle anlatan kutu.
- `komut` kutusu: kopyala butonlu kod bloğu (Ollama/llama.cpp komutları,
  Python istemci örnekleri, `nvidia-smi` çıktı okumaları).
- **Hesap kutusu** (`hesap` class): sayısal kestirim kutuları — "kaba VRAM
  hesabı", "token/s tahmini" gibi arka-zarf hesapları adım adım gösterir.
  Bu kılavuzun ayırt edici bileşeni; bolca kullanılmalı.

---

## 4. Görselleştirme Envanteri (ZORUNLU)

Her ana bölümde en az bir el yapımı SVG; toplamda **en az 20 şema**.
Şemalar anlatının taşıyıcısıdır, süs değil. Tüm şemalar inline SVG,
kütüphane yok; etiketler Türkçe, teknik alan adları İngilizce.
Her SVG'de `<title>` + altında `<figcaption>`.

| # | Şema | Bölüm |
|---|------|-------|
| 1 | LLM'in kuşbakışı çalışması: prompt → tokenizer → transformer katmanları → olasılık dağılımı → sonraki token (döngü oku ile) | LLM Nedir |
| 2 | Token kavramı: bir Türkçe + bir İngilizce cümlenin token'lara bölünmüş hali, renk kodlu | LLM Nedir |
| 3 | Parametre = ağırlık matrisleri: küçük bir katmanın matris görünümü, "7B = 7 milyar sayı" ölçek hissi | Model Anatomisi |
| 4 | Dense vs MoE mimari karşılaştırması: her token tüm ağdan geçiyor vs router + seçilen 2 expert (yan yana panel) | Mimariler |
| 5 | MoE bellek/hız paradoksu: "toplam parametre RAM'i belirler, aktif parametre hızı belirler" görsel denklemi | Mimariler |
| 6 | Precision cetveli: FP32 → FP16/BF16 → INT8 → Q4 → Q2; her seviyede byte/parametre ve kalite kaybı sezgisi | Quantization |
| 7 | Aynı 7B modelin FP16 / Q8 / Q4_K_M / Q2 boyutları — çubuk grafik + "hangi kaliteye mal oluyor" notu | Quantization |
| 8 | GGUF dosya adı anatomisi: `Qwen3.5-27B-Instruct-Q4_K_M.gguf` parçalara ayrılmış, her parça oklu açıklama | Formatlar |
| 9 | Bellek hiyerarşisi ve model yerleşimi: VRAM / unified memory / sistem RAM / disk — model nereye sığarsa oradan akar | Donanım |
| 10 | **Memory bandwidth = token hızı** ana şeması: her token üretimi tüm ağırlıkların okunması; GB/s → token/s ilişkisi | Donanım |
| 11 | GPU (ayrık VRAM) vs Apple Silicon (unified memory) vs CPU-only mimari karşılaştırması | Donanım |
| 12 | Prefill vs decode: prompt işleme (compute-bound, paralel) vs token üretme (bandwidth-bound, seri) iki fazlı zaman çizgisi | Çıkarım |
| 13 | KV cache büyümesi: context uzadıkça bellek tüketimi; "model sığdı ama context sığmadı" senaryosu | Çıkarım |
| 14 | Context window kavramı: kayan pencere, sistem promptu + geçmiş + cevap payı bütçelemesi | Çıkarım |
| 15 | Çıkarım motoru katman haritası: model dosyası → llama.cpp/MLX/vLLM → OpenAI-uyumlu API → istemci uygulamalar | Yazılım |
| 16 | Ollama akışı: `ollama pull` → blob store → `ollama run` → localhost:11434 API | Yazılım |
| 17 | Base → Instruct → Reasoning model evrimi: aynı gövde, farklı eğitim aşamaları (pretrain/SFT/RLHF) şeridi | Model Türleri |
| 18 | Cihaz-model uyum matrisi görseli: donanım katmanları (8GB→512GB) × model sınıfları ısı haritası | Cihaz Rehberi |
| 19 | Fiyat/bellek/bant genişliği üçgeninde popüler cihazların konumlanışı (RTX kartlar, Mac'ler, Strix Halo, DGX Spark) | Cihaz Rehberi |
| 20 | Lokal API mimarisi: tek makinede sunucu + ağdaki istemciler; "kendi ChatGPT'n" topolojisi | Kullanım |
| 21 | Karar ağacı: "hangi modeli seçmeliyim" — bellek → amaç (kod/sohbet/ajan) → dil → lisans akışı | Sentez |

---

## 5. İçindekiler (bölüm iskeleti)

Her bölüm: "neden umursamalısın" girişi → ana anlatı → şema(lar) →
saha notu/tuzak/hesap kutuları → 3-5 maddelik "bölüm özeti".

### Bölüm 0 — Önsöz: Neden Lokal?
Gizlilik, maliyet, çevrimdışı çalışma, sansürsüz deney, **compute sovereignty
(hesaplama egemenliği)** kavramı — kendi verinin ve aracının kontrolü.
Dürüst beklenti yönetimi: lokal model ≠ bedava Claude; nerede yeterli,
nerede değil. Okuma rotaları ("donanım almadan önce 5-8-9 oku" tarzı).

### Bölüm 1 — LLM Aslında Nedir?
Sonraki token tahmini; token/tokenizer kavramı (Türkçe'nin token verimliliği
notu); parametre ne demek; "model bir dosyadır" somutlaştırması —
diskteki GGUF dosyasının aslında milyarlarca sayı olduğu gerçeği.
Matematiğe girmeden, sezgi düzeyinde.

### Bölüm 2 — Model Anatomisi: Boyutlar ve İsimler
7B / 27B / 70B / 405B ne anlama gelir; model kartı okuma dersi
(Hugging Face sayfası anatomisi); parametre sayısı ≠ kalite tuzağı;
model aileleri ve sürümleme mantığı (aynı ailenin 4B'den 235B'ye ölçeklenmesi).

### Bölüm 3 — Mimariler: Dense ve MoE
Dense: her token tüm parametrelerden geçer. MoE (Mixture of Experts):
router + expert'ler, "26B-A4B" notasyonunun çözümü (toplam 26B, token başına
4B aktif). Kritik kavrayış: **MoE'de RAM ihtiyacını toplam, hızı aktif
parametre belirler** — lokal dünyada MoE'nin altın çağının sebebi.
`derin-dalis`: reasoning modelleri ve test-time compute; hybrid attention /
sliding window gibi KV tasarruf mimarilerine kısa pencere.

### Bölüm 4 — Quantization: Sıkıştırma Sanatı
Neden FP16 model evde çalışmaz; bit derinliği → dosya boyutu ilişkisi;
GGUF quant isimlendirmesi (Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3, Q2 — hangi durumda
hangisi); kalite kaybının gerçekte nasıl hissedildiği; **kaba kural hesap
kutusu:** `dosya boyutu ≈ parametre × bit/8 × 1.1`, ve "Q4'te GB ≈ B sayısının
yarısı + biraz" pratiği. `derin-dalis`: AWQ/GPTQ/MLX formatları, perplexity,
imatrix kavramına bir cümlelik dokunuşlar.

### Bölüm 5 — Donanım I: Bellek Her Şeydir
Kılavuzun kalbi. Modelin sığacağı yer: VRAM (ayrık GPU) / unified memory
(Apple, Strix Halo) / sistem RAM (CPU çıkarımı). **Memory bandwidth'in token
hızını belirlemesi** — her token için tüm aktif ağırlıklar okunur, dolayısıyla
`token/s ≈ bant genişliği / aktif model boyutu` kestirimi (hesap kutusuyla,
gerçek örnek sayılarla). CPU çıkarımının neden yavaş ama mümkün olduğu;
GPU offload kavramı (katmanların bir kısmı GPU'da, kalanı CPU'da).

### Bölüm 6 — Donanım II: Ne Alınır, Neyle Yetinilir
Sınıf sınıf: (a) eldeki laptop/PC — 8-16GB RAM ile neler döner;
(b) oyuncu GPU'ları — 12/16/24GB VRAM sınıfları (RTX 3060 12GB'dan 4090/5090'a),
ikinci el 3090'ın efsanevi fiyat/perf'i; (c) Apple Silicon — unified memory
avantajı, M-serisi bellek bant genişliği farkları (base/Pro/Max/Ultra);
(d) yeni nesil "AI mini PC" sınıfı — AMD Strix Halo (Ryzen AI Max+, 128GB),
NVIDIA DGX Spark; (e) çoklu GPU ve sunucu tarafına pencere.
Fiyat/bellek/bant genişliği üçgeni şeması. Elektrik/ısı/gürültü gerçekleri
saha notu.

### Bölüm 7 — Çıkarım Mekaniği: Prefill, Decode, KV Cache
Prompt işleme vs token üretme fazları; time-to-first-token vs token/s ayrımı;
KV cache nedir, context uzadıkça belleği nasıl yer (hesap kutusu: kaba KV
maliyeti); context window bütçelemesi; batch kavramına kısa dokunuş.
"Model yüklendi ama uzun promptta patladı" tuzağı burada çözülür.

### Bölüm 8 — Yazılım Katmanı: Motorlar ve Arayüzler
llama.cpp (ekosistemin temeli), Ollama (kolay başlangıç + API),
LM Studio (GUI + keşif), MLX (Apple yerlisi), vLLM/SGLang (sunucu sınıfı,
çok kullanıcı). Hangisi kime; hepsinin ortak paydası: **OpenAI-uyumlu API**.
Adım adım ilk kurulum: Ollama ile model indir, çalıştır, `curl` ile
localhost API'sine ilk istek. Open WebUI / Jan gibi sohbet arayüzlerine pencere.

### Bölüm 9 — Model Türleri ve Eğitim Aşamaları
Base vs Instruct vs Reasoning ("thinking") modeller; chat template kavramı;
SFT/RLHF'nin bir cümlelik sezgisi; embedding modelleri ve vision-language
(VLM) modellerine pencere; fine-tuning ve LoRA'nın ne olduğu (yapma rehberi
değil, kavram haritası); distillation kavramı ("büyük modelin küçüğe
öğretmesi").

### Bölüm 10 — Açık Model Ekosistemi: Kim Kimdir
Oyuncular ve aileleri (2026 ortası manzarası; **Claude Code: yazım sırasında
güncel sürümleri web'den teyit et, alan aylık değişiyor**):
Alibaba **Qwen** (3.x serisi, geniş boyut yelpazesi, Apache 2.0),
Zhipu **GLM** (5.x, kod/ajan gücü), Moonshot **Kimi** (K2.x, 1T sınıfı ajan
modelleri), **DeepSeek** (V3.x/V4, verimlilik okulu), Meta **Llama** (4 serisi,
community lisans), Google **Gemma** (4 serisi, küçük-orta sınıfın kralı),
**Mistral** (Large 3, Devstral), OpenAI **GPT-OSS**, Microsoft **Phi**
(küçük model okulu). "Open source vs open weights" dürüst ayrımı; lisans
okuma dersi (Apache 2.0 / MIT / community license farkları, ticari kullanım).

### Bölüm 11 — BÜYÜK TABLO: Hangi Model Hangi Cihazda
Kılavuzun referans zirvesi. İki ana tablo:

**Tablo A — Donanım katmanından bakış:**

| Donanım sınıfı | Örnek cihaz | Kullanılabilir bellek | Rahat çalışan sınıf (Q4) | Örnek modeller | Beklenen his |
|---|---|---|---|---|---|
| Giriş laptop | 8-16GB RAM, GPU'suz | 4-10GB | 3-8B dense | Phi-4-mini, Gemma 4 küçük, Qwen küçük | Yavaş ama kullanılabilir |
| Oyuncu PC alt | RTX 3060 12GB / 4060 Ti 16GB | 12-16GB VRAM | 7-14B dense | Qwen 14B, Gemma 4 12B, Devstral küçük | Akıcı |
| Oyuncu PC üst | RTX 3090/4090 24GB | 24GB VRAM | 27-32B dense / orta MoE | Qwen 3.x 27-32B, Gemma 4 26B-A4B | Hızlı |
| Mac orta | M4 24-48GB | ~16-36GB kullanılabilir | 14-32B + orta MoE | Qwen 27B, GPT-OSS küçük | Akıcı, sessiz |
| Mac üst / AI mini PC | M-Ultra 128-512GB, Strix Halo 128GB, DGX Spark | 96GB+ unified | 70B dense / büyük MoE | Llama 70B sınıfı, GPT-OSS 120B, orta Qwen MoE | Sunucu hissi |
| Çoklu GPU / iş istasyonu | 2×24GB+, sunucu | 48GB+ | 100B+ MoE quant | GLM/Qwen büyük MoE quantları | Frontier'e yakın |

(Tablo satırları örnektir; Claude Code güncel model sürümleriyle doldurup
genişletmeli — her satırda gerçekçi token/s aralığı da verilmeli.)

**Tablo B — Model tarafından bakış:** popüler ~12 açık model için:
parametre (toplam/aktif), mimari (dense/MoE), Q4 boyutu, asgari bellek,
tatlı nokta donanım, lisans, güçlü olduğu iş.

Ek olarak "1T sınıfı modeller neden hâlâ ev dışı" dürüst kutusu ve
API-üzerinden-açık-model (kendi sunucun olmadan açık model kullanmak)
seçeneğine bir paragraf.

### Bölüm 12 — Pratik Kullanım Senaryoları
Lokal modelle ne yapılır: kişisel asistan, kod yardımcısı (editör
entegrasyonları), doküman özetleme/RAG kavramına giriş penceresi
(embedding + vektör arama sezgisi), ajan/otomasyon kullanımı,
ev ağında herkese açık "aile ChatGPT'si" kurulumu. Her senaryoda
hangi model sınıfının yeterli olduğu notu.

### Bölüm 13 — SENTEZ: Kendi Kurulumunu Tasarla
Karar ağacı (şema #21) + üç örnek persona üzerinden uçtan uca reçete:
(a) "elimde sadece laptop var" → model + araç + beklenti;
(b) "orta bütçeyle kurulum yapacağım" → donanım + model seti;
(c) "ciddi bir lokal AI istasyonu istiyorum" → cihaz karşılaştırması + yazılım
yığını. Her reçetede kurulum komutları ve ilk test promptu.

### Bölüm 14 — Sözlük ve Model Kartı Okuma Antrenmanı
Alfabetik terimler sözlüğü + üç gerçek model kartı ekran-anatomisi üzerinden
"bunu artık okuyabiliyorsun" alıştırması.

### Ek A — Hızlı Referans Kartı
Tek ekran: quant tablosu (bit → boyut çarpanı), VRAM kestirim formülleri,
donanım sınıfı → model sınıfı özeti, temel Ollama/llama.cpp komutları.

---

## 6. Yazım Kuralları

1. **Pedagojik sıra:** hiçbir kavram tanımlanmadan kullanılmaz; bölümler
   birbirinin üstüne inşa edilir.
2. **Ton:** ciddi ama sıcak, ustadan çırağa. Hype yok — "devrim", "çığır"
   kelimeleri yasak; dürüst güçlü/zayıf yön anlatımı. Emoji yok.
3. **Her soyut kavrama somut karşılık:** analoji kutusu, gerçek komut çıktısı,
   gerçek dosya boyutu ya da hesap kutusu. Havada paragraf yasak.
4. **Sayılar gerçekçi ve tutarlı:** bellek hesapları, bant genişliği değerleri,
   token/s aralıkları kendi içinde tutarlı olmalı. Kesin bilinmeyen değer
   "yaklaşık/aralık" olarak verilir, uydurulmaz.
5. **Güncellik disiplini:** Bu alan aylık değişir. Model ve cihaz isimleri
   geçen bölümlerde (10, 11, 13) yazım öncesi web'den güncel sürümler teyit
   edilir; doküman başına "Son güncelleme: <tarih>, model manzarası hızla
   değişir" notu düşülür. Kavramsal bölümler (1-9) zamandan bağımsız yazılır —
   kılavuzun kalıcı değeri orada.
6. **Bölüm uzunluğu:** ana bölümler 800–1500 kelime; donanım bölümleri (5-6)
   ve büyük tablo bölümü (11) 2000 kelimeye çıkabilir.
7. **Komut örnekleri:** macOS ve Windows karşılıklarıyla; Python örnekleri
   stdlib + `openai` istemcisiyle sınırlı, kopyala-yapıştır çalışır halde.

---

## 7. Build Kuralları

- `build/build.py`: `content/*.md` → SVG göm → CSS inline → TOC üret →
  tek `dist/index.html`. Tercihen stdlib; markdown parser gerekirse tek
  dosyalık vendored çözüm.
- HTML çıktısı 2 MB altı hedef.
- JS bütçesi: tema toggle + TOC vurgusu + kod kopyala + progress bar +
  (opsiyonel) hesap kutularında canlı mini hesaplayıcı — örn. kullanıcı
  parametre sayısı ve quant seçince tahmini boyut/bellek gösteren küçük
  vanilla JS widget. Framework yok.

---

## 8. Üretim Akışı (Claude Code için)

1. Repo iskeletini kur, CLAUDE.md'yi yaz.
2. `kilavuz.css` temasını üret; boş bölümle uçtan uca build doğrula.
3. Bölüm 10-11 için web araştırması yap: güncel model sürümleri, cihaz
   fiyat/bellek/bant genişliği değerleri. Bulguları `content/_arastirma.md`
   notuna kaydet, tablolara oradan işle.
4. Bölümleri sırayla yaz (0→14, sonra ek). SVG'ler bölümle birlikte üretilir;
   "önce tüm metin sonra tüm şema" YAPMA.
5. Her 3-4 bölümde build alıp görsel kontrol: TOC, iki temada SVG okunurluğu,
   tablo taşmaları (Tablo A/B dar ekranda yatay scroll'lu olmalı).
6. Sentez (13) en son; önceki bölümlere geri referans verecek.
7. Son tur: terim tutarlılığı, çapraz linkler, sözlük derlemesi,
   hızlı referans kartı.

## 9. Kalite Çıtası (bitmiş sayılma kriterleri)

- [ ] `dist/index.html` çift tıklamayla, internetsiz kusursuz açılıyor
- [ ] En az 20 el yapımı SVG, iki temada da okunaklı
- [ ] Tablo A ve B dolu, güncel, satır başına token/s beklentisi içeriyor
- [ ] En az 8 hesap kutusu var (VRAM, boyut, token/s, KV cache kestirimleri)
- [ ] "26B-A4B Q4_K_M 128K" gibi bir ifade dokümanda adım adım çözülüyor
- [ ] Her bölümde en az bir saha-notu/tuzak kutusu
- [ ] Ollama ilk kurulum akışı kopyala-yapıştır çalışıyor
- [ ] Sözlük ve hızlı referans kartı tam
