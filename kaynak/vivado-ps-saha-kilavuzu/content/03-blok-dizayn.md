# Bölüm 3 — Blok Dizaynı Okuma Sanatı

## Neden umursamalısın

Blok dizayn (block design, BD), donanımcının sistemi IP bloklarından kurduğu
tuvaldir — ve senin dört sorunun (IP'ler, adresler, clock'lar, interrupt'lar)
ilkinin cevabı doğrudan bu tuvalde durur. Karmaşık görünür; değildir.
Karayolu haritası gibi okunur: önce şehirleri (büyük bloklar), sonra
otoyolları (kalın çizgiler), en son sokakları (tek teller).

## IP kutusunun anatomisi

Her kutu bir IP'dir (Intellectual Property — hazır donanım bloğu). Kutunun
üstündeki ad **instance adı**dır ve önemlidir: `xparameters.h` tanımları bu
addan türetilir (`axi_timer_0` → `XPAR_AXI_TIMER_0_...`). Kenarlardaki
bağlantı noktaları iki türdür:

- **Arayüz (interface) pinleri** — kalın, tek sembol. Onlarca sinyalin
  paketlenmiş hâli; en sık göreceğin tür AXI arayüzüdür. Bir AXI bağlantısı
  şemada tek çizgidir ama altında adres, veri ve el sıkışma kanalları yatar.
- **Tek tel pinler** — ince çizgiler: clock, reset, interrupt gibi.

[[sema: sema-03-ip-anatomi | Şema 3 — IP kutusu okuma anahtarı: sol kenar erişim (S_AXI), alt kenar yaşam destek (clock/reset), sağ kenar dünyaya çıkış ve interrupt. Demo projedeki axi_uartlite_dbg örneği.]]

:::analoji
AXI arayüzünü bir USB kablosu gibi düşün: dışarıdan tek "bağlantı"dır ama
içinde besleme, veri ve el sıkışma telleri birlikte gider. Blok dizaynda
kalın çizgiyi gördüğünde tek tek telleri düşünme — "bu iki blok konuşuyor"
de, geç. Tellerin ayrıntısı donanımcının derdi.
:::

## Demo dizaynda rehberli tur

Aşağıdaki görsel, repo'daki `create_bd.tcl`'in kurduğu gerçek dizaynın
Vivado'dan alınmış hâlidir (`write_bd_layout` çıktısı). Zoom/pan ile gez:

[[bd: ultrascale-bd-full | Demo 1 blok dizaynı (ZCU102, gerçek `write_bd_layout` export'u). Solda ps_ultra (Zynq UltraScale+ PS), ortada axi_smc (SmartConnect), sağda dört AXI çevre birimi; altta reset bloğu, sağ üstte interrupt concat.]]

Aynı export'un PS'e yakın kırpımı — dört adımlık okuma sırasının ilk iki
durağı (PS + trafik göbeği) tek pencerede:

[[bd: ultrascale-bd-ps | PS-yakın kırpım: ps_ultra bloğunun M_AXI_HPM0_FPD kapısından axi_smc'ye (SmartConnect) giden kalın AXI çizgisi; sol altta pl_ps_irq0 ve pl_clk0 iğneleri.]]

Yukarıdaki export temiz bir vektör çizimdir; Vivado'da aynı dizayn şu
çerçevede karşına çıkar (Diagram penceresi, Flow Navigator ve Sources yan
yana):

[[ekran: 04 | Diagram penceresi — sistem BD tam görünüm (GUI çerçevesiyle)
rozet 1: Zoom Fit sonrası tüm dizayn tek karede — export'un GUI'deki karşılığı.
]]

Okuma sırası — her yeni dizaynda aynı dört adım:

1. **PS'i bul.** En büyük kutu, genelde `zynq_ultra_ps_e` (bizde `ps_ultra`).
   Sistemin güneşi budur; her şey etrafında döner.
2. **Trafik göbeğini bul.** PS'ten çıkan kalın AXI çizgisini izle:
   `axi_smc` (SmartConnect) ya da eski projelerde `axi_interconnect`.
   Görevi adres çözmek: PS'ten gelen tek yolu IP'lere dağıtır.
   Kaç IP'ye dağıttığına bak — sana görünen çevre birimi sayısı budur.
3. **Yaprakları say.** SmartConnect'in dallandığı kutular: `axi_gpio_led`,
   `axi_timer_0`, `axi_uartlite_dbg`, `axi_bram_ctrl_0`. Her biri Bölüm 7'de
   adres haritasında bir satır olacak.
4. **İnce telleri izle.** Interrupt telleri (`irq_concat` üzerinden
   `pl_ps_irq0`'a) ve clock/reset dağıtımı (`pl_clk0` ve `rst_ps...`
   bloğundan herkese).

## Gezinme ve sinyal takibi

Büyük dizaynlarda fare ile kaybolursun; şu üç araç kurtarır:

- **Zoom Fit** — Diagram araç çubuğundaki daire simgesi; tüm dizaynı
  pencereye sığdırır. Kaybolduğunda ilk refleks.
- **Arama** — Diagram içinde `Ctrl+F`. IP adı, port adı, net adı arar.
  "uart" yazıp Enter: doğrudan bloğa ışınlanırsın.
- **Seçim = vurgu** — bir çizgiye tıkladığında çizgi tüm uzunluğunca
  vurgulanır; kalabalık bölgelerde bir sinyalin nereden nereye gittiğini
  görmek için çizgiye tıkla, gerekirse `Ctrl` ile komşu segmentleri ekle.

[[ekran: 06 | Diagram içinde arama — Ctrl+F ile "uart"
rozet 1: Arama kutusu — IP, port ve net adlarında canlı filtre.
rozet 2: Sonuç satırı — seçince Diagram ilgili bloğa odaklanır.
]]

[[ekran: 05 | Sinyal takibi — interrupt demeti seçili
rozet 1: Seçili net irq_concat_dout — concat çıkışından ps_ultra/pl_ps_irq0'a giden demet, seçimle turuncu vurgulu.
rozet 2: irq_concat — üç interrupt telini tek demet yapan blok; giriş sırası ID'leri belirler (Bölüm 6).
rozet 3: System Net Properties — seçilen netin kimlik kartı: adı, sürücüsü (irq_concat/dout).
not: Seçim yalnızca görsel vurgudur; diske hiçbir şey yazılmaz.
]]

Hiyerarşi: donanımcılar kalabalık dizaynları klasörlere (hierarchy) katlar —
kutunun sol üstünde **+** işareti görürsen çift tıkla, içine girersin;
Diagram üstündeki yol şeridinden geri çıkarsın. Demo dizaynımız düz
(hiyerarşisiz) tutuldu; sahada +'lı kutu gördüğünde şaşırma yeter.

Bir bloğu seçtiğinde **Block Properties** paneli (sol alt) kimlik kartını
gösterir: VLNV (Vendor:Library:Name:Version — IP'nin tam kimliği), sürüm,
konfigürasyon parametreleri.

[[ekran: 07 | Block Properties — axi_gpio_led seçili
rozet 1: Block Properties paneli — Name: axi_gpio_led; instance adı, XPAR türetmelerinin kökü. VLNV ayrıntısı alttaki Properties/IP sekmelerinde.
rozet 2: Seçili blok Diagram'da turuncu çerçeveli — panel ile diyagram hep senkron.
]]

:::tuzak
Diagram'daki yerleşim (layout) anlam taşımaz. Donanımcı blokları estetik
için dizmiştir; fiziksel yerleşimle, sinyal gecikmesiyle, öncelikle ilgisi
yoktur. "GPIO, PS'e daha yakın çizilmiş, demek ki daha hızlı" türü çıkarımlar
yapma. Anlam çizgilerdedir, koordinatlarda değil.
:::

:::yazilima-yansimasi
Blok dizayndaki her AXI yaprağı, BSP'nde bir driver instance'ı olarak doğar:
`axi_gpio_led` → `XGpio`, `axi_timer_0` → `XTmrCtr`, `axi_uartlite_dbg` →
`XUartLite`. Dizaynda kutuyu görüp saymak, `xparameters.h`'ta kaç
`XPAR_*_BASEADDR` bekleyeceğini söyler. Kutu var ama XPAR yoksa: ya adres
atanmamış (Bölüm 7'deki unmapped tuzağı) ya da .xsa eski.
:::

:::deneme id=deneme-3-1
**Hedef:** Dört adımlık okuma sırasını gerçek dizaynda uygula.

[[adim: Flow Navigator → IP INTEGRATOR → Open Block Design]]

Demo 1'i aç ve şu üç soruyu Diagram'dan cevapla: (a) SmartConnect kaç
master portu kullanıyor (kaç IP'ye dağıtıyor)? (b) `irq_concat`'ın kaç
girişi dolu? (c) BRAM denetleyicisinin arkasındaki ikinci kutu ne?

::cozum::
(a) 4 — GPIO, Timer, Uartlite, BRAM denetleyici. (b) 3 — timer, uartlite,
gpio. (c) `axi_bram_ctrl_0_bram` (Block Memory Generator): denetleyici
AXI tarafını, bu blok ise gerçek RAM hücrelerini taşır. Denetleyici-bellek
ikilisi, "IP + arkasındaki kaynak" kalıbının en küçük örneğidir.
:::

:::ozet
- Instance adı → XPAR tanımlarının kökü; kalın çizgi → arayüz, ince → tek tel.
- Okuma sırası: PS → trafik göbeği → yapraklar → ince teller.
- Ctrl+F, Zoom Fit ve seçim-vurgu üçlüsü her dizaynda yolunu buldurur.
- Layout estetiktir; anlam çizgilerde.
:::
