# Bölüm 2 — Fiziksel Katman ve Kablonun İçi

Fiziksel katman, bitlerin gerçek dünyada var olduğu yerdir: bakırdaki
gerilim, fiberdeki ışık. Gömülü yazılımcı olarak burada kod yazmazsın ama
arızaların ciddi bir bölümü — sallanan konnektör, yanlış kablo, duplex
uyuşmazlığı — bu katta doğar. Kısa ama somut geçeceğiz: kablonun içinde ne
var, link nasıl kurulur, o yeşil LED tam olarak ne söylüyor.

## Twisted pair: bükümün fiziği

Ofislerde ve laboratuvarlarda gördüğün klasik Ethernet kablosu **twisted
pair**dir (bükülü çift): içinde dört çift, toplam sekiz tel vardır ve her
çift kendi etrafında sürekli bükülür. Büküm süs değildir. Sinyal her çiftte
**diferansiyel** taşınır: bir tel sinyalin kendisini, eşi tersini taşır;
alıcı ikisinin *farkına* bakar. Ortamdan gelen elektromanyetik gürültü
(motor, floresan, yan kablo) bükülü iki tele hemen hemen eşit biner —
fark alınınca gürültü birbirini götürür. RF kılavuzundan hatırlıyorsan
LVDS'in mantığı aynıdır; Ethernet bunu ucuz bakırda, 100 metreye kadar
götürür.

{{svg:sema-03-kablo-link.svg|Solda kablonun içindeki dört bükülü çift ve diferansiyel taşımanın gürültüyü nasıl sildiği; sağda iki PHY'nin auto-negotiation ile anlaşıp linki kurması ve link LED'inin gerçek anlamı.}}

Kablo **kategorileri**, bu çiftlerin ne kadar sıkı büküldüğünün ve ne kadar
yalıtıldığının sınıflandırmasıdır:

| Kategori | Pratik tavan | Not |
|---|---|---|
| Cat5e | 1 Gb/s @ 100 m | sahadaki en yaygın kablo, çoğu iş için yeter |
| Cat6 | 1 Gb/s @ 100 m, 10 Gb/s @ ~55 m | daha sıkı büküm, iç ayırıcı |
| Cat6a | 10 Gb/s @ 100 m | ekranlı varyantları yaygın, kalın ve az esnek |

Hız ayrımı kablodan çok **standarttan** gelir: `100BASE-TX` (Fast Ethernet,
100 Mb/s) dört çiftin ikisini kullanır — biri gönderme, biri alma.
`1000BASE-T` (Gigabit) dört çiftin hepsini, her çifti **aynı anda iki
yönlü** kullanır. Bu yüzden "iki çifti kopuk kablo" 100 Mb/s'de sorunsuz
çalışıp Gigabit'te link kuramaz ya da linki kurup hataya boğulur —
sahada kafa karıştıran klasik senaryodur.

**Fiber** ise bambaşka bir fizik: bakır yerine cam, elektron yerine ışık.
Avantajı mesafe (kilometrelere çıkar), elektriksel yalıtım (topraklama
farkı ve parazit derdi yok) ve yüksek hız; bedeli konnektör hassasiyeti ve
maliyet. Lab içinde ve kart üstünde neredeyse hep bakır göreceksin; bina
katları arasında ve yüksek hızlı test düzeneklerinde fiber çıkar.
Kart tarafında fiber genellikle SFP (Small Form-factor Pluggable) yuvasına
takılan bir modülle gelir.

## Auto-negotiation: linkin el sıkışması

Kabloyu taktığın anda iki uçtaki **PHY**'ler (physical layer transceiver —
fiziksel katman alıcı-vericisi; Bölüm 14'te yakından tanışacağız) konuşmaya
başlar. **Auto-negotiation** (otomatik anlaşma) denen bu süreçte her taraf
"benim yapabildiklerim: 10/100/1000, half/full duplex" listesini özel
darbe dizileriyle (FLP, fast link pulse) karşıya yollar; iki taraf da iki
listede ortak olan en iyi modu seçer. Anlaşma biter, link kurulur, LED yanar.

İki kavramı ayır:

