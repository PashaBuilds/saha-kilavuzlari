# Bölüm 9 — SYSREF: Neden Var, Nasıl Çalışır

Bu dokümanda üç bölümdür aynı cümleye çarpıyoruz: "LMFC/LEMC'lerin hizalı
olduğunu varsayıyoruz — {{sec:9}}'a bakınız." Geldik. SYSREF, JESD204
dünyasının en çok yanlış anlaşılan sinyalidir: ne bir clock'tur ne de veri;
işi bittiğinde susabilen, ama sustuğunda bile etkisi kalıcı olan bir
**hizalama emridir**. Bu bölümde önce SYSREF'in çözdüğü problemi sayılarla
koyacağız, sonra tanımını, frekans kuralını, kullanım tiplerini ve
yakalama/izleme mekanizmalarını göreceğiz. Bu bölüm dokümanın kalbidir:
{{sec:15}}'teki bring-up sırasının ve {{sec:16}}'daki kayma teşhislerinin
tamamı buraya yaslanır.

::: ogren
- İki cihazın sayaçları hizasızsa tam olarak neyin bozulduğunu
- SYSREF'in tanımını: setup/hold penceresi ve faz reset mekaniği (W01)
- Frekans kuralını: SYSREF, LMFC/LEMC periyodunun tam böleni
- Continuous / gapped periodic / one-shot tiplerini ve seçim mantığını
- SYSREF windowing/monitoring: "geç geldi/erken geldi" sayaçlarını
- SYSREF'in neden hem AFE'ye hem FPGA'ya gittiğini
:::

## Problem: herkesin takvimi kendine

{{sec:6}}'dan hatırla: linkin iki ucunda da birer yerel sayaç var — TX'in
LMFC'si (C'de LEMC'si) ve RX'in LMFC'si. "Local" demiştik: her cihaz kendi
sayacını kendi reset'inden başlatır. İki cihazın reset'i arasında kaç
nanosaniye olduğunu kimse bilmez; dolayısıyla iki LMFC arasındaki faz farkı
**rastgeledir** — her açılışta farklı.

Bunun iki bedeli var:

1. **Deterministic latency ölür.** {{sec:6}}'daki buffer release "LMFC +
   RBD" anında oluyordu. TX, ILAS'ı *kendi* LMFC kenarında yollar; RX,
   buffer'ı *kendi* LMFC kenarına göre boşaltır. İki takvim arasındaki fark
   her açılışta değişiyorsa, verinin uçtan uca gecikmesi de açılıştan
   açılışa **bir multiframe'e kadar** oynar. Bizim örnekte LMFC periyodu
   86.8 ns idi — radar için felaket, kalibre edilmiş herhangi bir sistem
   için kâbus.
2. **Çok çipli sistem kurulamaz.** Aynı kartta iki AFE varsa ve
   LMFC/LEMC'leri hizasızsa, iki çipin örnekleri arasında sabit ama
   *bilinmeyen* bir zaman kayması olur. Beamforming, faz karşılaştırma,
   kanal eşleme — hepsi bu belirsizliğe kurban gider ({{sec:10}}).

Çözüm ilkece basit: **herkese aynı anda "sayacını sıfırla" diyen ortak bir
sinyal dağıt.** O sinyalin adı SYSREF'tir ve subclass 1'in tanımlayıcı
mekanizmasıdır ({{sec:5}}).

## Tanım: clock değil, hizalama emri

SYSREF, device clock ile **aynı kaynaktan üretilen** (kaynak-senkron) ve
alıcı cihaz tarafından **device clock'un kenarıyla örneklenen** bir
sinyaldir. Yakalanan her SYSREF kenarı, cihazın LMFC/LEMC sayacının fazını
bilinen konuma sıfırlar. {{fig:w01}} mekaniği gösteriyor:

![SYSREF'in device clock ile yakalanması: SYSREF kenarı, device clock'un örnekleme kenarına göre setup/hold penceresi içinde gelmeli; yakalanan kenar sayaç fazını sıfırlar.](../diagrams/wavedrom/w01.json5)

