# Bölüm 9 — Model Türleri ve Eğitim Aşamaları

Model depolarında aynı ismin `Base`, `Instruct`, `Thinking` gibi eklerle
çoğaldığını; ayrıca "embedding modeli", "VLM", "LoRA", "distill" gibi
terimlerin dolaştığını göreceksin. Bu bölüm, tür haritasını çıkarır —
hangisini ne zaman indirmelisin sorusunun bölümüdür. (Bunlar "nasıl model
eğitilir" dersi değil, tüketici gözüyle kavram haritasıdır.)

## Üç aşama: Base → Instruct → Reasoning

{{svg:18-egitim-asamalari.svg|Aynı gövdenin üç eğitim durağı: ham tamamlayıcı base, asistanlaşmış instruct, adım adım düşünmeye ödüllenmiş reasoning. İndirilenlerin ezici çoğunluğu instruct'tır.|wide}}

**Base (taban) model**, ön eğitimden (pretraining) çıkmış hâldir: trilyonlarca
token üzerinde yalnızca "sıradaki token'ı tahmin et" oynamıştır. Sohbet etmeyi
bilmez; soruya cevap vermek yerine metni istatistiksel olarak "sürdürür".
Fine-tuning yapacak araştırmacılar için hammaddedir, son kullanıcı için
değildir.

**Instruct model**, base'in üstüne iki inceltme katmanı almıştır. **SFT**
(supervised fine-tuning): on binlerce örnek diyalogla "soruya böyle cevap
verilir" öğretilir. **RLHF** (insan geri bildirimiyle pekiştirmeli öğrenme):
insanların beğendiği cevap tarzı ödüllendirilerek üslup cilalanır. Sonuç,
bildiğimiz asistan davranışıdır. İndirdiğin modellerin ezici çoğunluğu budur.

**Reasoning model**, instruct'ın üstüne bir tur daha alır: doğrulanabilir
problemlerde (matematik, kod, mantık) "adım adım düşünüp doğru sonuca varınca
ödül" ile eğitilir. Cevaptan önce görünür bir düşünme bölümü üretir
(Bölüm 3'teki derin dalışta bedelini konuşmuştuk: bol ekstra token = süre).
2026 itibarıyla yaygın kalıp **hibrit** modeldir: aynı model, istekte
`/think` gibi bir anahtar ya da API parametresiyle düşünme kipini açıp kapar.

:::saha-notu
İndirme anındaki pratik kural: isimde `Instruct`/`it`/`chat` yoksa ve model
adı çıplaksa (`Qwen3.6-27B` gibi), kartı dikkatle oku — bazı aileler çıplak
adı instruct için, bazıları base için kullanır. Yanlışlıkla base indirmenin
belirtisi meşhurdur: model soruna cevap vermek yerine sorunu andıran metinler
üretir, kendi kendine soru-cevap uydurur, durmayı bilmez. "Model bozuk"
değildir; ham tamamlayıcı indirmişsindir.
:::

## Chat template: diyaloğun görünmez ambalajı

Model aslında hâlâ tek şey yapıyor: token dizisini sürdürmek. "Sohbet" hissi,
mesajların özel ayraç token'larıyla paketlenmesinden doğar. Buna **chat
template** denir; kabaca şöyle görünür:

```text
<|system|>Kısa cevap ver.<|end|>
<|user|>Başkent neresi?<|end|>
<|assistant|>
```

Model bu kalıpla eğitilmiştir; `<|assistant|>` işaretinden sonrasını
"asistanın cevabı" olarak sürdürür. Her ailenin şablonu farklıdır ama
neyse ki bu dert senin değil: GGUF dosyası şablonu içinde taşır ve Ollama /
LM Studio gibi araçlar otomatik uygular. Bilmenin faydası teşhistedir —
çıktının içinde `<|end|>` gibi tuhaf işaretler görürsen ya da model hiç
susmuyorsa, sorun neredeyse her zaman yanlış/eksik chat template'tir.

## Pencere: metin dışına açılan türler

- **Embedding modelleri** sohbet etmez; metni anlamını temsil eden bir sayı
  vektörüne çevirir. "Anlamca benzer metinleri bulma"nın motorudur —
  Bölüm 12'de RAG kurarken başrolde. Küçüktürler (0,1–8B) ve LLM'in yanında
  ikinci model olarak çalışırlar.
- **VLM'ler (vision-language model)** görüntü de alır: ekran görüntüsü,
  fotoğraf, grafik yorumlar. Model kartında `VL`/`Vision`/`Omni` ekiyle
  gezerler; 2026 ailelerinin çoğu orta boydan itibaren multimodal (çok
  kipli) geliyor. Bellek planında görüntü işleme katmanının küçük ek
  maliyeti dışında kural aynıdır.

## Fine-tuning, LoRA, distillation: kavram haritası

**Fine-tuning** (ince ayar), hazır modeli kendi verinle bir tur daha eğitmektir:
kurum jargonu, özel format, dar alan bilgisi. Tam fine-tuning tüm parametreleri
günceller — pahalıdır. **LoRA** (low-rank adaptation) ise ağırlıkların yanına
küçük ek matrisler iliştirip yalnız onları eğitir: maliyetin kesri, sonuç çoğu
işte yeterli; çıktısı da modelin yanına takılan megabaytlarca küçük bir "yama"
dosyasıdır. Sahada duyacağın cümle bu yüzden "70B'yi eğittim" değil, "70B'ye
LoRA taktım" olur.

**Distillation** (damıtma) tersi yönde çalışır: büyük "öğretmen" modelin
çıktıları, küçük "öğrenci" modele eğitim verisi olur; küçük model boyundan
büyük konuşmayı öğrenir. Bölüm 2'deki "yeni nesil küçük, eski nesil büyüğü
döver" gözleminin ardındaki tekniklerden biri budur; model kartlarında
"distilled from …" ibaresiyle gezer.

:::tuzak
"Kendi verimle fine-tune edeyim de model şirketimi öğrensin" ilk bakışta
cazip, pratikte çoğu zaman yanlış ilk hamledir. Bilgi güncellemek için
fine-tuning kötü bir araçtır — model olguları güvenilir biçimde "ezberlemez",
üstüne mevcut yeteneklerini de bozabilirsin (catastrophic forgetting).
Bilgi işi için önce RAG'i dene (belgeyi context'e ver — Bölüm 12); fine-tuning'i
**davranış/üslup/format** öğretmek için sakla. Kural: bilgi → context,
davranış → fine-tuning.
:::

:::derin-dalis Uzmanlaşmış türevler ve "abliterated" modeller
Depolarda bir ailenin resmî üyeleri dışında topluluk türevleri de gezer.
`Coder`/`Devstral` gibi işe özel resmî türevler, o alanın verisiyle ek
eğitim almıştır ve alanlarında genel modeli geçer. Topluluk merge'leri
(birden çok modelin ağırlık ortalaması) ve "abliterated/uncensored" türevler
(reddetme davranışı ağırlık cerrahisiyle sökülmüş modeller) ise kalite
açısından kumardır: benchmark'ta parlayıp gerçek işte tutarsızlaşabilirler.
Başlangıçta resmî instruct sürümlerde kal; türevlere merak, kendi test
setinle (Bölüm 2'deki tavsiye) sınayarak gidilir.
:::

:::ozet
- Üç aşama: Base (ham tamamlayıcı) → SFT/RLHF ile Instruct (asistan) →
  reasoning RL ile düşünen model. Günlük kullanım için Instruct indirilir;
  2026'da reasoning çoğu modelde açılıp kapanan bir kiptir.
- Sohbet, chat template denen ambalajın eseridir; GGUF taşır, motor uygular.
  Çıktıda ayraç token'ları görmek = şablon sorunu.
- Embedding modelleri anlam vektörü üretir (RAG'in motoru); VLM'ler görüntü
  anlar.
- LoRA = ucuz, yamalı fine-tuning; distillation = büyükten küçüğe öğretme.
- Bilgi → context/RAG, davranış → fine-tuning; bilgiyi modele "ezberletme".
:::
