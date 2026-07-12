# Bölüm 2 — Model Anatomisi: Boyutlar ve İsimler

Bölüm 1'de modelin milyarlarca sayıdan oluşan tek bir dosya olduğunu gördük.
Bu bölümde o "milyarlarca"nın nasıl anıldığını, model isimlerinin nasıl
söküldüğünü ve bir model kartını (model card — modelin künye sayfası) nasıl
okuyacağını öğreneceksin. Bölümün sonunda "Qwen3.6-27B-Instruct" gibi bir ismin
her parçası sana bir şey söylüyor olacak.

## Parametreler nerede durur: matrisler ve katmanlar

Parametreler dosyanın içinde rastgele bir yığın hâlinde durmaz;
**ağırlık matrisleri** (weight matrix — sayıların satır-sütun tabloları)
hâlinde örgütlenir. Her transformer katmanı birkaç büyük matristen oluşur;
model, token üretirken bu matrislerle art arda çarpma işlemi yapar. "Model
büyüdü" demek, hem matrislerin büyümesi hem katman sayısının artması demektir.

{{svg:03-parametre-matris.svg|Parametreler ağırlık matrislerinin hücreleridir; matrisler katmanları, katmanlar modeli oluşturur. 7B'nin ölçeği: FP16 kayıtta 14 GB'lik bir dosya.|wide}}

Şemanın sağındaki küçük hesap, kılavuzun bel kemiği olan formülün ilk hâli:
**dosya boyutu ≈ parametre sayısı × parametre başına byte.** FP16 (16 bit = 2
byte) kayıtta 7B model 14 GB, 27B model 54 GB, 70B model 140 GB eder. Bu
sayıların ev bilgisayarına sığmadığını fark etmişsindir — tam da bu yüzden
Bölüm 4'ün konusu olan quantization, lokal dünyanın olmazsa olmazıdır.

## Boyut sınıfları: sahada ne anlama gelir

Parametre sayıları sürekli bir cetvel olsa da pratikte model dünyası kabaca
sınıflara ayrılır. 2026 ortası itibarıyla saha karşılıkları şöyle:

| Sınıf | Tipik boyutlar | Sahada anlamı |
|---|---|---|
| Mini | 0,5–4B | Telefonda/8GB laptopta döner; özet, sınıflandırma, basit sohbet. Keskin bilgide zayıf. |
| Küçük | 7–14B | Lokal dünyanın giriş katı; 8–16GB bellekli makinelerde akıcı. Günlük işlerin çoğuna yeter. |
| Orta | 24–35B | "Ciddi iş" sınıfı; 24GB VRAM ya da 32GB+ Mac ister. Kod ve akıl yürütmede belirgin sıçrama. |
| Büyük | 70–120B | Tek tüketici GPU'suna sığmaz; 64–128GB unified memory ya da çoklu GPU işi. |
| Dev | 200B–1T+ | Frontier'e yakın açık modeller; 256GB+ bellek, çoğu evde "zar zor" ya da hiç. |

Sınırlar kesin değildir ve MoE mimarisi (Bölüm 3) bu tabloyu ilginç biçimde
büker — ama "kaç B, hangi sınıf, nasıl donanım" refleksi bu tabloyla başlar.
Bölüm 11'deki büyük tablo bunun ayrıntılı hâlidir.

## Model kartı okuma dersi

