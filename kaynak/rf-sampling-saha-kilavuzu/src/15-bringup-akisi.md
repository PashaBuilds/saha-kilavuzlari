# Bölüm 15 — Bring-up Akışı

Kart masada, güç verildi, JTAG bağlı. Bu bölüm senin bölümün: on dört
bölümlük teoriyi, çalışan bir sisteme çeviren **sıra**. JESD bring-up'ının
acımasız gerçeği şudur: adımların %90'ı sırasız da "bir şekilde" çalışır
gibi görünür — ta ki üretimin yüzüncü kartında, soğuk startta, sahada
çalışmayana kadar. Doğru sıra, şans faktörünü sistemden atmak içindir.
Akış üretici bağımsızdır; TI/ADI renklerini {{sec:11}}–{{sec:12}}'den
alır.

::: ogren
- Uçtan uca init sırasını ve her adımın "neden önce" gerekçesini
- Her adımda hangi durumu doğrulayacağını (kavramsal register düzeyi)
- Init state machine önerisini
- Sık yapılan sıra hatalarını ve belirtilerini
:::

## Büyük resim: beş perde

Sıranın mantığı tek cümledir: **önce zemin (clock), sonra duvarlar
(cihaz konfigürasyonları), sonra çatı (link), en sonda hiza (SYSREF) ve
muayene (doğrulama).** Her perde, bir öncekinin çıktısına yaslanır:

```text
1. CLOCK ZEMİNİ      clock chip init → PLL kilitleri → çıkışlar aktif
2. CİHAZ KONFİGÜ     AFE init (clock modu, DSA, DDC/DUC, NCO, JESD parametreleri)
                     FPGA: GT + IP konfigürasyonu (henüz link yok)
3. LİNK KURULUMU     GT reset sırası → IP enable → (B: SYNC~ el sıkışması /
                     C: SH→EMB kilit merdiveni)
4. SYSREF PERDESİ    yakalama pencerelerini kur → SYSREF tetikle →
                     LMFC/LEMC + NCO hizası
5. DOĞRULAMA         kilitler, sayaçlar, monitörler, veri sağlığı
```

Adım adım, her durakta "neye bakacaksın" ile:

**1a — Clock chip'i ayaklandır** ({{sec:8}}, {{sec:11}}–{{sec:12}}):
referans girişini seç, PLL1 register'larını yaz, **PLL1 kilit bayrağını
bekle**; PLL2'yi yaz, **PLL2 kilidini bekle**; çıkış bölücü/formatlarını
yaz. SYSREF üreticisini yapılandır ama **tetikleme**. *Bakacağın yer:*
kilit bayrakları + holdover durumu. Kilit gelmiyorsa ileri gitme —
sonraki her şey kumdan inşaat olur.

**1b — Dağıtım halkası** (LMX1204/ADF4382): bölücü/çarpan/kanal
konfigürasyonu, kilit (ADF4382) veya giriş algılama (LMX1204) kontrolü.