Buradaki kritik incelik **setup/hold penceresidir**: SYSREF, device clock
kenarında örneklenen sıradan bir dijital giriş gibidir — kenar değişimi,
clock kenarına çok yakın gelirse (pencere ihlali) cihaz onu bu kenarda mı
sonraki kenarda mı gördüğüne **kararsız kalır**. Sıradan bir veri hattında
bu tek bit hatası olurdu; SYSREF'te ise sayacın *bir device clock periyodu
kaymış* olarak sıfırlanması demektir — 3 GHz'lik clock'ta ~333 ps'lik,
sistemin geri kalanının asla fark edemeyeceği sinsi bir kayma. Bu yüzden:

::: dikkat
SYSREF ile device clock arasındaki **faz ilişkisi bir tasarım
parametresidir**, tesadüfe bırakılamaz. Clock chip'ler tam bu yüzden
DCLK/SYSREF çıkışlarını **çift** olarak üretir ({{sec:8}}): aynı bölücü
zincirinden türedikleri için aralarındaki faz bilinir ve gecikme
register'larıyla ayarlanabilir. Kart üstünde de iki iz, uzunluk eşlemeli
çekilir. "SYSREF'i başka bir kaynaktan veririm, nasılsa yavaş bir sinyal"
düşüncesi, bu pencereyi tesadüfe bırakmaktır — {{sec:16}}'daki "sıcaklıkla
kayan link" vakalarının klasik kökeni.
:::

## Frekans kuralı: takvimle aynı ritimde

SYSREF periyodik kullanılacaksa frekansı serbest değildir:

```text
f_SYSREF = f_LMFC / n      (n = 1, 2, 3, …)
```

