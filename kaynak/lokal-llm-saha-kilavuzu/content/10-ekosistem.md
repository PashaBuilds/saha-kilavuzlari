# Bölüm 10 — Açık Model Ekosistemi: Kim Kimdir

Kavramlar tamam; artık vitrindeki isimleri tanıma zamanı. Baştan büyük uyarı:
**bu bölüm kılavuzun en hızlı eskiyen bölümüdür.** Burada yazılanlar Temmuz
2026 fotoğrafıdır; aile adları ve karakterleri yıllar içinde görece kalıcı,
sürüm numaraları ve "en iyi" etiketleri aylıktır. Okurken mantığı al,
listeyi güncel kaynaklardan (Hugging Face trendleri, r/LocalLLaMA) tazele.

## Manzaranın büyük resmi

2026 ortasının açık model dünyasını üç cümle özetler. Birincisi: **ağırlık
merkezi Çin laboratuvarlarına kaydı** — Qwen, DeepSeek, GLM, Kimi ve
takipçileri hem en geniş boyut yelpazesini hem en serbest lisansları sunuyor.
İkincisi: **Meta geri çekildi** — Llama 4 (Nisan 2025) son açık sürüm oldu;
şirket sonraki amiral gemilerini kapalı API'ye aldı ve "Llama = açık model"
denklemi tarihe karıştı. Üçüncüsü: **büyük modeller MoE'ye döndü** (Bölüm 3'ün
öngördüğü gibi) — 2026'da 32B üstü yeni dense model neredeyse çıkmıyor;
rekabet "dev toplam, küçük aktif" tasarımlarında.

