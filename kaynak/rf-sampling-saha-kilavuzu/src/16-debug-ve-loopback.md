# Bölüm 16 — Debug ve Loopback

Link kalkmıyor. Ya da kalkıyor ama veri bozuk. Ya da her şey güzeldi,
kart ısınınca CRC sayaçları yürümeye başladı. Bu bölüm, o anlarda
panik yerine **yöntem** koymak için var. Yöntemin üç ayağı: problemi
dilimlere ayıran **loopback haritası**, fiziksel katmanın gözünü açan
**IBERT/eye scan** ve on beş bölümün bilgisini semptomlara bağlayan
**teşhis tabloları**. Debug'ın altın kuralını baştan söyleyelim: rastgele
şeyler denemek değil, **her deneyle hipotez uzayını yarıya indirmek**.

::: ogren
- Loopback türlerini ve her birinin zincirin hangi dilimini test ettiğini
- IBERT ve eye scan'i ne zaman, nasıl kullanacağını
- Semptom → sebep tablosunu (B ve C linkleri için)
- SYSREF kaynaklı kaymaların nasıl teşhis edildiğini
- İki anonim saha vakasından çıkan dersleri
:::

## Loopback haritası: problemi dilimle

Zincir uzun: AFE'nin dijital çekirdeği → AFE SerDes → kablo/iz → GT →
IP → kullanıcı lojiği. Arıza bu zincirin *bir* diliminde; loopback'ler,
dilimleri **tek tek devreye alarak** suçluyu köşeye sıkıştırır:

![Loopback noktaları haritası. Numaralar metindeki dilim tanımlarına karşılık gelir; parantez içi kodlar Versal GT'nin CH[x]_LOOPBACK[2:0] port değerleridir.](../diagrams/svg/d08.svg)

| # | Loopback | Test ettiği dilim | Test *etmediği* |
|---|---|---|---|
| 3 | GT Near-End PCS (001) | FPGA içi dijital yol: IP ↔ PCS | PMA analogu, kablo, AFE |
| 4 | GT Near-End PMA (010) | + FPGA SerDes analog ön ucu | kablo, AFE |
| 5 | GT Far-End PMA (100) | AFE→FPGA kablo + AFE TX (FPGA, geleni yansıtır; AFE kendi verisini alıp doğrular) | FPGA PCS/IP işleme |
| 6 | GT Far-End PCS (110) | + FPGA PCS'ten geçiş | IP'nin transport'u |
| 2 | AFE JESD dijital loopback | AFE'nin link katmanı (JESD RX→TX) | AFE analog çekirdeği |
| 1 | AFE dijital loopback (DUC→DDC) | AFE dijital sinyal yolu, NCO'lar | JESD, SerDes, FPGA |

Strateji {{fig:d08}}'in altındaki kural: **içeriden dışarıya**. Önce 3
(saf FPGA içi — çalışmıyorsa kablonun suçu yok demektir), sonra 4, sonra
kabloyu dahil eden 5/6, sonra AFE tarafının 2 ve 1'i. Hangi halkada
bozuluyorsa, arıza son eklediğin dilimdedir. Versal'de loopback modu
GT'nin `CH[x]_LOOPBACK[2:0]` portundan seçilir (000 normal; kodlar
tabloda) — tasarımına bu portu bağlamayı bring-up *öncesinde* akıl etmek,
sahada JTAG'den mod değiştirebilmek demektir.

::: not
Far-end loopback'lerin az bilinen değeri: FPGA'yı **aynaya** çevirirler.
AFE "kendi kendine konuşurken" (kendi gönderdiğini alıp doğrularken)
FPGA'nın işlem katmanları denklemden çıkar — "AFE mi FPGA mı?" ikilemini
tek deneyle çözer.
:::

## IBERT ve eye scan: fiziksel katmanın gözü

