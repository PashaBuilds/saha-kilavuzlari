# Bölüm 12 — Pratik Kullanım Senaryoları

Model kurdun, API çalışıyor — peki bununla fiilen ne yapılır? Bu bölüm, lokal
LLM'in sahada en çok işe yaradığı beş senaryoyu gezer. Her birinde aynı iki
soruya cevap var: nasıl kurulur ve **hangi model sınıfı yeter?** (Sınıflar
Bölüm 11 tablolarının diliyle; "yeter" = işi görür, "iyi" = konfor.)

## 1. Kişisel asistan: günlük yazı-çizi işleri

En doğal başlangıç: özetleme, taslak yazma, çeviri, yeniden ifade etme,
beyin fırtınası, e-posta cilalama. Kurulumu Bölüm 8'de zaten yaptın —
Ollama + istersen üzerine Jan ya da Open WebUI. Buradaki asıl beceri model
beklentisi ayarıdır: bu işlerin çoğu dil akıcılığı ister, derin akıl yürütme
değil.

**Model sınıfı:** 7-14B yeter (Gemma 4 12B, Qwen3.5-9B); 27B+ iyi.
Keskin olgu bilgisi gerekiyorsa (tarihler, kişiler, teknik ayrıntı) küçük
modele güvenme — ya belgeyi ver (aşağıdaki RAG) ya da bu işi buluta bırak.

## 2. Kod yardımcısı: editörünün içinde

Lokal modelin en olgun profesyonel kullanımı. VS Code/JetBrains dünyasında
Continue, Cline gibi açık kaynak eklentiler; OpenAI-uyumlu her uca
bağlanabilen ajan araçları — hepsi `localhost`'a yönlendirilebilir. İki
kullanım katmanını ayır:

