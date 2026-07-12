# Bölüm 3 — Mimariler: Dense ve MoE

Model kartlarında "27B" gibi yalın sayıların yanında giderek daha sık
"35B-A3B" gibi çift sayılı ifadeler görüyorsun. Bu küçük ek, lokal LLM
dünyasının son yıllardaki en önemli dönüşümünün imzasıdır. Bu bölümde iki
temel mimariyi — dense ve MoE — sökeceğiz; bölümün sonunda "A3B" ekinin neden
"evde büyük model" çağını başlattığını anlayacaksın.

## Dense: herkes her işte

Şimdiye kadar anlattığımız model **dense** (yoğun) mimariydi: her token
üretilirken ağın **tüm parametreleri** hesaba katılır. 27B'lik dense modelde
her bir token, 27 milyar sayının tamamından geçerek doğar. Basit, öngörülebilir,
eğitimi iyi anlaşılmış bir yapıdır; küçük ve orta boyutlarda (0,5–32B) hâlâ
standarttır.

Dense'in bedeli ölçekte ortaya çıkar: model büyüdükçe her token'ın maliyeti de
aynı oranda büyür. 70B dense model, 7B'ye göre token başına 10 kat veri okutur —
birazdan Bölüm 5'te göreceğimiz gibi bu, hızın 10'a bölünmesi demektir.

## MoE: danışma yönlendirir, uzmanlar çalışır

**MoE (Mixture of Experts — uzman karışımı)** bu maliyeti kırmak için ağı
parçalara böler. Katmanlardaki büyük matris blokları, **expert** (uzman) denen
çok sayıda küçük bloğa ayrılır; önlerine de **router** (yönlendirici) adlı
küçük bir seçici konur. Her token, her katmanda tüm expert'lerden değil,
router'ın o token için seçtiği birkaç expert'ten geçer.

{{svg:04-dense-vs-moe.svg|Dense'te her token ağın tamamından geçer; MoE'de router her token için birkaç expert seçer, kalanlar o token için hiç çalışmaz.|wide}}

Artık "26B-A4B" ya da "35B-A3B" notasyonunu tam çözebilirsin:

- İlk sayı **toplam parametre**: tüm expert'lerin toplamı (35B).
- **A**'lı sayı **aktif parametre** (active): bir token üretilirken fiilen
  hesaba giren miktar (~3B) — router + seçilen expert'ler + ortak katmanlar.

:::analoji
Büyük bir hastane düşün: yüzlerce uzman doktor kadroda (toplam parametre),
ama sen kapıdan girdiğinde danışma (router) seni yalnızca ilgili iki uzmana
yönlendirir (aktif parametre). Hastanenin bilgeliği yüzlerce uzmanın
varlığından gelir; senin muayeneni hızlı yapan ise yalnızca ikisiyle
görüşmendir. Bütün doktorların binada olması gerekir — kimin gerekeceği
önceden bilinmez — ama hepsinin seninle ilgilenmesi gerekmez.
:::

## Altın kural: bellek toplamla, hız aktifle ölçülür

MoE'nin lokal dünyadaki bütün önemi tek cümlede toplanır ve bu cümle
donanım seçiminin anahtarıdır:

{{svg:05-moe-paradoks.svg|MoE denklemi: bellek ihtiyacını toplam parametre (hepsi yüklü durmalı), üretim hızını aktif parametre (token başına okunan) belirler.|wide}}

Neden hepsi bellekte durmak zorunda? Çünkü router kararını **token token**
verir: bu token matematik expert'ine, sıradaki kod expert'ine gidebilir.
Hangi expert'in ne zaman gerekeceği önceden bilinemediği için tümü hazır
beklemelidir. Ama her token yalnızca aktif dilimi okuttuğu için üretim hızı,
o dilim boyutundaki bir dense modele yakındır.

:::hesap 35B-A3B pratikte ne ister, ne verir?
>> Bellek: 35B toplam × ~0,6 GB/B (Q4) ≈ 22 GB — 24GB VRAM'e ya da 32GB Mac'e sığar
>> Hız: token başına ~3B aktif okunur ≈ 3-4B dense modelin hızı
>> Karşılaştırma: aynı bellekteki 27B dense, token başına 27B okutur
=> Benzer bellek, kabaca 6-8 kat daha az veri trafiği = kat kat yüksek token/s
Formüllerin kendisi Bölüm 4 (boyut) ve Bölüm 5'te (hız) gelecek; burada
kalıbı gör: MoE'de bellek "toplam"a, hız "aktif"e bakar.
:::

Bu asimetri, MoE'yi özellikle **bol belleği olan ama hesaplama gücü mütevazı**
makineler için biçilmiş kaftan yapar: 64–128GB unified memory'li bir Mac ya da
mini PC, 100B+ toplam parametreli bir MoE'yi belleğine alıp küçük model
akıcılığında çalıştırabilir. 2026'nın açık model manzarasında büyük modellerin
neredeyse tamamen MoE'ye dönmesinin (Bölüm 10) ve "evde büyük model" çağının
açılmasının sebebi budur.

:::tuzak
İki karıştırma klasiği: (1) "35B-A3B, 3B'lik modelmiş" — hayır; bilgi
kapasitesi 35B tarafındadır, 3B yalnızca hız karakterini anlatır. Kalitesi
kabaca 20-30B dense sınıfında gezer, 3B sınıfında değil. (2) "Aktifi 3B,
o hâlde 4GB belleğe sığar" — hayır; belleğe **toplam** sığmak zorunda.
A'lı sayıya bakarak bellek planı yapmak, MoE tuzaklarının en pahalısıdır.
:::

:::derin-dalis Reasoning modelleri ve KV cimrisi mimariler
İki güncel akıma kısa pencere. **Reasoning ("thinking") modelleri:** cevaptan
önce görünür bir "düşünme" bölümü üretir — problemi adım adım açar, sonra
toparlar. Buna test-time compute (çıkarım anında ek hesap) denir: model
eğitimde değil, cevap üretirken daha çok emek harcayarak kaliteyi yükseltir.
Lokal maliyeti nettir: yüzlerce hatta binlerce ekstra token üretilir, yani
aynı soruya cevap süresi kat kat uzar; token/s'in düşük olduğu kurulumda
"1 dakika düşünen" model sabır ister. Çoğu güncel model bu kipi açıp
kapatmana izin verir. **KV tasarrufu mimarileri:** uzun context'in bellek
maliyetini (Bölüm 7) düşürmek için attention katmanları budanır — sliding
window (kayan pencere: her token yalnızca yakın geçmişe bakar), hybrid
attention (katmanların çoğu yakına, birkaçı tüm geçmişe bakar), MLA gibi
sıkıştırma teknikleri. Model kartında bu adları gördüğünde çevirisi şudur:
"uzun context'te belleği daha az yer".
:::

:::ozet
- Dense: her token tüm parametrelerden geçer; küçük-orta boyutların standardı.
- MoE: router her token için birkaç expert seçer; "35B-A3B" = 35B toplam,
  ~3B aktif.
- Altın kural: **bellek ihtiyacını toplam, hızı aktif parametre belirler** —
  MoE bu sayede bol bellekli mütevazı makinelerde büyük model çalıştırtır.
- A'lı sayıdan bellek planı yapma; kaliteyi de aktif sayıyla yargılama.
- Reasoning modelleri cevap kalitesini ekstra "düşünme token'ları" ile satın
  alır — düşük token/s'li kurulumda bedeli süredir.
:::
