# Bölüm 1 — LLM Aslında Nedir?

Donanım ve model seçimine girmeden önce elimizdeki şeyin ne olduğunu netleştirmemiz
gerekiyor, çünkü sonraki her bölüm bu bölümün üstüne kurulacak: modelin neden
gigabaytlarca yer kapladığı, hızın neden bellekle sınırlandığı, context'in neden
dolduğu — hepsi LLM'in çalışma biçiminin doğrudan sonuçları. İyi haber: bu çalışma
biçimi, matematiğine hiç girmeden, sezgisel olarak anlaşılabilir.

## Tek numara: sıradaki token'ı tahmin etmek

Bir LLM (Large Language Model — büyük dil modeli), özünde tek bir iş yapan devasa
bir tahmin makinesidir: eldeki metne bakıp **sıradaki parçanın ne olacağını**
kestirmek. Telefonundaki klavyenin kelime önerisini bilirsin; LLM aynı fikrin
uç noktasına taşınmış hâlidir. Fark ölçekte ve derinliktedir: klavye önerisi son
birkaç kelimeye bakar, LLM ise binlerce kelimelik bağlamın tamamına bakar ve bu
bağlamı milyarlarca sayıdan geçirerek çok daha isabetli bir tahmin üretir.

{{svg:01-llm-kusbakisi.svg|LLM'in üretim döngüsü: metin token'lara çevrilir, transformer katmanlarından geçer, model bir olasılık dağılımı üretir, bir token seçilir ve metnin sonuna eklenir. Cevap bitene kadar bu döngü döner.|wide}}

Şemadaki döngü, kılavuz boyunca döneceğimiz en önemli gerçeği içeriyor:
**model cevabı tek hamlede üretmez; her seferinde tek token üretir** ve her
token için tüm ağın hesabı baştan yapılır. "Model saniyede kaç token üretiyor"
(token/s) ölçüsünün, yani lokal LLM dünyasının bir numaralı performans metriğinin
kaynağı budur. Bölüm 5'te bu döngünün donanımda neye mal olduğunu hesaplayacağız.

:::analoji
LLM'i, milyonlarca kitap okumuş ama elinde hiçbir kitap bulunmayan bir
"cümle tamamlama ustası" gibi düşün. Ona bir metnin başını verirsin; okuduğu
her şeyden damıttığı sezgiyle en makul devamı söyler. Ansiklopedi gibi sayfa
açıp bakmaz — o sayfaların izleri ustalığının içinde erimiştir. Bu yüzden çoğu
zaman isabetlidir ama kaynak gösteremez ve arada gayet özgüvenli biçimde yanılır.
:::

## Token: modelin harfleri, heceleri, kelimeleri

Model metni bizim gibi harf harf ya da kelime kelime görmez. Metin önce
**tokenizer** (metin bölücü) adlı bir bileşenden geçer ve **token** denen
parçalara ayrılır. Token bazen tam bir kelimedir, bazen bir kelime parçası,
bazen tek bir karakter ya da noktalama işaretidir. Her token'ın modelin
sözlüğünde bir numarası vardır; model aslında metinle değil, bu numara
dizileriyle çalışır.

{{svg:02-token-bolunmesi.svg|Aynı anlamdaki cümlenin İngilizce ve Türkçe token bölünmesi. Türkçe'nin ek yapısı, kelimeleri birden çok token'a böler.}}

Kaba ezber değerleri şöyle: İngilizce'de 1 token ortalama 4 karakter ya da
0,75 kelimedir — yani 100 kelimelik bir İngilizce paragraf ~130 token eder.
Türkçe'de durum farklıdır: dilimiz eklemeli olduğu ve çoğu tokenizer ağırlıklı
İngilizce metinle eğitildiği için **bir Türkçe kelime çoğu zaman 2–3 token'a**
bölünür. Bunun iki pratik sonucu var:

- Aynı içerik Türkçe'de daha fazla token tutar; context penceresi (Bölüm 7)
  daha hızlı dolar.
- token/s cinsinden aynı hızda çalışan bir model, Türkçe üretirken göze
  "kelime başına daha yavaş" görünür — saniyede 20 token, İngilizce'de ~15
  kelime ama Türkçe'de ~8-10 kelime demektir.

:::hesap 8K token'lık context kaç kelime taşır?
>> İngilizce: 8.192 token × ~0,75 kelime/token ≈ 6.100 kelime
>> Türkçe: 8.192 token ÷ ~2 token/kelime ≈ 4.100 kelime
=> Aynı pencere, Türkçe metinde kabaca üçte bir daha az yer taşır
Kesin oran tokenizer'a göre değişir (Qwen ve Gemma gibi çok dilli aileler
Türkçe'yi daha verimli böler); büyüklük sırası hesabı için bu yeterli.
:::

## Parametre: ustalığın saklandığı sayılar

