# Bölüm 6 — JESD204B Derinlemesine

{{sec:5}}'te haritayı çizdik; şimdi 204B linkinin gerçekte nasıl ayağa
kalktığını kare kare izleyeceğiz. Bunu bilmek zorundasın, çünkü bring-up
sırasında status register'larında göreceğin bayraklar — "CGS'de", "ILAS
yakalandı", "SYNC düştü" — bu bölümdeki üç perdelik oyunun sahneleridir.
Link bir sahnede takılı kaldığında, o sahnenin *neye ihtiyaç duyduğunu*
bilirsen nereye bakacağını da bilirsin.

::: ogren
- SYNC~ sinyalinin görevlerini
- CGS: K28.5 yağmuru ve comma kilidi (W02)
- ILAS: 4 multiframe'lik geçit töreni ve içindeki konfigürasyon verisi
- Frame / multiframe / LMFC üçlüsünü ve K'nin rolünü
- Character replacement: veri akarken frame hizasının izlenmesi
- RBD ve elastic buffer release: deterministic latency'nin mekanik temeli
:::

## SYNC~: tek pinlik telsiz

204B'de RX'in TX'e konuşabildiği tek kanal, **SYNC~** adlı aktif-düşük
sinyaldir (genelde diferansiyel bir çift; FPGA'dan AFE'ye doğru gider —
veri yönünün tersi). Üç işi vardır:

1. **Senkronizasyon isteği**: RX, "link kur/yeniden kur" demek için SYNC~'i
   düşük tutar.
2. **Hata bildirimi**: veri akarken ciddi hata görürse RX, SYNC~'i yeniden
   düşürerek linki CGS'e döndürebilir (kısa hata darbeleri de tanımlıdır).
3. **Zamanlama referansı** (yalnız subclass 2): SYNC~'in bırakılma anı
   deterministic latency cetveli olarak kullanılır — {{sec:5}}'te
   anlattığımız gibi yüksek hızda pratik değildir.

Görünüşte masum bu pin, kart tasarımında gerçek bir sinyaldir: yanlış
polarite, yanlış gerilim standardı veya unutulmuş pull-up, "link hiç
kalkmıyor" vakalarının klasiklerindendir ({{sec:16}}).

## Birinci perde — CGS: comma yağmuru

CGS (code group synchronization — kod grubu senkronizasyonu) linkin
alfabesini kurar. RX, SYNC~'i düşürür; TX cevaben kesintisiz **K28.5**
karakteri basar. K28.5, 8b/10b'nin yıldızıdır: 10-bit kodu, veri
akışında başka hiçbir yerde oluşamayan **comma** desenini içerir. RX'in
deserializer'ı bu deseni kayan pencereyle arar; bulduğunda 10-bit sözcük
sınırlarını öğrenmiştir — {{sec:4}}'te "CDR bit bulur ama bit'in nerede
başladığını bilmez" demiştik, comma tam o boşluğu doldurur. RX, tüm
lane'lerde **dört ardışık doğru /K/ karakteri** görünce senkron olduğuna
karar verir ve SYNC~'i bırakır (subclass 1'de bırakma anı da başıboş
değildir: kendi LMFC kenarına hizalanır).

{{fig:w02}} akışın tamamını gösterir: SYNC~ düşer, K yağmuru başlar, SYNC~
bırakılır — ama TX hemen veriye geçmez.

![JESD204B link kalkışı: CGS'ten ILAS'a, ILAS'tan veriye. ILAS'ın SYNC~ bırakıldıktan sonraki LMFC kenarında başladığına dikkat — determinizmin ilk tuğlası.](../diagrams/wavedrom/w02.json5)

## İkinci perde — ILAS: geçit töreni

SYNC~ bırakıldıktan sonra TX (subclass 1'de) **bir sonraki LMFC kenarını
bekler** ve ILAS'a (initial lane alignment sequence — başlangıç lane
hizalama dizisi) başlar. ILAS, tam **4 multiframe** süren, içeriği önceden
tanımlı bir geçittir; üç iş görür:

1. **Multiframe sınırlarını işaretler**: her ILAS multiframe'i /R/ (K28.0)
   ile açılır, /A/ (K28.3) ile kapanır. RX, /A/ karakterlerinin geliş
   anlarından lane'ler arası kayıklığı ölçer ve elastic buffer'larını buna
   göre hizalar — "lane alignment"ın kendisi.
2. **Kimlik beyan eder**: 2. multiframe'de /R/'nin ardından /Q/ (K28.4)
   gelir ve peşinden 14 oktetlik **link konfigürasyon verisi**: TX'in
   kullandığı L, M, F, S, K, N′, subclass... hepsi. RX bunu kendi
   register'larıyla karşılaştırıp uyuşmazlık bayrağı dikebilir.
3. **Frame cetveli verir**: RX, frame ve multiframe sayaçlarını bu geçit
   sırasında kilitleyerek veri fazına hazır girer.

::: saha
ILAS konfigürasyon verisi, debug'daki en değerli tanıklardan biridir: çoğu
FPGA IP'si yakaladığı ILAS oktetlerini okunabilir register'lara koyar.
"Link kalkıyor ama veri bozuk" durumunda oraya bak — TX'in *gerçekte*
gönderdiği parametre setini, kendi RX konfigürasyonunla yan yana görürsün.
İki setin farkı, hatanın adresidir.
:::

## Frame, multiframe, LMFC: linkin takvimi

