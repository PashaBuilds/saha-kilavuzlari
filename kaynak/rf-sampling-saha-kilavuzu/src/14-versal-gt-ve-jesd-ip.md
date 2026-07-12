# Bölüm 14 — Versal GT ve JESD204C IP

Zincirin AFE ucunu ve clock ağacını gördük; sıra FPGA ucunda. Bu bölümde
{{sec:4}}'te kavramsal tanıttığımız GT anatomisini AMD Versal'in gerçek
adlarıyla dolduracak, JESD204C IP'sinin clock ve register dünyasını
öğrenecek ve {{sec:5}}'teki link parametrelerinin IP konfigürasyonuna
nasıl eşlendiğini göreceğiz. Terimler ve kurallar AMD'nin iki dokümanından
gelir: **AM002** (*Versal Adaptive SoC GTY and GTYP Transceivers
Architecture Manual*) ve **PG242** (*JESD204C LogiCORE IP Product Guide*).
Bu iki numarayı yer imine ekle; bu bölüm harita, onlar arazidir.

::: ogren
- Versal GTY/GTYP quad yapısını: kanallar, HSCLK, LCPLL/RPLL
- Refclk yerleşim kurallarını (ve 16.375 Gb/s eşiğini)
- JESD204C IP'nin kuşbakışını: portlar, register arayüzü, lisans
- Core clock hesabını: lane rate / 66 ve SYSREF ilişkisini
- IP konfigürasyon alanlarının §5 parametreleriyle eşlemesini
:::

## GTY/GTYP: quad'ın içi

Versal'de yüksek hızlı transceiver'lar **GTY** ve **GTYP** aileleridir;
ikisi de **32.75 Gb/s'ye kadar** lane hızı destekler (fark uygulama
odaklıdır: GTYP, PCIe Gen5/128B-130B gibi protokol yetenekleri ekler —
JESD işi için ikisi de aynı şekilde kullanılır). Yapı taşı **quad**'dır
({{fig:d07}}): **4 kanal** (her biri bağımsız TX+RX; SerDes, CDR,
eşitleyiciler {{sec:4}}) ve **2 HSCLK bloğu**. Her HSCLK bloğunda bir
**LCPLL** (LC-tank, düşük jitter — yüksek hızlı JESD lane'lerinin tipik
kaynağı) ve bir **RPLL** (ring, esnek) bulunur; HSCLK0 kanallar 0–1'i,
HSCLK1 kanallar 2–3'ü besler.

![Versal GTY quad'ı ve JESD204C IP'nin clock bağlantıları: refclk çiftleri HSCLK bloklarını, clock chip SYSREF'i IP'nin tx/rx_sysref girişini besler. Alt notta refclk yerleşim kuralları.](../diagrams/svg/d07.svg)

::: not
UltraScale kuşağından geliyorsan sözlük güncellemesi: orada quad-ortak
QPLL0/QPLL1 ve kanal başına CPLL vardı. Versal'de kanal başına PLL yok;
LCPLL/RPLL çiftleri iki kanallı HSCLK bloklarında yaşar. Kavram aynı
(LC = kaliteli, ring = esnek), örgütlenme farklı.
:::

## Refclk yerleşimi: kart tasarımına inen kurallar

Her quad'ın **2 özel refclk pin çifti** vardır (GTREFCLK0/1) ve refclk
{{sec:8}}'de kurduğumuz clock ağacından gelir — fabric'ten değil. AM002'nin
yerleşim kuralları, kart şemasını FPGA pinout'una bağlar:

- Bir quad, refclk'ini **komşu quad'lardan** ödünç alabilir: en fazla iki
  quad aşağıdan (Q(n−1), Q(n−2)) veya iki quad yukarıdan (Q(n+1), Q(n+2));
  kuzey/güney yönünde ikişer yönlendirme kanalı vardır. Çok SLR'li (SSI)
  cihazlarda paylaşım kendi SLR'ı içinde kalır.
- **Kritik eşik**: **16.375 Gb/s üzerindeki lane hızlarında refclk
  paylaşımı yasaktır** — refclk o quad'ın *kendi* pinlerinden gelmek
  zorundadır. 4 kanallı örneğimiz (12.17 Gb/s) paylaşabilir; AD9084'ü
  28 Gb/s'de koşturan bir tasarım her quad'a kendi refclk çiftini çekmek
  zorundadır. Bu kural, kart şeması donmadan **önce** bilinmelidir —
  sonradan fark edilen versiyonu, {{sec:16}}'daki üzücü vakalardandır.

## JESD204C IP (PG242) kuşbakışı

AMD'nin JESD204C çekirdeği ücretli bir LogiCORE'dur (değerlendirme
lisansı ücretsiz). Kuşbakışı özellikleri: **8B/10B modda 1–16.375 Gb/s,
64B/66B modda 1–32.5 Gb/s**, 1–8 lane, subclass 0 ve 1, 64B/66B'de CRC-12
ve FEC desteği. TX ve RX ayrı core'lar olarak gelir; GT'lere bağlantı
Versal'de **Transceivers Wizard (PG331)** üzerinden kurulur. (JESD204B
için ayrı bir IP ailesi vardır: PG066 çekirdek + PG198 PHY —
UltraScale kuşağının yoludur.)

Yazılımcıya bakan yüzler:

- **Register arayüzü AXI4-Lite'tır**: link parametreleri, SYSREF kontrol,
  durum/hata bayrakları — {{sec:15}}'te init kodunun konuştuğu kapı.