- **Link speed** (hız): 10 / 100 / 1000 Mb/s... — saniyede kaç bit.
- **Duplex**: **full-duplex** aynı anda iki yön (telefon konuşması);
  **half-duplex** tek seferde tek yön (telsiz). Modern switch'li ağlarda
  her şey full-duplex'tir; half-duplex, hub'lı eski dünyanın kalıntısıdır
  (Bölüm 4'te collision kavramıyla birlikte anacağız).

:::tuzak Duplex mismatch: yavaşlığın sinsi klasiği
Bir ucu elle "100 full, autoneg kapalı" sabitleyip öbür ucu auto bırakmak,
sahanın en sinsi arızasını üretir. Autoneg açık taraf karşıdan yetenek
listesi alamayınca standard gereği **half-duplex** varsayar. Sonuç: link
kurulur, ping gider, ama yük binince half taraf "çarpışma" algılayıp
frame'leri kırpar — bağlantı var ama performans berbat, hata sayaçları
(`late collision`, CRC) tırmanır. Kural: ya iki uç da auto, ya iki uç da
elle aynı ayar. Gömülü kartlarda PHY'yi elle sabitlemeden önce switch
portunun ayarını bilmiyorsan sabitleme.
:::

## Link LED: ne diyor, ne demiyor

RJ45 konnektörün yanındaki LED'ler PHY'nin dışa açılan tek yüzüdür.
Tipik düzen: **link/activity** LED'i (link varsa yanar, trafik varsa
kırpışır) ve **speed** LED'i (renk/durumla hızı kodlar — kartına göre
değişir, şemasına bak).

Link LED'inin yandığını görmek şunu söyler: kablo iki ucundan takılı,
çiftler sağlam, iki PHY birbirini duydu ve hız/duplex'te anlaştı. Yani
**fiziksel katman tamam**. Söylemediği şeyler: IP adresin doğru mu, DHCP
aldın mı, ping gider mi, uygulaman bağlanır mı. Bunların hepsi üst
katmanların dertleridir. Bu yüzden Bölüm 16'daki arıza karar ağacının ilk
sorusu hep budur: *"Link LED yanıyor mu?"* — cevap hayırsa üst katmanlara
hiç girmeden kabloya, konnektöre, PHY'ye bakılır.

:::saha-notu MDI/MDI-X ve düz–çapraz kablo efsanesi
Eski dünyada "PC'den PC'ye çapraz (crossover) kablo gerekir" kuralı vardı;
gönderme çiftinin karşıda alma çiftine denk gelmesi gerekiyordu. Gigabit
standardı ve modern PHY'lerdeki **auto MDI-X** özelliği bunu tarihe gömdü:
PHY, çiftleri kendisi eşler. Elindeki kablo düz mü çapraz mı diye artık
düşünme; ama çekmecedeki 20 yıllık kabloların *kategorisine* bakmaya devam
et — Cat5 (e'siz) bir kablo Gigabit'te başını ağrıtabilir.
:::

:::derin-dalis 100 metre sınırı nereden geliyor?
Bakır Ethernet standartları segment uzunluğunu 100 metreyle sınırlar
(90 m sabit tesisat + 10 m patch kablosu varsayımı). Sınırın iki kaynağı
var: sinyal zayıflaması (attenuation — yüksek frekans bileşenleri bakırda
mesafeyle erir) ve yankı/karışma bütçeleri (NEXT, return loss). 100 metre
"garantili çalışır" çizgisidir; 110 metrede dünya yıkılmaz ama standart
sana hiçbir söz vermez. Uzun mesafe gerekiyorsa araya switch koy ya da
fibere geç. Endüstriyel sahada bir de 10BASE-T1L gibi tek çiftli (single
pair) Ethernet türleri boy gösteriyor: 10 Mb/s'i tek bükülü çiftle
1 km'ye taşır — sensör ağları için tasarlandı.
:::

:::ozet
- Twisted pair, gürültüyü diferansiyel taşımayla yener; kategori (Cat5e/6/6a)
  büküm ve yalıtım kalitesidir.
- 100BASE-TX iki çift, 1000BASE-T dört çift kullanır; yarısı kopuk kablo
  100'de çalışıp Gigabit'te çuvallar.
- Auto-negotiation hız + duplex'i anlaştırır; "ya iki uç da auto ya ikisi de
  elle" kuralını çiğneme — duplex mismatch sinsi yavaşlık üretir.
- Link LED yalnızca L1'in tamam olduğunu söyler; ping/IP dertleri üst
  katmanlarındır.
- Bakırda pratik sınır 100 m; ötesi için switch ya da fiber.
:::