yani SYSREF periyodu, LMFC (C'de LEMC) periyodunun **tam katı** olmalıdır.
Neden: sayaç zaten periyodik sıfırlanıyor; SYSREF kenarları hep sayacın
*aynı fazına* denk gelirse ikinci ve sonraki kenarlar hiçbir şeyi değiştirmez
(hizayı yalnızca doğrular). Kural bozulursa her SYSREF kenarı sayacı *başka*
bir faza çeker — link periyodik olarak kendini yeniden hizalar, veri akışı
düzenli aralıklarla sarsılır. Bu, "SYSREF frekansım yanlıştı" diye değil,
"link arada bir hıçkırıyor" diye görünür; teşhisi zordur.

Örneğimizle: LMFC = 11.52 MHz (B) veya LEMC = 5.76 MHz (C) idi. SYSREF
adayları: 5.76/n — örneğin 1.44 MHz (n=4), 360 kHz (n=16)... Clock chip'in
SYSREF bölücüsüne yazacağın değer tam bu hesaptan çıkar ve **frekans
planının bir parçasıdır** ({{sec:17}}'deki kontrol listesinde yerini alacak).

## Tipler: sürekli mi, tek atım mı?

SYSREF'in *ne zaman* aktığı bir tasarım kararıdır; üç yaygın kullanım:

- **Continuous (sürekli) periyodik**: SYSREF hep akar. Artı: cihazlar hizayı
  sürekli doğrular; kurulum basit. Eksi: SYSREF, veri bandına ve clock'a
  **kuplaj** yapabilir — periyodik bir kare dalga, spektrumda f_SYSREF
  aralıklı spur ailesi demektir. RF dünyasında bu genellikle kabul edilemez.
- **Gapped periodic (aralıklı periyodik)**: senkronizasyon gerektiğinde bir
  süre periyodik akar, sonra susturulur. Hizalama penceresi boyunca
  continuous'un rahatlığı, veri toplarken sessizlik.
- **One-shot / tek atım**: yazılım tetikler, clock chip tek (veya sayılı —
  clock chip'lerde tipik seçenekler 1/2/4/8/16 darbe) SYSREF darbesi
  üretir, hat susar. RF açısından en temizi; iki bedeli var: senkronizasyon
  tamamen **senin init akışının** sorumluluğuna geçer ve hat üzerinde tek
  başına duran bir darbe olduğu için **DC kuplaj** gerektirir (AC kuplajlı
  bir hattan geçen tek darbe, kondansatörde şekil bozar — periyodik
  SYSREF'in aksine).

::: saha
Pratik politika çoğunlukla şudur: bring-up ve senkronizasyon aşamasında
gapped/one-shot SYSREF tetikle, hizayı doğrula, sonra SYSREF'i sustur ve
görev boyunca sessiz tut. TI'ın ADC32RF45 uygulama notu bu politikayı
yazıya dökmüştür: SYSREF frekansını düşük tut (o örnekte <5 MHz) ve link
kurulduktan sonra SYSREF'i kapat — gerekçe tam da kuplaj/spur riski.
Spektrumda f_SYSREF katlarında açıklanamayan spur'lar görürsen ilk soru:
"SYSREF hâlâ akıyor mu?" İkinci soru: "SYSREF izi, RF girişine veya
clock'a nereden kuplaj yapıyor?"
:::

## Yakalama ve izleme: windowing/monitoring

Modern AFE'ler ve clock chip'ler, SYSREF'i kör bir dijital giriş gibi
yutmaz; çoğunda iki destek mekanizması vardır:

- **Capture/yakalama kontrolü**: SYSREF girişinin hangi kenarla, hangi
  bölücü fazında, kaç kez dinleneceği register'la seçilir ("ilk kenarı al,
  sonra kulağını kapa" tek atım davranışı dahil).
- **SYSREF monitoring/windowing**: cihaz, gelen SYSREF kenarının kendi
  device clock'una göre **nerede** düştüğünü ölçer ve raporlar — "kenar,
  clock kenarından şu kadar önce/sonra geldi" sayaçları. Bazı cihazlarda
  buna bağlı otomatik gecikme ayarı (kenarı pencereye çekme) da bulunur.
  Gerçek örnekler: TI ADC12DJ3200'ün "SYSREF windowing" mekanizması kenar
  konumunu ölçüp güvenli örnekleme fazını seçtirir; TI AFE'lerinde SYSREF
  timing detector, ADI MxFE ailesinde SYSREF monitor + hata penceresi
  register'ları aynı işi görür.

**Yazılıma dokunduğu yer**: bu monitör senin en değerli bring-up aletindir.
Init sırasında SYSREF konumunu okuyup logla; pencere kenarına yakınsa
(marjin azsa) clock chip'in SYSREF gecikme register'ıyla ortala. Üretim
hattındaki yüz karttan birinde link'in "bazen" kurulamamasının en olası
açıklaması, o kartın SYSREF'inin pencere kenarında gezinmesidir —
monitörü okuyan yazılım bunu kart daha sahaya çıkmadan yakalar.

## Neden hem AFE'ye hem FPGA'ya?

{{fig:d01}}'e dönüp bak: SYSREF, clock chip'ten **iki** yere gidiyordu.
Sebebi artık açık: linkin *iki ucunda da* birer sayaç var. AFE'nin
LMFC/LEMC'si SYSREF'le hizalanıp FPGA'nınki hizalanmazsa, determinizm tek
taraflı kalır — RX'in buffer release cetveli hâlâ rastgele fazlıdır.
Subclass 1'de kural nettir: **SYSREF, linke katılan her cihaza dağıtılır**
ve her cihaz kendi device clock'uyla (FPGA tarafında core clock
domain'iyle, {{sec:14}}) yakalar. Bu da SYSREF dağıtımını clock tree'nin
birinci sınıf vatandaşı yapar: {{sec:11}} ve {{sec:12}}'deki şemalarda
camgöbeği hatların hep çift dal olduğunu göreceksin.

Sırada takvim hizasının meyvesi var: deterministic latency'nin adım adım
kuruluşu ve birden çok çipin tek koherent sisteme dönüşmesi.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- TI, SLYT628: *Synchronizing multiple high-speed multichannel converters*
  — SYSREF'in iki şartı (setup/hold + frekans kuralı), her iki uca dağıtım,
  one-shot'ta DC kuplaj.
- TI, SBAA221 (ADC32RF45 SYSREF uygulaması) — düşük SYSREF frekansı ve
  "link kurulunca kapat" politikası, kuplaj riski.
- AMD, PG242 (JESD204C IP) *SYSREF Type* bölümü — periodic / one-shot /
  gapped periodic sınıflandırması.
- TI ADC12DJ3200 (SYSREF windowing) ve ADI AD9081/AD9082 UG-1578 (SYSREF
  monitor) — windowing/monitoring örnekleri.
- TI ve ADI clock chip datasheet'leri (LMK04832, HMC7044) — DCLK/SYSREF
  çiftleri, darbe üretici modları ({{sec:8}} ve {{sec:11}}–{{sec:12}}'de
  ayrıntılı).
- Toplu ve linkli liste: {{sec:19}}.

</details>