Kilit gelmiyorsa ya da CRC'ler yürüyorsa, sorunun analog boyutunu ölçmek
gerekir. Versal GT'lerinde **IBERT** ayrı bir IP değil, transceiver'a
gömülü bir özelliktir: Vivado'nun **Serial I/O Analyzer**'ı (veya
ChipScoPy API'si) ile çalışma anında PRBS desenleri gönderir, BER ölçer
ve — en değerlisi — **2D eye scan** çizer: RX örnekleme noktası
yatay/dikey taranarak {{sec:4}}'te anlattığımız gözün gerçek fotoğrafı
çekilir.

Okuma rehberi: geniş, simetrik göz = sağlıklı kanal; yatay dar göz =
jitter/ISI (eşitleyici ayarlarına, kanal kaybına bak); dikey dar =
genlik/sonlandırma problemi; asimetrik/çift kenar = yansıma (empedans
süreksizliği, via stub). Lane'ler arasında gözler belirgin farklıysa
yerleşim/kablo farkı ara. IBERT'in PRBS'i **protokolsüz** çalışır — JESD
konfigürasyonundan bağımsız olarak "bu bakır 12 Gb/s taşıyabiliyor mu?"
sorusunun cevabıdır; {{fig:m02}}'deki PHY dalının ana aletidir.

## Semptom → sebep tablosu

{{sec:6}}–{{sec:7}}'nin kilit merdivenleri, debug'ın koordinat sistemidir:
*nerede takıldığı*, *neyin bozuk olduğunu* söyler.

| Semptom | İlk şüpheliler | İlk testler |
|---|---|---|
| GT PLL kilitlenmiyor | refclk yok/yanlış frekans; yerleşim kuralı ihlali ({{sec:14}}, >16.375G paylaşım) | refclk sayacını oku; clock chip kilitleri |
| SH lock yok (C) / CGS'de takılı (B) | polarite ters, lane eşleşmesi, eşitleme, hat kopuk | near-end 3→4; IBERT PRBS; SYNC~ elektriği (B) |
| SH lock var, EMB lock yok (C) | SYSREF frekans kuralı ({{sec:9}}), E/F uyumsuzluğu, EoEMB bekleme | SYSREF'i durdur/tetikle; K-E-F setini iki uçta karşılaştır |
| ILAS hatası (B) | K uyumsuz, lane sırası karışık, RBD dar | yakalanan ILAS konfigürasyonunu oku ({{sec:6}} saha notu) |
| CRC / kod hataları artıyor | sinyal bütünlüğü marjinal; sıcaklık; SYSREF spur kuplajı | eye scan; sıcaklık taraması; SYSREF'i sustur, fark var mı? |
| Link kalkıyor, veri kayık/yanlış kanalda | transport parametre uyuşmazlığı ({{sec:5}}); lane haritası | ILAS/register karşılaştır; bilinen desen (ramp) bas |
| Kanallar arası faz her açılışta farklı | deterministic latency kurulmadı: SYSREF perdesi atlandı/başarısız, RBD sınırda ({{sec:10}}) | SYSREF-LEMC faz register'ları; RBD marjini ölç |
| Sıcaklıkla düşen link | SYSREF penceresi kenarda ({{sec:9}}); eşitleyici marjı; RBD sınırı | SYSREF monitörünü sıcaklıkla logla; eye scan'i sıcak/soğuk çek |

## SYSREF kaymalarının teşhisi

En sinsi arıza ailesi, çünkü belirtisi *link katmanında değil* uygulama
katmanında çıkar (faz kayması, kanal tutarsızlığı) ve genelde aralıklıdır.
Teşhis zinciri:

1. **Monitörü oku** ({{sec:9}}): AFE'nin SYSREF konum/pencere raporu tam
   ortada mı, kenarda mı? Kenardaysa dur — suçluyu buldun.
2. **Sıcaklıkla tara**: pencere konumunu soğuk/sıcak logla. Kenara doğru
   *yürüyorsa*, kart gecikmeleri sıcaklıkla kayıyor demektir; clock chip'in
   SYSREF gecikme adımıyla ({{sec:11}}–{{sec:12}}: 25 ps / ~3 ps sınıfı)
   pencereyi ortala.
3. **Frekans kuralını doğrula**: f_SYSREF gerçekten LMFC/LEMC'nin tam
   böleni mü ({{sec:9}})? Hesabı registerlardan (varsayımdan değil) yap.
4. **Tek atım politikasını kontrol et**: SYSREF sürekli mi akıyor? IP'de
   SYSREF Always ne durumda ({{sec:14}})? "Hıçkıran link" reçetesini
   hatırla.

## Saha vakaları

::: saha
**Vaka 1 — "SH lock, ayda bir kartta gelmiyor."** Üretim hattında yüz
kartın ~üçü, ilk açılışta C linkini kuramıyor; güç çevrimiyle düzeliyor.
İz: GT reset state machine'i, clock chip'in PLL2 kilidini *beklemeden*
GT PLL reset'ini bırakıyormuş — refclk henüz kararsızken kilitlenmeye
çalışan LCPLL, bazı kartlarda yanlış frekansa oturuyor. Ders: {{sec:15}}
perde 1'in kilit bayrağı, perde 3'ün ön şartıdır; "genelde çalışıyor"
sıralar, istatistikle test edilmeden doğru sayılmaz. İkinci ders: hata
anında durum register'larını loglayan kod olmasaydı, "ayda bir"lik arıza
asla yakalanamazdı.
:::

::: saha
**Vaka 2 — "Kart ısınınca CRC sayacı yürüyor."** Laboratuvarda kusursuz
sistem, kapalı kasada 20 dakika sonra CRC hataları başlıyor. Eye scan
sıcakta da temiz — yani SerDes değil. SYSREF monitörü ise sıcaklıkla
pencere kenarına yürüyor ve arada bir *bir clock kayarak* yakalanıyor;
her kayma LEMC fazını bir periyot oynatıp linki sarsıyor. Kök neden:
SYSREF izi, device clock izinden farklı katmanda yönlendirilmiş —
sıcaklıkla farklı uzuyorlar. Çözüm katmanda değil registerda bulundu:
SYSREF gecikmesi pencere ortasına ayarlandı ve senkron sonrası SYSREF
susturuldu. Ders: {{sec:9}}'daki setup/hold penceresi teorik bir
incelik değil, sahada sıcaklıkla yürüyen gerçek bir sinyaldir.
:::

## Karar ağacı

Hepsini tek haritada toplayalım — semptomdan teste giden yol:

![Debug karar ağacı: her düğüm bir status register sorusudur; yapraklar ilgili bölüme ve alete yönlendirir.](../diagrams/mermaid/m02.mmd)

Bu ağacın gücü, {{sec:6}}–{{sec:7}}'nin kilit merdivenlerine yaslanması:
her soru bir register okumasıdır, her cevap hipotez uzayını yarılar. Ağaç
seni bir yaprağa götürdüğünde, o yaprağın bölümünü aç ve derinleş.

Debug da bitti. Geriye, tüm bu bilgiyi bir sonraki projeye taşınabilir
hale getirmek kalıyor: kontrol listesi, sözlük ve kaynakça.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- AMD, AM002 — loopback modları ve kodları, eye scan mimarisi.
- AMD, UG908 (Vivado Programming and Debugging) — IBERT / Serial I/O
  Analyzer akışı.
- AMD, PG242 — IP durum bayrakları, SYSREF Always.
- {{sec:6}}–{{sec:7}} ve {{sec:9}}–{{sec:10}}'un standart/datasheet
  kaynakları — kilit merdivenleri ve SYSREF mekanikleri.
- Saha vakaları: anonimleştirilmiş mühendislik deneyimi; teknik
  mekanizmaları yukarıdaki public kaynaklarla uyumludur.
- Toplu ve linkli liste: {{sec:19}}.

</details>