Veri fazında akış, görünmez bir takvimle örgütlenir. **Frame**, S örneklik
temel dilimdir (bizim örnekte F=4 oktet, ~2.7 ns). **Multiframe**, K
frame'lik büyük dilimdir (K=32 ile ~86.8 ns). **LMFC** (local multiframe
clock), her cihazın kendi içinde multiframe sınırlarını sayan sayaçtır:

```text
f_LMFC = frame clock / K        (örneğimizde 368.64 MHz / 32 = 11.52 MHz)
```

"Local" kelimesine dikkat: TX'in de RX'in de *kendi* LMFC'si vardır ve
{{sec:9}}'a kadar bu ikisinin fazlarının aynı olduğunu garanti eden hiçbir
şey yok. ILAS'ın LMFC kenarında başlaması, buffer'ların LMFC'ye göre
boşalması — takvimin tüm işlevleri, iki ucun takvimlerinin hizalı olduğu
varsayımına yaslanır. O hizayı kuran sinyal SYSREF'tir ve bu cümle,
{{sec:9}}'un fragmanıdır.

## Veri fazında hiza bekçiliği: character replacement

Link kalktı, veri akıyor. Peki RX'in frame hizası kaydıysa — bir glitch,
bir bit kayması — bunu nasıl fark ederiz? 204B'nin zarif hilesi: TX, belirli
koşullar sağlandığında frame'in **son oktetini** özel bir karakterle
değiştirir. Kurallar:

- **Scrambling kapalıyken**: bir frame'in son okteti, önceki frame'in son
  oktetine *eşitse* değiştirilir — multiframe sonundaysa /A/ (K28.3),
  değilse /F/ (K28.7) gönderilir. (Eşitlik şartı sayesinde RX, orijinal
  değeri önceki frame'den kopyalayarak geri koyabilir.)
- **Scrambling açıkken**: eşitlik aranmaz; son oktetin *değerine* bakılır —
  frame sonunda 0xFC ise /F/, multiframe sonunda 0x7C ise /A/ ile
  değiştirilir (bu değerler zaten /F/ ve /A/'nın 8-bit karşılıklarıdır;
  RX geri çevirir).

RX bu karakterleri gördüğü konumları kendi frame sayacıyla karşılaştırır:
/A/ hep multiframe sınırında görünmeli; başka yerde görünüyorsa hiza
kaymış demektir. Değiştirme iki uçta da bilinen kurala dayandığı için
veri kaybı olmaz.

Bu mekanizma **süreklidir**: link ömrü boyunca frame hizası bekçisiz
kalmaz. Status register'larındaki "frame alignment error" ve "lane
alignment error" sayaçları bu bekçinin raporudur; artıyorlarsa hiza
periyodik olarak sarsılıyor demektir — genelde clock veya sinyal bütünlüğü
kokusu ({{sec:16}}).

## RBD ve elastic buffer release

{{sec:4}}'te lane'ler arası skew'u "alıcı çözer" demiştik; mekanizma şu:
her lane'in verisi RX'te bir **elastic buffer**'a yazılır. Lane'ler farklı
anlarda varır ama buffer'lardan **okuma**, hepsi için aynı anda başlar:
LMFC kenarından **RBD** (RX buffer delay) frame kadar sonra. RBD, 1 ile K
arasında seçilir ve iki şeyi dengelemelidir: en geç gelen lane bile release
anından önce buffer'a yazmış olmalı (yoksa boş buffer okunur), ama gereksiz
büyük RBD da baştan sona gecikme ekler.

Bu mekanizmanın güzelliği şurada: release anı *veriye değil takvime*
bağlıdır. Lane'lerin varış anları kart kartlar arasında, açılış açılışlar
arasında pikosaniyelerce oynasa da, release hep "LMFC + RBD" anında olur —
**gecikme deterministik hale gelir**. Tabii ki bir şartla: LMFC'lerin
kendisi her açılışta aynı yerde olmalı. Yine {{sec:9}}'a selam.

![JESD204B RX link state machine — status register'larında gördüğün bayrakların haritası.](../diagrams/mermaid/m01b.mmd)

## 8b/10b vergisi ve B'nin tavanı

Kapanışta {{sec:4}}'teki hesabı hatırlayalım: 8b/10b, hat kapasitesinin
%20'sini kodlamaya harcar. 12.5 Gb/s tavanındaki bir 204B lane'i en fazla
10 Gb/s payload taşır. RF AFE'lerin bant genişliği iştahı büyüdükçe bu
vergi ve tavan dar geldi: {{sec:5}}'teki hesapta gördük, 4 kanallı mütevazı
senaryomuz bile B'de 8 lane istiyor. JESD204C'nin cevabı — 64b/66b, 32 Gb/s
ve yeni bir senkronizasyon modeli — bir sonraki bölümün konusu.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- TI, SBAA517 ve SLAP160 (*JESD204B Transport and Data Link Layers*) —
  CGS/ILAS akışı, 4×/K/ kuralı, K-karakter tablosu, character replacement.
- Analog Devices, MS-2448: *Critical Design Issues for a Functioning
  JESD204B Interface* — replacement kuralları (0xFC/0x7C).
- TI, SBAA543: *Determining Optimal Receive Buffer Delay in JESD204B* —
  RBD ve elastic buffer release.
- chipinterfaces.com, *What is JESD204B — quick summary* — ILAS multiframe
  içerikleri, SYNC~ görevleri.
- Intel JESD204B IP User Guide — LMFC tanımı, K kuralları.
- Toplu ve linkli liste: {{sec:19}}.

</details>