{{svg:19-ekosistem-haritasi.svg|Temmuz 2026 ekosistem fotoğrafı: Çin laboratuvarları geniş yelpaze ve serbest lisansla merkezde; ABD seçici açıklıkta; Avrupa'da Mistral tek başına. Oyuncular kalıcı, sürümler dönemseldir.|wide}}

## Aile aile saha rehberi

**Qwen (Alibaba)** — lokal dünyanın varsayılan ailesi. 0,8B'den 397B'ye uzanan
Qwen3.5/3.6 yelpazesi, tamamı Apache 2.0. Her boyutta "sınıfının en iyisi"
adaylarından; kod, çok dillilik (Türkçe dahil) ve ajan işlerinde dengeli.
Qwen3.6-27B, "24 GB sınıfının tatlı noktası" ününü taşıyor; 35B-A3B ise
hız/kalite dengesinin 2026 gözdesi.

**DeepSeek** — verimlilik okulu. V4 ailesi (V4-Flash 284B-A13B, V4-Pro
1,6T-A49B; MIT lisans) 1M context ve MLA gibi bellek cimrisi tekniklerin
öncüsü. Flash, 128-256 GB sınıfı makinelerin "frontier'e en yakın" seçeneği.
Not: efsaneleşen R1'in halefi "R2" hiç çıkmadı; reasoning artık V4'ün
açılıp kapanan kipi.

**GLM (Zhipu/Z.ai)** — kod ve ajan gücü. Amiral gemisi GLM-5.2 (744B-A40B,
MIT, 1M context) ev için fazla büyük; asıl yıldız **GLM-4.7-Flash**
(30B-A3B): "30B sınıfının en güçlüsü" diye anılan, 24 GB'ye sığan kod/ajan
canavarı.

**Kimi (Moonshot)** — "1T sınıfının" bayraktarı. K2.5 → K2.7 Code hattı
(1T toplam, 32B aktif, Modified MIT) açık modelin frontier'le boy ölçüştüğü
yer; K2.7'nin native INT4 eğitimi sayesinde Q4 dosyası "kayıpsız" sayılıyor.
Evde çalıştırması ayrı bahis (Bölüm 11'deki dürüstlük kutusuna bak).

**Gemma (Google)** — küçük-orta sınıfın kralı. Gemma 4 (2B→31B, çok kipli,
140+ dil) ile birlikte lisans da **Apache 2.0'a geçti** — önceki nesillerin
"Gemma Terms" çekincesi tarih oldu. 12B'si "ilk ciddi model" tavsiyelerinin,
26B-A4B'si verimli orta sınıfın demirbaşı.

**Mistral** — Avrupa'nın tek büyük açık oyuncusu. Large 3 (Batı'nın en büyük
açık MoE'si), Small 4 (119B-A6B; tek modelde metin+görüntü+kod) ve kod ajanı
Devstral 2; açık sürümler Apache 2.0.

**GPT-OSS (OpenAI)** — tek seferlik ama kalıcı etkili jest (Ağustos 2025):
gpt-oss-20b ve gpt-oss-120b, Apache 2.0, native MXFP4. 120b, "128 GB unified
memory sınıfının standardı" olmayı 2026'da da sürdürüyor; v2 gelmedi.

**Phi (Microsoft)** — küçük model okulu. Phi-4 varyantları (3,8B mini'den
15B reasoning-vision'a, MIT); "8 GB laptopta ne dener?" sorusunun ilk cevabı.

**Yeni/kurumsal kanat** — NVIDIA **Nemotron 3** (Super 120B-A12B: Mamba
hibrit, 1M context, tek Strix Halo'da çalışabiliyor), IBM **Granite 4.1**
(3-30B, 512K context, kurumsal/RAG odağı), **MiniMax** M2.5/M2.7 (230B-A10B,
"açık Sonnet" diye anılan ajan kodcusu), Tencent **Hunyuan Hy3** (295B-A21B,
Apache 2.0). Llama 3.1/3.3 (8B/70B) ise ekosistem alışkanlığıyla hâlâ çok
indiriliyor — eski ama iyi belgelenmiş bir klasik.

:::saha-notu Hangi aileden başlamalı?
Kararsızlığa pratik çözüm: donanımına Bölüm 11 tablosundan bak, sonra şu
sırayla dene — genel iş için **Qwen** ya da **Gemma**, kod/ajan için
**GLM-4.7-Flash** ya da **Devstral**, 128 GB sınıfında **gpt-oss-120b**.
Bu dördü, 2026 ortasında "yanlış seçmiş olma" riskini sıfıra yakın tutar;
zevkler kendi test setinle (Bölüm 2) rafine edilir.
:::

## "Open source" mu, "open weights" mi?

Dürüst ayrım şudur: bu modellerin neredeyse hiçbiri klasik anlamda açık
kaynak değildir. **Open weights** (açık ağırlık), eğitilmiş parametrelerin
indirilebilir olması demektir — tarif değil, pişmiş yemek paylaşılır. Eğitim
verisi, veri işleme hattı ve eğitim kodu genellikle kapalıdır; modeli
"yeniden derleyemezsin". Bu, pratik özgürlüklerini çoğu zaman kısıtlamaz
(çalıştır, incele, fine-tune et, dağıt) ama "open source AI" pazarlamasını
duyduğunda kastedilenin çoğunlukla bu daraltılmış açıklık olduğunu bil.
Tam açıklık (veri + kod + ağırlık) OLMo, Pythia gibi araştırma projelerinde
yaşar; üretim sınıfı modellerde istisnadır.

## Lisans okuma dersi: üç dakikada hukuk

Model kartının lisans satırı üç kümeden birine düşer:

| Küme | Örnek | Pratikte anlamı |
|---|---|---|
| Serbest | Apache 2.0, MIT | Ticari dahil her kullanım; değiştir, dağıt, ürünleştir. Tek yük: lisans metnini koru. |
| Community/özel | eski Llama, bazı kurumsal lisanslar | Genelde serbest **ama** şartlı: kullanıcı eşiği (örn. 700M MAU), kabul edilebilir kullanım politikası, ürün adlandırma kuralları. Ticari kullanım öncesi metni oku. |
| Kısıtlı açık | araştırma-yalnız, NC (non-commercial) | Deney serbest, ticari iş yasak. Ürün planı varsa baştan ele. |

2026'nın iyi haberi: ana akım, serbest kümeye kaydı (Qwen/Gemma/Mistral/
GPT-OSS Apache 2.0; DeepSeek/GLM MIT; Kimi "Modified MIT" — büyük ölçekli
ticari kullanımda küçük ek şartlar). Yine de refleks edin: **isim ne kadar
tanıdık olursa olsun, ticari projede lisans satırını oku.** NVIDIA'nın Open
Model License'ı gibi "genelde serbest ama kendi metni olan" lisanslar da
5 dakikalık okumayı hak eder.

:::tuzak
"Hugging Face'te indirilebiliyorsa serbesttir" sanmak hukuki tuzaktır —
indirme düğmesi lisans vermez. İkinci tuzak dönemseldir: bir ailenin eski
sürümünün lisansıyla yenisininkini aynı sanmak. Aynı aile lisans değiştirir
(Gemma kısıtlıdan Apache'ye geçti; Llama açıktan kapalıya yürüdü). Sürüm
başına kontrol et.
:::

:::derin-dalis Neden herkes modelini açıyor (ya da kapatıyor)?
Açık ağırlık yayımlamanın ticari mantığı çok katmanlı: ekosistem kurma
(senin modelinin etrafında araç/bilgi birikimi oluşursa API'n ve bulutun da
kazanır), yetenek çekme, standart belirleme ve — özellikle Çin cephesinde —
kısıtlanmış çip erişimine karşı yazılım kalitesiyle küresel etki kurma.
Kapatmanın mantığı da simetrik: model frontier'e yaklaştıkça rakibe
verilen her şey maliyete dönüşür (Meta'nın dönüşü, OpenAI'ın tek jestle
yetinmesi). Senin için pratik ders: açık ekosistem bir hayır işi değil,
rekabet stratejisidir — bugün bedava olan yarın kapanabilir. Lokal kopyanın
kıymeti de tam burada: **indirdiğin dosyayı kimse geri alamaz.**
:::

:::ozet
- 2026 fotoğrafı: merkez Çin'de (Qwen/DeepSeek/GLM/Kimi), Meta çekildi,
  büyük modeller MoE'leşti; bu bölüm hızla eskir, mantığı al, listeyi tazele.
- Kısa yol: genel iş Qwen/Gemma, kod-ajan GLM-Flash/Devstral, 128 GB sınıfı
  gpt-oss-120b, frontier merakı DeepSeek V4-Flash / Kimi.
- "Open weights" ≠ open source: pişmiş yemek paylaşılır, tarif değil.
- Lisans üç küme: serbest (Apache/MIT — ana akım artık burada), şartlı
  community, kısıtlı. Ticari işte sürüm başına lisans oku.
- İndirdiğin ağırlık geri alınamaz — lokal kopya, ekosistem rüzgârlarına
  karşı sigortadır.
:::