Açık modeller Hugging Face (açık model deposu — ekosistemin GitHub'ı)
üzerinden dağıtılır. Bir model sayfasında gözün şuraları taramalı:

1. **İsim:** çoğu bilgi ismin içindedir; birazdan sökeceğiz.
2. **Parametre sayısı ve mimari:** "27B dense" mi, "35B-A3B MoE" mi? (Bölüm 3)
3. **Context length:** modelin tek seferde işleyebildiği azami token (Bölüm 7).
4. **Lisans:** Apache 2.0 / MIT ise rahatsın; "community license" görürsen
   şartları oku (Bölüm 10).
5. **Files:** `safetensors` orijinal ağırlıklar (eğitim/sunucu dünyası);
   senin arayacağın çoğu zaman `GGUF` çevirileri (Bölüm 4) — genellikle
   "quantizations" bağlantısı altında ayrı depolarda durur.

Şimdi ismi sökelim:

```text
Qwen3.6-27B-Instruct
│    │  │   └── eğitim aşaması: talimat takip eden sohbet modeli (Bölüm 9)
│    │  └────── parametre sayısı: 27 milyar
│    └───────── aile içi nesil/sürüm: 3.6
└────────────── model ailesi (üretici: Alibaba)
```

Aynı kalıp hemen her ailede tekrar eder: `Gemma-4-12B-it` (it = instruction
tuned), `Phi-4-mini`, `Llama-3.3-70B-Instruct`. Bazı isimlerdeki ek kısaltmalar
sonraki bölümlerin konusu: `A4B` gibi ekler MoE aktif parametresini (Bölüm 3),
`Q4_K_M` gibi son ekler quantization düzeyini (Bölüm 4) anlatır. Kılavuzun
başındaki "26B-A4B Q4_K_M 128K" ifadesinin yarısını çözebilir hâle geldin bile.

:::saha-notu
Model kartında ilk bakılacak dört şey: **parametre (toplam ve varsa aktif) →
lisans → context → GGUF var mı?** Bu dördü 30 saniyede "benlik mi değil mi"
kararını verdirir. Benchmark tablolarına dalmadan önce bu dördü kontrol et.
:::

## Parametre sayısı ≠ kalite

Parametre sayısı kabaca kapasiteyi ölçer — ama kaliteyi tek başına belirlemez.
Aynı boyuttaki iki model arasında uçurum olabilir; dahası **yeni nesil küçük
model, eski nesil büyük modeli düzenli olarak geçer.** Bugünün iyi eğitilmiş
9B'si, üç yıl önceki 70B'nin yaptığı çoğu işi yapar. Sebepleri:

- **Veri kalitesi ve miktarı:** parametre kadar, o parametrelerin kaç trilyon
  token'la ve ne kalitede veriyle ayarlandığı önemlidir.
- **Distillation (damıtma):** büyük modelin davranışı küçüğe öğretilir;
  küçük model, boyutundan beklenmeyecek olgunlukta konuşur (Bölüm 9).
- **Eğitim tarifi:** aynı boyut, farklı tarif — bambaşka sonuç.

:::tuzak
"405B > 70B > 27B, o hâlde en büyüğü kurayım" akıl yürütmesi iki kez yanlıştır.
Birincisi: kalite sırası her iş için böyle değildir — kod için eğitilmiş bir
27B, genel amaçlı bir 70B'yi kod işinde geçebilir. İkincisi: donanımına
sığmayan ya da 2 token/s sürünen "daha iyi" model, pratikte akıcı çalışan
"daha küçük" modelden kötüdür. Doğru soru "en büyük hangisi?" değil,
"benim donanımda akıcı çalışan en iyi hangisi?" sorusudur.
:::

## Aileler ve sürümleme mantığı

Model üreticileri tek model değil **aile** yayımlar: aynı eğitim tarifinin
farklı boyutlara ölçeklenmiş üyeleri. Örneğin bir Qwen nesli 0,8B'den
400B'ye uzanan üyelerle çıkar; Gemma 4 ailesi 2B'den 31B'ye serilir. Bunun
sana faydası şudur: **ailenin küçük üyesiyle prototip kurar, gerekirse aynı
davranış diliyle büyük üyeye geçersin** — prompt'ların, şablonların çoğu
zaman aynen çalışır.

Sürüm numaraları (3 → 3.5 → 3.6) yeni eğitim turlarını anlatır; ara sürümler
bile kayda değer sıçramalar getirebilir. Aile içindeki ek etiketler de kalıba
oturur: `Instruct`/`it` sohbet için ayarlanmış demektir, `Base` ham tamamlama
modelidir (Bölüm 9'da ayrımı işleyeceğiz), `Coder`/`Devstral` gibi adlar işe
özel ayarı gösterir, `VL`/`Omni` görüntü-ses yeteneğine işaret eder.

:::derin-dalis Benchmark tablolarını nasıl okumalı?
Model kartlarında MMLU, GPQA, SWE-bench gibi kısaltmalarla dolu tablolar
görürsün — bunlar standart test setleridir (genel bilgi, bilimsel akıl
yürütme, gerçek yazılım hatası çözme gibi). İki uyarıyla yaklaş. Birincisi,
üretici tabloları en iyi göründüğü karşılaştırmayla kurar; bağımsız
sıralamalara da bak. İkincisi, benchmark'lar eğitim verisine sızabilir
("contamination") — parlak skor, senin işinde parlak performans garantisi
değildir. En sağlam test hâlâ şudur: kendi gerçek işinden 5-10 örnek hazırla,
aday modellere aynı örnekleri ver, çıktıları yan yana koy. Lokal dünyada bu
test bedava — Bölüm 8'de araçlarını kuracağız.
:::

:::ozet
- Parametreler ağırlık matrislerinde durur; dosya boyutu ≈ parametre ×
  parametre başına byte. FP16'da 7B ≈ 14 GB — quantization bu yüzden şart.
- Boyut sınıfları kabaca: 0,5–4B mini, 7–14B küçük, 24–35B orta, 70B+ büyük,
  200B+ dev. Her sınıfın donanım karşılığı Bölüm 11'de.
- Model kartında ilk dört kontrol: parametre, lisans, context, GGUF.
- İsim kalıbı: Aile + sürüm + boyut + eğitim aşaması (Instruct/Base/Coder…).
- Parametre sayısı kaliteyi tek başına belirlemez; "donanımımda akıcı çalışan
  en iyi" diye düşün, benchmark yerine kendi işinle test et.
:::