**2a — AFE init**: RESETZ/reset ile bilinen duruma al; clock modunu kur
(harici CLK± mi, REFCLK±+dahili PLL mi — {{sec:11}}/{{sec:12}} tablosu);
dahili PLL kullanılıyorsa **onun kilidini de bekle**. Sonra sinyal yolu:
DSA başlangıç değerleri ({{sec:1}}'deki saha notunu hatırla), DDC/DUC ve
NCO konfigürasyonu ({{sec:3}}), JESD parametre seti ({{sec:5}} tablosu) ve
çip kalibrasyonları (interleaving vb., {{sec:2}}) — kalibrasyon bitti
bayrağını bekle. *Bakacağın yer:* clock-algılandı/PLL-kilit bitleri,
kalibrasyon durum register'ı.

**2b — FPGA konfigürasyonu**: bitstream yüklü, GT Wizard çekirdeği ve
JESD204C IP register'ları ({{sec:14}}) yazılmış; IP henüz "enable"
edilmemiş olabilir. *Bakacağın yer:* AXI4-Lite üzerinden IP versiyon/ID
okuması — okuyamıyorsan zaten bus/reset problemin var demektir.

**3 — GT reset sırası ve link kurulumu**: altın kural — **refclk
kararlı olmadan GT reset bırakılmaz.** Tipik sıra: refclk'in geldiğini
doğrula (clock chip perde 1'de bitti; FPGA'da refclk sayacı/monitörü
varsa oku) → GT PLL (LCPLL) reset'ini bırak, **PLL kilidini bekle** → TX/RX
yol reset'lerini bırak, reset-done bayraklarını bekle → IP'yi enable et.
B linkinde SYNC~ el sıkışması başlar (CGS→ILAS, {{sec:6}}); C linkinde RX,
SH→EoEMB→EMB merdivenini tırmanır ({{sec:7}}). *Bakacağın yer:* GT PLL
lock, reset-done, IP'nin SH lock / EMB lock (C) veya sync durumu (B)
bayrakları — {{fig:m01b}} ve {{fig:m01c}}'nin gerçek hayattaki
karşılıkları.

**4 — SYSREF perdesi** ({{sec:9}}–{{sec:10}}): tüm cihazlarda SYSREF
yakalama modunu kur (AFE'nin capture/windowing ayarı, IP'de SYSREF
Always politikası); NCO senkron reset modunu kur; clock chip'ten SYSREF'i
tetikle (pulser, 1/2/4/8 darbe); sonra SYSREF'i sustur. *Bakacağın yer:*
AFE'nin SYSREF monitörü (kenar pencerenin neresinde? — logla!), IP'nin
SYSREF-yakalandı/LMFC-hizalandı göstergeleri, cihazların "SYSREF–LEMC
faz" register'larının sıfır okuması ({{sec:10}}).

**5 — Doğrulama**: link kilitleri stabil mi (birkaç saniye izle), CRC/kod
hata sayaçları sıfırda mı ({{sec:7}}), test tonu ile uçtan uca veri
sağlığı, çok kanallıysa kanal-arası faz ölçümü. Ancak bunlardan sonra
"link çalışıyor" cümlesini kur.

## Init state machine önerisi

Yukarıdaki akışı düz bir script yerine **durum makinesi** olarak kodla;
farkı sahada görürsün: her durumun tek bir bekleme koşulu, her bekleme
koşulunun bir zaman aşımı ve her zaman aşımının anlamlı bir hata mesajı
olur.

```c
typedef enum {
    S_CLK_INIT,        // clock chip yaz, PLL1/PLL2 kilidi bekle
    S_DIST_INIT,       // LMX/ADF konfig, kilit bekle
    S_AFE_INIT,        // AFE reset+konfig, kalibrasyon bekle
    S_FPGA_CFG,        // GT+IP register'ları, sanity read
    S_GT_BRINGUP,      // GT reset sırası, PLL/reset-done bekle
    S_LINK_ENABLE,     // IP enable, kilit merdiveni bekle
    S_SYSREF_ARM,      // yakalama+NCO reset modları
    S_SYSREF_FIRE,     // tetikle, hiza register'larını doğrula
    S_VERIFY,          // sayaç/CRC/faz doğrulama
    S_RUN, S_ERROR
} bringup_state_t;
```

Her durumdan `S_ERROR`'a giden kenara, **durumu ve okunan register
görüntüsünü** loglayan bir aksiyon koy. "Kart yüz kartta bir kalkmıyor"
mesaisi, bu logların varlığıyla saatler; yokluğuyla haftalar sürer.

## Sık yapılan sıra hataları

| Hata | Belirti | Neden |
|---|---|---|
| GT reset'i refclk'ten önce bırakmak | Link *bazen* kalkar; soğukta hiç | CDR/PLL rastgele faza kilitlenir — {{sec:16}}'daki vaka |
| SYSREF'i link kurulmadan tetiklemek | Hiza var gibi, veri kayık | B'de ILAS zaten LMFC'ye hizalı başlar; erken SYSREF, sonraki adımlarla ezilir |
| SYSREF'i hiç susturmamak | Spektrumda f_SYSREF spur ailesi | {{sec:9}} kuplaj riski |
| AFE kalibrasyonunu beklememek | İlk saniyelerde bozuk spektrum/spur | Kalibrasyon veri yolunu sonradan değiştirir |
| Parametre setini tek uçta değiştirmek | Link kalkar, veri çorba | {{sec:5}} — iki uç birebir aynı olmalı |
| Kilit beklemeden ilerlemek | "Bazen çalışıyor" sendromu | Her perde bir öncekinin kilidine yaslanır |

::: saha
Bring-up scriptine en başta şunu ekle: **her perdenin sonunda tüm durum
register'larını oku ve zaman damgasıyla logla** — başarılı koşularda da.
İlk arızalı kart geldiğinde elinde "sağlıklı kartın imzası" olur; fark
almak, sıfırdan teşhisten on kat hızlıdır.
:::

Sıra doğruysa ve yine de çalışmıyorsa? O zaman debug bölümüne hoş
geldin — loopback'ler, göz taramaları ve semptom tabloları.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- {{sec:11}}–{{sec:12}}'nin cihaz dokümanları (LMK04832, HMC7044, AFE7900,
  AD9084) — kilit bayrakları, kalibrasyon ve SYSREF mekanizmaları.
- AMD PG242/AM002 — GT reset sırası, IP enable ve durum bayrakları.
- TI SLYT628 / ADI MCS dokümanları — SYSREF perdesinin sırası.
- Toplu ve linkli liste: {{sec:19}}.

</details>
