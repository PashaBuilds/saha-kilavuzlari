# Bölüm 7 — Çıkarım Mekaniği: Prefill, Decode, KV Cache

Model belleğe sığdı, token/s tahminini de yaptın — ama sahada iki sürprizle
karşılaşacaksın: uzun bir doküman yapıştırdığında cevabın **başlaması** uzun
sürüyor; ve sorunsuz çalışan model, sohbet uzayınca ya yavaşlıyor ya "belleğim
doldu" diyor ya da az önce söylediğini unutuyor. İkisinin de açıklaması bu
bölümde: çıkarımın iki fazı ve KV cache.

## İki faz: önce oku, sonra yaz

Enter'a bastığın anda model cevabı hemen damlatmaya başlamaz. Önce prompt'un
tamamını "okur" — buna **prefill** denir. Prompt'taki token'lar birbirini
beklemek zorunda olmadığından bu faz **paralel** işlenir ve dar boğazı işlem
gücüdür (compute-bound). Sonra üretim başlar — **decode** fazı. Burada her
token bir öncekine bağlıdır, süreç mecburen **seridir** ve Bölüm 5'ten
bildiğin gibi dar boğaz bellek bandıdır (bandwidth-bound).

{{svg:13-prefill-decode.svg|Prefill: prompt'un tamamı paralel işlenir, işlem gücü belirler. Decode: cevap token token seri üretilir, bellek bandı belirler. İki faz, iki ayrı performans metriği demektir.|wide}}

İki faz, iki ayrı metrik doğurur ve cihazlar bu ikisinde farklı karakter
gösterir:

- **TTFT (time to first token — ilk token'a kadar geçen süre):** prefill'in
  hızı. NVIDIA GPU'ları ham işlem gücü sayesinde burada ezicidir; Apple
  Silicon'un bilinen zaafı buradadır — 30-50 sayfalık bir dokümanı M-serisi
  bir Mac'e verdiğinde ilk cevap onlarca saniye, uç durumlarda dakikalar
  sürebilir. Aynı doküman 4090'da birkaç saniyede yutulur.
- **token/s:** decode hızı, yani Bölüm 5 formülünün alanı. Burada bant
  genişliği konuşur; 819 GB/s'lik bir M3 Ultra, decode'da birçok GPU'yla
  boy ölçüşür.

Kısa prompt'lu sohbette TTFT'yi kimse fark etmez; uzun doküman/kod tabanı
işlerinde ise kullanıcı deneyimini TTFT belirler. Cihaz seçerken (Bölüm 6)
iş yüküne göre bu ikisini tartmalısın.

## KV cache: hafızanın bedeli

Decode sırasında model her yeni token için önceki **tüm** token'larla ilişki
kurar (attention). Bu ilişki hesabında her token'ın "anahtar" ve "değer"
vektörleri gerekir; bunları her seferinde baştan hesaplamak korkunç israf
olurdu. Çözüm: bir kez hesapla, bellekte sakla. Bu depoya **KV cache**
(key-value önbelleği) denir.

Bedava değildir: KV cache **context'teki her token için** yer kaplar ve
context uzadıkça lineer büyür. Bellek planındaki "ikinci kiracı" budur:

{{svg:14-kv-cache.svg|Aynı model, üç context boyutu: model dosyası sabit kalır, KV cache context ile büyür. 8 GB'lik kartta 5 GB'lik model 4K'da rahat, 128K'da belleğe sığmaz.|wide}}

:::hesap KV cache kaba maliyeti
>> kaba kural (fp16 KV, güncel GQA'lı modeller): her 8K token context başına…
>> 7-9B sınıfı ≈ 1 GB · 27-32B sınıfı ≈ 2 GB · 70B sınıfı ≈ 3 GB
>> Örnek: 27B modelle 64K context = 8 × 2 ≈ 16 GB — modelin kendisi (17 GB) kadar!
=> Bellek planı = model dosyası + (context/8K) × sınıf katsayısı + ~1 GB pay
Katsayılar mimariye göre değişir (GQA kafa sayısı, MLA, sliding window);
Q8 KV cache seçeneği bu maliyeti yarılar, kalite bedeli çoğu işte ihmal
edilebilir düzeydedir.
:::

<div class="calc" data-calc="kv">
  <span class="calc-title">Canlı hesap: KV cache kestirimi</span>
  <div class="calc-row">
    <label>Context (token):</label>
    <input type="number" name="ctx" value="32768" min="1024" step="1024">
    <label>Model sınıfı:</label>
    <select name="model">
      <option value="1" selected>7-9B (~1 GB / 8K)</option>
      <option value="2">27-32B (~2 GB / 8K)</option>
      <option value="3">70B (~3 GB / 8K)</option>
    </select>
  </div>
  <div class="calc-row">
    <span>Tahmini KV cache: <span class="calc-out" data-out="kv">—</span></span>
  </div>
  <p class="calc-note">fp16 KV varsayımıyla kaba kestirim; Q8 KV bunu yarılar. Motorlar genellikle context'i baştan rezerve eder — "kullanmadığım context de yer tutuyor" şaşkınlığının sebebi.</p>
</div>

:::tuzak
Klasik senaryo: "27B model 24 GB kartıma sığıyordu, 100 sayfalık PDF verdim,
bellek hatası aldım" — model sığdı, **context sığmadı.** İkinci klasik:
motorlar çoğu zaman context penceresini baştan ayırır; 128K açıp 2K
kullansan bile bellek 128K'ya göre gider. Kural: context'i ihtiyacın
kadar aç, "en büyüğü açayım ne olur ne olmaz" deme.
:::

## Context penceresi bir bütçedir

Model kartındaki "128K context" modelin görebileceği azami pencereyi söyler;
o pencerenin **nasıl harcandığı** ise senin elindedir. Pencereye sistem
promptu, verdiğin belgeler, sohbet geçmişi, son sorun ve — unutulan kalem —
modelin üreteceği cevabın payı birlikte sığmak zorundadır:

{{svg:15-context-butcesi.svg|Context bütçesi: sistem promptu + belgeler + birikimli sohbet geçmişi + soru + cevap payı. Pencere dolunca en eski mesajlar sessizce düşer — model onları artık hiç görmez.}}

"Az önce söylediğimi unuttu" şikâyetinin teknik karşılığı budur: pencere
dolmuş, arayüz en eski mesajları düşürmüştür. Model hata yapmıyor;
düşen mesajları **hiç görmüyor.** Uzun oturumlarda pratik çare, biriken
geçmişi ara ara özetletip taze pencereyle devam etmektir.

:::saha-notu Motorun gerçek context'i, modelin context'inden farklıdır
En sık yaşanan hayal kırıklığı: "128K'lık model kurdum ama 5 sayfa sonra
unutuyor." Sebep çoğu zaman motor ayarıdır — çalıştırıcılar belleği korumak
için varsayılanı düşük tutar. Ollama'nın güncel sürümleri context'i VRAM'e
göre kademelendirir (24 GB altı kartlarda varsayılan 4K'dır!); eski
sürümlerde varsayılan 2-4K'ydı. Modelin kapasitesini kullanmak için context'i
açıkça ayarla: Ollama'da `OLLAMA_CONTEXT_LENGTH` ya da ayarlar; LM Studio'da
model yükleme ekranındaki context alanı. Ve her artışın KV bedelini yukarıdaki
hesapla kontrol et.
:::

:::derin-dalis Batch: aynı anda birden çok istek
Tek kullanıcının decode'u bant genişliğiyle sınırlıdır; işlemci çoğu zaman
boş bekler. Peki aynı anda 8 istek gelirse? Motor, ağırlıkları bellekten
**bir kez** okuyup aynı turda 8 isteğin de birer token'ını üretebilir —
maliyet neredeyse aynı, üretim 8 kat. Buna **batching** denir. Tek kullanıcılı
lokal kurulumda önemi azdır; ama Bölüm 12'deki "aileye/ekibe sunucu" ve toplu
veri işleme senaryolarında vLLM gibi sunucu motorlarının (Bölüm 8) toplam
verimi (aggregate throughput) tek akış hızının 10-50 katına çıkarması bu
sayededir. Aynı ilke, spekülatif decoding ve MTP gibi hızlandırıcıların da
temelidir: madem bant başına bol boş hesap var, aynı okumayla birden çok
token "denenebilir".
:::

:::ozet
- Çıkarım iki fazdır: prefill (paralel, compute-bound) → TTFT'yi; decode
  (seri, bandwidth-bound) → token/s'yi belirler. GPU'lar prefill'de,
  yüksek bantlı her cihaz decode'da parlar.
- KV cache, görülen her token için büyür: kabaca 7-9B'de 1 GB, 27-32B'de
  2 GB, 70B'de 3 GB / her 8K context (fp16). Bellek planına dahil et.
- "Model sığdı, context sığmadı" ve "baştan rezerve edilen context" en sık
  iki bellek sürprizidir; pencereyi ihtiyaç kadar aç.
- Context bir bütçedir: sistem promptu + belgeler + geçmiş + soru + cevap payı.
  Dolunca eskiler sessizce düşer — "unutkanlık" bunun belirtisidir.
- Motor varsayılan context'i çoğu zaman modelden küçüktür; açıkça ayarla.
:::
