# Bölüm 4 — Kalbin İçi: UltraScale+ PS IP'si

## Neden umursamalısın

Blok dizayndaki en büyük kutu — `zynq_ultra_ps_e`, bizim dizaynda `ps_ultra`
— aslında bir IP değil, çipin yarısıdır: dört A53, iki R5F, DDR denetleyici,
bütün sabit çevre birimleri. Yazılımını çalıştıracak her şey bu kutunun
içinde ve bu kutunun *ayarlarında* yaşar. UART hangi pinde, DDR kaç bit,
clock kaç MHz — hepsinin adresi burası.

## Kutuya çift tıklayınca: Re-customize IP

Diagram'da PS bloğuna çift tıkla:

[[adim: Open Block Design → ps_ultra bloğuna çift tık → Re-customize IP diyaloğu]]

Karşına çıkan pencere Vivado'nun en kalabalık diyaloglarındandır. Panik yok:
sol kenardaki **Page Navigator** haritan; yazılımcı olarak dört durağın var.

[[ekran: 08 | PS IP Re-customize — açılış görünümü
rozet 1: Page Navigator — sekmeler arası geçiş; dört durağın: I/O, Clock, DDR, PS-PL.
rozet 2: Blok şeması — PS'in iç dünyası; tıklanabilir bölgeler ilgili sayfaya götürür.
rozet 3: Cancel — bu pencereden çıkışın TEK doğru düğmesi (Bölüm 2'deki görgü kuralı).
]]

| Sayfa | Sorusu | Bölüm |
|---|---|---|
| I/O Configuration | Hangi çevre birimi açık, hangi pinde? | 5 |
| Clock Configuration | Hangi saat kaç MHz? | 5 |
| DDR Configuration | Bellek tipi, hızı, boyutu | 5 |
| PS-PL Configuration | PL'e açılan AXI kapıları, interrupt'lar | 6 |

Sekmelere dalmadan önce PS'in iç coğrafyasını bir kez kuşbakışı gör —
sekmelerin her biri bu haritanın bir bölgesini yönetir:

[[sema: sema-04-mpsoc-kusbakisi | Şema 4 — MPSoC PS kuşbakışı: APU/RPU, sabit çevre birimleri, DDR denetleyici, MIO/EMIO çıkış kapıları ve sağda PS-PL AXI pencereleri. Her bölge, Re-customize'daki bir sayfaya karşılık gelir.]]

## Board preset: bu yüzlerce ayarı kimse elle girmedi

PS'in binlerce parametresi var (gerçek sayı: demo projedeki PS'in CONFIG
dökümü 2600 satırın üzerinde — repo'da `assets/reports/ultrascale-ps-config-full.txt`
olarak duruyor). Bunları kimse tek tek girmez. Kart üreticisi, kartın
şemasına uygun ayar paketini **board preset** olarak yayınlar; donanımcı
projeyi kart tanımıyla (board part) açtığında Vivado bu preset'i tek
hamlede uygular. Demo projemizde de öyle oldu: `create_bd.tcl` içindeki
`apply_board_preset` satırı, ZCU102 kartının UART'ından DDR zamanlamalarına
kadar her şeyi getirdi.

Bunun pratikteki anlamı: PS ekranlarında gördüğün değerlerin çoğu kartın
fiziksel gerçekleridir. UART0'ın MIO 18-19'da olması bir tercih değil,
kartta o pinlere USB-UART köprüsünün lehimlenmiş olmasının sonucudur.
Donanımcı preset üstüne yalnızca projeye özgü dokunuşlar yapar (bir HPM
portu açmak, bir fabric clock eklemek gibi) — senin dikkatin de zaten o
dokunuşlarda olmalı.

:::derin-dalis
Preset'in ne olduğunu Tcl'den görmek istersen: PS hücresi seçiliyken
`get_property CONFIG.PSU__UART0__PERIPHERAL__ENABLE [get_bd_cells ps_ultra]`
gibi tekil sorgular atabilir ya da `list_property` ile tüm parametre
adlarını dökebilirsin (Ek A'da hazır reçetesi var). Fark analizi için
donanımcının projesindeki değerleri repo'daki referans dökümle
karşılaştırmak, "preset'ten kim ne değiştirmiş" sorusunu cevaplar.
:::

## RFSoC, MPSoC, ZCU111, ZCU102 — hangisi kimin nesi

Ekipteki kart ZCU111 (RFSoC), bu kılavuzun demo projesi ZCU102 (MPSoC).
İkisi arasında PS açısından fark **yok**: RFSoC = MPSoC'un PS'i + PL
tarafına eklenmiş RF veri dönüştürücüler (ADC/DAC dilimleri). PS IP'si
her ikisinde de aynı `zynq_ultra_ps_e`'dir; sekmeler, parametre adları,
MIO yapısı, clock ağacı birebir örtüşür. Bu bölümde ve 5-6-7'de öğrendiğin
her şey ZCU111 projesine aynen uygulanır.

RF tarafı (RF Data Converter IP'si, örnekleme, NCO ayarları) bilinçli
olarak kapsam dışıdır — o dünya serinin *RF Örnekleme Saha Kılavuzu*'nda
anlatılıyor; oradaki bilgiyle buradaki PS okuma becerisi birbirini tamamlar.

:::yazilima-yansimasi
PS konfigürasyonunun bütünü, .xsa içinde `psu_init.tcl` / `psu_init.c`
dosyalarına derlenir: FSBL (First Stage Boot Loader) açılışta bu init
kodunu koşturarak clock'ları, DDR'ı, MIO yönlendirmesini fiziksel olarak
kurar. Yani bu ekranda gördüğün her değer, boot'un ilk milisaniyelerinde
register yazmalarına dönüşür. "Kart JTAG'dan açılıyor ama SD boot'ta
çakılıyor" gibi vakalarda fark çoğu zaman bu init zincirindedir — kaynağı
da bu ekrandır.
:::

:::deneme id=deneme-4-1
**Hedef:** PS diyaloğunda yolunu bulduğunu kanıtla.

[[adim: Open Block Design → ps_ultra çift tık → Page Navigator]]

Demo 1'de PS diyaloğunu aç. Page Navigator'da kaç ana sayfa listeleniyor?
I/O Configuration sayfasına gir ve tabloda kaç sütun başlığı olduğuna bak.
Sonra **Cancel** ile çık.

::cozum::
2022.2'de Page Navigator: Switch To Advanced Mode kapalıyken PS UltraScale+
Block Design, I/O Configuration, Clock Configuration, DDR Configuration,
PS-PL Configuration sayfalarını gösterir. I/O tablosunda Peripheral,
I/O sütunları öndedir. Sayıları ezberlemek önemli değil; Cancel ile çıkma
refleksini ezberlemek önemli.
:::

:::ozet
- PS IP = çipin işlemci yarısının ayar paneli; çift tık → Re-customize.
- Dört durak: I/O, Clock, DDR, PS-PL. Gerisi donanımcının alanı.
- Değerlerin çoğu board preset'ten gelir; kartın fiziksel gerçeğidir.
- RFSoC'un PS'i = MPSoC'un PS'i; ZCU102 anlatımı ZCU111'i tam kapsar.
- Bu ekranın çıktısı psu_init olarak boot'ta koşar.
:::