Peki şemadaki "transformer katmanları" kutusunun içinde ne var? Milyarlarca
**parametre** (parameter — modelin eğitim sırasında öğrenilmiş sayısal
ağırlıkları). Her parametre tek bir ondalıklı sayıdır; "7B model" dendiğinde
kastedilen, 7 milyar (B = billion) böyle sayının bir arada çalışmasıdır.
Eğitim sırasında model trilyonlarca token okur ve bu sayılar azar azar ayarlanır;
"öğrenilen" her şey — dil bilgisi, dünya bilgisi, kod yazma alışkanlıkları —
bu sayıların değerlerinde saklıdır. Bölüm 2'de bu sayıların matrislere nasıl
dizildiğine daha yakından bakacağız.

## Model bir dosyadır

Bu kılavuzun en somutlaştırıcı gerçeği şu: indirdiğin model, diskte duran
**tek bir dosyadır** ve bu dosyanın içeriği neredeyse tamamen o milyarlarca
parametredir. Örneğin:

```text
~/.ollama/models/ …               # Ollama'nın model deposu
Qwen3.6-27B-Instruct-Q4_K_M.gguf  # ~17 GB — 27 milyar sayı, sıkıştırılmış
Phi-4-mini-Q4_K_M.gguf            # ~2,5 GB — 3,8 milyar sayı
```

Dosyanın içinde sihir yok: başta kısa bir üstbilgi (mimari, tokenizer sözlüğü,
ayarlar), ardından gigabaytlarca ağırlık verisi. Bu yüzden "modeli çalıştırmak"
demek, bu dosyayı belleğe yükleyip her token için o sayılarla dev bir hesap
yapmak demektir — Bölüm 5'in ana konusu olan "model belleğe sığıyor mu?"
sorusunun kökeni budur. Dosya boyutunun parametre sayısıyla ilişkisini de
Bölüm 4'te (quantization) formüle bağlayacağız.

:::tuzak
LLM'i bilgi veritabanı sanmak, yeni başlayanların en pahalı yanılgısıdır.
Model bilgiyi kayıt olarak tutmaz; olasılık sezgisi olarak tutar. Bu yüzden
emin görünerek yanlış bilgi üretebilir (halüsinasyon). Lokal modellerde bu
eğilim küçük modellere doğru belirginleşir: 4B'lik bir model akıcı Türkçe
konuşur ama tarih, isim, sayı gibi keskin olgularda sık çuvallar. Olgu
doğruluğu kritikse modele kaynak metni ver (Bölüm 12'deki RAG yaklaşımı)
ya da çıktıyı doğrulat.
:::

:::derin-dalis Aynı prompt'a neden hep aynı cevap gelmiyor?
Şemadaki son adım "olasılıklardan biri örneklenir" diyordu; işte ayar oradadır.
**Temperature (sıcaklık)** örneklemenin cüretini belirler: 0'a yaklaştıkça model
hep en yüksek olasılıklı token'ı seçer (deterministik, tutarlı, ama monoton);
yükseldikçe düşük olasılıklı token'lara da şans tanır (yaratıcı, ama savruk).
`top_p` ve `top_k` gibi ayarlar da aday listesini budar. Lokal çalıştırmanın
güzelliği: bu ayarlar tamamen senin elindedir — kod üretiminde 0,2'ye çekmek,
beyin fırtınasında 0,9'a çıkarmak gibi işe göre oynayabilirsin. Bulut
arayüzlerinde bu vanaların çoğu senin adına sabitlenmiştir.
:::

:::saha-notu
İlerideki bölümlerde geçecek üç ölçü birimini şimdiden cebe koy:
**B** = milyar parametre (model büyüklüğü), **GB** = dosyanın/belleğin boyutu,
**token/s** = üretim hızı. Lokal LLM seçiminin tamamı bu üç sayının
etrafında döner: B belleği belirler, bellek ve bant genişliği token/s'yi
belirler. Bu zinciri Bölüm 4 ve 5 adım adım kuracak.
:::

:::ozet
- LLM tek iş yapar: bağlama bakıp sıradaki token'ı tahmin eder; cevaplar bu
  döngünün token token dönmesiyle oluşur — hız ölçüsü bu yüzden token/s'dir.
- Token, modelin metin birimidir; İngilizce'de ~0,75 kelime, Türkçe'de bir
  kelime çoğu zaman 2–3 token. Aynı context Türkçe'de daha az metin taşır.
- Parametreler modelin öğrendiği milyarlarca sayıdır; "7B" = 7 milyar sayı.
- Model diskte tek bir dosyadır (ör. 27B Q4 ≈ 17 GB); çalıştırmak, bu dosyayı
  belleğe yükleyip her token için hesaba sokmaktır.
- LLM veritabanı değildir: akıcılığı yüksek, olgu garantisi yoktur — küçük
  modellerde bu fark daha da açılır.
:::