- **Satır içi tamamlama** (yazarken öneri): küçük ve hızlı model ister;
  gecikme her şeydir. 3-9B sınıfı (ya da A3B MoE'ler) idealdir.
- **Sohbet/ajan işleri** (açıkla, düzelt, dosya boyu değişiklik): kalite
  ister. 2026'nın yıldızları GLM-4.7-Flash ve Devstral 2 Small; 24 GB
  kartı olan Qwen3.6-27B ile de çok iyi yaşar.

**Model sınıfı:** tamamlama 3-9B; sohbet 27-35B yeter, 120B MoE sınıfı iyi.
Dürüst not: en zorlu "koca repoyu anla, çok adımlı değişiklik yap" ajan
işlerinde açık modeller frontier'ın hâlâ gerisindedir — hassas kod tabanında
lokal, gündelik işlerin; en kritik refactor'ların bulutun payı olabilir.

## 3. Doküman işleri ve RAG'e giriş penceresi

"Modele PDF'lerimi öğretmek istiyorum" isteğinin doğru tekniği fine-tuning
değil (Bölüm 9'daki tuzak), **RAG'dir (retrieval-augmented generation —
erişimle zenginleştirilmiş üretim).** Sezgisi üç adımdır:

1. Belgelerin parçalara bölünür; her parça bir **embedding modeliyle**
   (Bölüm 9) anlam vektörüne çevrilip bir vektör deposuna yazılır.
2. Soru geldiğinde o da vektöre çevrilir; deposundan **anlamca en yakın**
   parçalar bulunur (kelime eşleşmesi değil, anlam yakınlığı).
3. Bulunan parçalar + soru, LLM'in context'ine konur: "şu alıntılara
   dayanarak cevapla."

Model ezberden değil, önüne konan metinden konuşur — olgu doğruluğu ve
"kaynağı göster" ihtiyacı böyle çözülür. Hazır yaşamak için: Open WebUI'nin
doküman yükleme özelliği ve LM Studio'nun sohbete dosya ekleme özelliği,
küçük ölçekte bu akışı kutudan verir. Ciddileşince anahtar kelimeler:
LangChain/LlamaIndex, Chroma/Qdrant.

**Model sınıfı:** cevaplayıcı LLM 7-14B ile şaşırtıcı iyi (metin önünde!);
embedding için ayrı küçük model (0,1-1B sınıfı, ör. `nomic-embed-text`
Ollama'da tek komut). Uzun belgelerde asıl sınır context + KV cache
bütçendir (Bölüm 7).

## 4. Ajan ve otomasyon: LLM'i boru hattına takmak

API'nin (Bölüm 8) asıl meyvesi: LLM'i insan arayüzünden çıkarıp betiklerin
içine koymak. Gece çalışan bir cron işi gelen e-postaları etiketler; bir
betik indirilen makaleleri özetleyip arşive yazar; bir izleme aracı log'lardan
anormallik raporu çıkarır. **Tool calling / function calling** (modelin
"şu aracı şu parametrelerle çağır" diye yapılandırılmış çıktı üretmesi)
güncel instruct modellerin standart yeteneğidir ve ajan çatılarının temelidir.

Lokalin bu alandaki süper gücü **hacim ekonomisidir** — ve gizlilik:
e-posta/log gibi hassas akışlar makineden çıkmaz.

:::hesap Hacim ekonomisi: günde 10.000 özet
>> İş: günde 10.000 e-posta özeti; istek başına ~1.500 token giriş + 150 çıkış
>> API'de (tipik küçük model fiyatıyla, ~$0,20/M giriş + $0,80/M çıkış): (15M × 0,20 + 1,5M × 0,80) ÷ 1000 ≈ $4,2/gün ≈ $125/ay
>> Lokalde (3090, ~350W, günde ~3 saat yük, $0,15/kWh): 0,35 × 3 × 0,15 × 30 ≈ $4,7/ay elektrik
=> Aynı iş: ayda ~$125'a karşı ~$5 — hacim büyüdükçe makas açılır
Fiyatlar dönemseldir (Tem 2026 mertebeleri); kalıcı olan yapı: API maliyeti
hacimle lineer büyür, lokal maliyet sabite yakındır. Düşük hacimde tersi de
doğrudur — ayda yüz istek için donanım alınmaz.
:::

**Model sınıfı:** sınıflandırma/etiketleme/özet gibi dar işler 4-9B;
çok adımlı ajan akışları 27B+ ister, tool calling güvenilirliği için
gpt-oss-20b gibi reasoning-eğilimli modeller iyi bir orta yoldur.

## 5. Aile (ya da ekip) ChatGPT'si

Kılavuzun topolojik finali: evin bir köşesindeki tek makine, herkese hizmet
veren özel bir ChatGPT olur.

{{svg:21-aile-sunucusu.svg|Ev sunucusu topolojisi: model + Open WebUI tek makinede; laptoplar, telefonlar ve editör eklentileri ev ağı üzerinden aynı API'yi kullanır. Sohbetler evden çıkmaz.|wide}}

Kurulum iskeleti: (1) En güçlü makineye Ollama kur; ağdan erişim için
`OLLAMA_HOST=0.0.0.0` ayarla. (2) Üzerine Open WebUI kur (tek Docker
komutu); kullanıcı hesapları, model seçimi, doküman yükleme hazır gelir.
(3) Diğer cihazlar tarayıcıdan sunucunun ev-içi adresine bağlanır.
Eş zamanlı kullanıcı sayısı arttıkça Ollama'dan vLLM'e geçiş (Bölüm 7'deki
batch bahsi) sunucuya nefes aldırır.

**Model sınıfı:** 24 GB'lik bir kartla 27-35B sınıfı bütün aileye yeter;
128 GB unified makineyle gpt-oss-120b sınıfı "evde kurumsal asistan"
deneyimi verir.

:::tuzak
`0.0.0.0` ayarı API'yi **ağdaki herkese** açar — bunu yaptığın makine asla
doğrudan internete açık olmamalı (modem port yönlendirmesi yok!). Ollama'nın
API'sinde varsayılan kimlik doğrulama yoktur; internetten erişim gerekiyorsa
yol VPN'dir (Tailscale gibi araçlarla on dakikalık iş), API'yi dünyaya açmak
değil. Taranabilir açık Ollama sunucuları, güvenlik araştırmacılarının
bitmeyen eğlencesidir — listeye girme.
:::

:::saha-notu Senaryolar birleşir
Bu beş senaryo ayrı kurulumlar değildir; hepsi aynı API'nin müşterileridir.
Tipik olgun kurulum tek makinede şöyle görünür: Ollama iki model tutar
(27-35B genel + 4-9B hızlı işler), Open WebUI aileye sohbet verir, Continue
editöre bağlanır, üç cron betiği gece hacimli işleri öğütür. Modeli bir kez
seçersin, meyvesini her kanaldan yersin.
:::

:::ozet
- Kişisel asistan: 7-14B yeter; olgu işlerinde belge ver ya da buluta bırak.
- Kod: tamamlamaya küçük-hızlı (3-9B), sohbete 27-35B (GLM-Flash/Devstral/Qwen);
  en zorlu ajan işleri hâlâ frontier'ın alanı.
- "PDF'lerimi öğret" = RAG (embedding + vektör arama + context'e alıntı);
  fine-tuning değil. Open WebUI/LM Studio küçük ölçekte kutudan verir.
- Otomasyonda lokalin süper gücü hacim ekonomisi + gizlilik; tool calling
  güncel modellerde standart.
- Aile sunucusu: Ollama (0.0.0.0) + Open WebUI; internete açma, VPN kullan.
:::