- **Veri arayüzü AXI4-Stream'dir** (data + cmd): transport katmanının
  kullanıcı lojiğine teslim noktası.
- **SYSREF portları**: `tx_sysref` / `rx_sysref` — {{fig:d07}}'de camgöbeği
  hattın FPGA içindeki son durağı. Subclass 1'de zorunlu; subclass 0'da
  bağlanmaz.
- **irq** ve durum sayaçları: link izlemenin ({{sec:16}}) ham maddesi.

## Clock hesabı: lane rate → core clock → SYSREF

PG242'nin clock modeli tek cümleye iner: **core clock, 64B/66B modda
lane rate / 66'dır** (64-bit datapath; 8B/10B modda /40). "Link clock"
diye ayrı bir saat aramayın — IP'nin link ve transport katmanları core
clock'ta koşar. Örneğimizle uçtan uca:

```text
lane rate  = 12.16512 Gb/s            ({{sec:5}}'te ~12.17 diye yuvarladık)
core clock = 12.16512 / 66 = 184.32 MHz
refclk     = 368.64 MHz               (clock chip'ten; GT Wizard'ın
                                       LCPLL için desteklediği değer)
SYSREF     = 1.44 MHz                 (LEMC'nin böleni, {{sec:9}})
kontrol    : 184.32 MHz / 1.44 MHz = 128 → SYSREF periyodu, core clock
             periyodunun tam katı ✓ (PG242 şartı: 64B/66B'de 8-byte'lık
             core-clock periyotlarının katı)
```

Refclk seçimi görece serbesttir (GT'nin o lane hızı için desteklediği
herhangi bir değer); pratik akış terstir: GT Wizard'da lane hızını gir,
sunulan refclk seçeneklerinden clock chip'inin üretebildiğini seç,
{{sec:11}}–{{sec:12}}'deki ağaca işle. İki tuzak:

::: dikkat
(1) **SYSREF, core clock domain'inde örneklenir** — PG242 açıkça "SYSREF,
core clock'a senkron üretilmeli" der. Bu, SYSREF'in kart üstünde core
clock ile ilişkili bir kaynaktan gelmesi ve zamanlama analizine dahil
edilmesi demektir; "nasılsa yavaş" diye asenkron bırakılan SYSREF,
{{sec:9}}'daki pencere ihlalinin FPGA'daki kopyasını üretir. (2) GT'nin
refclk'ini core clock olarak kullanma hevesi: 64B/66B'de refclk
frekansları lane rate/66'ya denk gelmediğinden bu yol subclass 1 için
uygun değildir; PG242 "alternatif clock şemaları tasarım hatasına yol
açabilir" diye uyarır. Core clock'u IP'nin beklediği yerden (GT çıkış
clock'u / uygun kart clock'u) türet.
:::

Bir de "SYSREF Always" register biti vardır: 1 iken core her SYSREF
olayında LMFC/LEMC sayacını yeniden hizalar; 0 iken yalnızca reset sonrası
ilkini kullanır, sonrakileri yok sayar. {{sec:9}}'daki "continuous SYSREF
frekans kuralı bozuksa link periyodik sarsılır" belirtisinin FPGA'daki
düğmesi budur — continuous SYSREF + yanlış frekans + SYSREF Always=1
kombinasyonu, klasik "hıçkıran link" reçetesidir.

## IP konfigürasyonu ↔ §5 parametreleri

Vivado'da IP'yi açtığında göreceğin alanların çoğu {{sec:5}}'ten
tanıdıktır:

| IP konfigürasyon alanı | §5 karşılığı | Not |
|---|---|---|
| Line rate / refclk | lane rate | {{sec:5}} formülünden gelir |
| Lanes | L | 1–8 |
| Octets per frame | F | AFE ile birebir aynı olmalı |
| Frames per multiblock/K | K (B'de) / EMB yapısı (C'de) | 64B/66B'de multiblock sabit 32 blok |
| Subclass | subclass 0/1 | RF dünyası: 1 |
| Scrambling | scrambler | 64B/66B'de hep açık |
| CRC/FEC seçimi | sync word formatı | iki uçta aynı ({{sec:7}}) |
| SYSREF Always / delay | SYSREF yakalama politikası | {{sec:9}} |

M, N′, S transport tarafında AFE ile anlaşmanın parçasıdır; IP tarafında
F ve K üzerinden görünürler (F = M·S·N′/(8·L) muhasebesi {{sec:5}}).
Kural değişmedi: **iki uçta birebir aynı parametre seti** — IP'nin
AXI4-Lite register'larına yazdıklarınla AFE'nin SPI register'larına
yazdıkların aynı tabloyu anlatmalı.

Donanım tarafı tamam. Şimdi bütün bu parçaları doğru sırayla ayağa
kaldırma sanatına — yazılımcının bölümüne — geçiyoruz.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- AMD, AM002: *Versal Adaptive SoC GTY and GTYP Transceivers Architecture
  Manual* — quad/HSCLK/LCPLL-RPLL yapısı, refclk yerleşim kuralları,
  16.375 Gb/s eşiği.
- AMD, PG242: *JESD204C LogiCORE IP Product Guide* — hız aralıkları,
  AXI4-Lite/AXI4-Stream arayüzleri, tx/rx_sysref, core clock = lane
  rate/66, SYSREF Always, lisans.
- AMD, PG331: *Versal Adaptive SoC Transceivers Wizard* — GT bağlantısı.
- AMD, PG066 / PG198 — JESD204B IP ailesi (UltraScale yolu, referans için).
- Toplu ve linkli liste: {{sec:19}}.

</details>
