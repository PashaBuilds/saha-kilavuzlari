# Bölüm 7 — Adres Haritası: Address Editor'dan xparameters.h'a

## Neden umursamalısın

`Xil_Out32(0xA0010000, ...)` yazdığında o sayının doğru olduğunu sana kim
söylüyor? Bu bölümün cevabı: Address Editor → .xsa → xparameters.h zinciri.
Zinciri bilen, "yanlış adrese yazıyorum" şüphesini iki dakikada kapatır;
bilmeyen bus hatasını driver'da arar.

## Address Editor: kim nerede oturuyor

[[adim: Open Block Design → Window → Address Editor]]

Address Editor, dizayndaki her master'ın (bizde PS'in `Data` uzayı) hangi
slave'i hangi aralıkta gördüğünü listeler. Sütunlar: satır başına bir
**segment** — slave'in bir penceresi; **Master Base Address** — pencerenin
başladığı adres; **Range** — boyu; **High Address** — bittiği yer.

Demo 1'in gerçek haritası (repo'daki `ultrascale-adres-haritasi.md`
raporundan, tek kaynağı `assign_bd_address` çıktısı):

| Master uzayı | Segment | Base | High | Aralık |
|---|---|---|---|---|
| `/ps_ultra/Data` | `SEG_axi_gpio_led_Reg` | `0xA0000000` | `0xA000FFFF` | 64K |
| `/ps_ultra/Data` | `SEG_axi_timer_0_Reg` | `0xA0010000` | `0xA001FFFF` | 64K |
| `/ps_ultra/Data` | `SEG_axi_uartlite_dbg_Reg` | `0xA0020000` | `0xA002FFFF` | 64K |
| `/ps_ultra/Data` | `SEG_axi_bram_ctrl_0_Mem0` | `0xA0030000` | `0xA0031FFF` | 8K |

[[ekran: 17 | Address Editor — demo projenin haritası
rozet 1: Network ağacı — /ps_ultra/Data uzayı altında dört PL segmenti.
rozet 2: Master Base Address sütunu — 0xA000_0000'dan itibaren 64K'lık dilimler.
rozet 3: Range/High — pencerenin boyu ve son adresi; BRAM 8K ile diğerlerinden küçük.
]]

"Neden 0xA000_0000?" — UltraScale+'ta HPM0 FPD kapısının arkasına açılan
hazır pencerelerden ilki bu bölgededir (HPM'ler 0xA000_0000–0xB000_0000
civarını ve daha yukarıda ikinci bir bölgeyi PL'e ayırır). Vivado otomatik
atamada IP'leri bu pencereye ardışık dizer. Donanımcı adresleri elle de
seçebilir; o yüzden haritayı her projede yeniden okumak zorundasın —
"GPIO hep 0xA0000000'dadır" diye ezber yapılmaz.

### Unmapped: en sinsi satır

Bir slave bağlıdır ama adresi atanmamıştır — Address Editor'da **Unmapped
Slaves** altında görünür. Sonuç: o IP fiziksel olarak vardır, yazılımdan
**erişilemez** ve xparameters.h'ta hiç doğmaz. Validate Design çoğu durumda
bunu yakalayıp uyarır ama uyarı görmezden gelinebilir; teslim aldığın
projede Address Editor'ı açıp unmapped satır aramak otuz saniyelik sigortadır.

### Çakışma: validate'in işi

İki segment aynı aralığa elle atanırsa **adres çakışması** doğar; Vivado
bunu `validate_bd_design` (GUI'de F6 / Validate Design düğmesi) sırasında
hata olarak yakalar. Demo projelerin validate çıktıları temizdir
(`assets/reports/*-validate.txt`). Senin refleksin: teslim alınan projede
donanımcının validate'i temiz geçtiğini sormak — geçmiyorsa adres haritasına
güvenilmez.

[[ekran: 18 | Validate Design — başarı diyaloğu
rozet 1: Validation successful mesajı — adres çakışması ve bağlantı hatası yok demek.
]]

## Export Hardware: .xsa'nın doğduğu an

[[adim: File → Export → Export Hardware...]]

Sihirbaz iki kritik soru sorar: platform tipi (**Fixed** — donanım sabit,
tipik teslimat bu) ve çıktı kapsamı: **Pre-synthesis** (yalnız donanım
tarifi — analiz ve erken yazılım geliştirme için yeterli) ya da **Include
bitstream** (implementasyon bitmişse, PL imajı da pakete girer).

[[ekran: 19 | Export Hardware — sihirbaz açılışı
rozet 1: Fixed platform seçimi — donanım tarifi sabit, Vitis platformu bunun üstüne kurulur.
]]

[[ekran: 20 | Export Hardware — çıktı kapsamı
rozet 1: Pre-synthesis — sentez gerektirmez; adresler, clock'lar, IP listesi tam.
rozet 2: Include bitstream — PL imajını da paketler; boot imajı üretecek ekip için gerekli.
]]

:::derin-dalis
.xsa bir ZIP arşividir; uzantıyı değiştirmeden `unzip -l` ile içine
bakabilirsin. Demo 1'in gerçek export'unda (repo: `ultrascale-demo.xsa`)
öne çıkan içerik: `sistem.hwh` — donanım tarifinin XML'i, xparameters'ın
ham kaynağı; `psu_init.c/.tcl` — Bölüm 4'te anlattığımız boot init'i;
`sistem_bd.tcl` — blok dizaynın yeniden üretim scripti. Bitstream'li
export'ta bunlara `.bit` eklenir. Vitis "platform" dediğinde, bu arşivin
üstüne BSP ve boot bileşenlerini giydirilmiş halini kastediyoruz.
:::

## Zincirin kapanışı: xparameters.h

Vitis platformu .xsa'dan doğarken her adreslenmiş IP için tanımlar üretir.
Zincir uçtan uca şöyle görünür:

[[sema: sema-09-adres-zinciri | Şema 9 — Aynı sayının dört durağı: Address Editor satırı, .hwh kaydı, xparameters.h tanımı, koddaki kullanım. Kaynak hep en üst durak.]]

Demo 1 haritasının xparameters.h karşılığı (adresler yukarıdaki tablodan;
tanım adları instance adlarından türetilir):

```c
#define XPAR_AXI_GPIO_LED_BASEADDR     0xA0000000
#define XPAR_AXI_TIMER_0_BASEADDR      0xA0010000
#define XPAR_AXI_UARTLITE_DBG_BASEADDR 0xA0020000
#define XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR 0xA0030000
```

:::tuzak
Adres uyuşmazlığının bir numaralı nedeni bayat .xsa'dır: donanımcı adresi
değiştirir, sana yeni .xsa göndermeyi unutur; senin xparameters.h'ın eski
haritayı taşır. Kod derlemeye devam eder — sayılar sabittir — ama artık
yanlış kapıya vurursun. Belirti tipik olarak bus hatası değil *sessiz
yanlış davranıştır* (başka IP'nin register'ına yazarsın). Teslim aldığın
her donanım değişikliğinde ilk soru: ".xsa'nın tarihi ne?"
:::

:::yazilima-yansimasi
Bu bölümün tamamı zaten yazılıma yansıma; tek cümlelik damıtılmışı şu:
**xparameters.h'taki her adres, Address Editor'daki bir satırın kopyasıdır
— şüphelendiğinde karşılaştıracağın iki şey bu ikisidir.** Linux tarafında
aynı satırlar device tree'ye `reg = <0x0 0xA0000000 0x0 0x10000>` biçiminde
düşer; generic UIO/devmem denemelerinde de aynı base'i kullanırsın.
:::

:::deneme id=deneme-7-1
**Hedef:** Haritayı iki kaynaktan doğrula.

[[adim: Window → Address Editor]]

Demo 1'de Address Editor'ı aç, dört segmentin base adresini not et. Sonra
GUI'yi hiç kullanmadan aynı bilgiyi Tcl'den çek (Ek A'daki reçete):

```tcl
vivado -mode batch -source vivado/export_visuals.tcl -tclargs rapor ultrascale
```

`assets/reports/ultrascale-adres-haritasi.md` ile ekrandaki tablo birebir
aynı mı?

::cozum::
Aynı olmalı — ikisi de aynı BD veritabanından okur. Bu deneme sana iki şey
kazandırır: (1) GUI ve Tcl'in aynı gerçeğin iki görünümü olduğu iç görüsü,
(2) donanımcıdan proje geldiğinde Vivado'yu hiç açmadan adres haritası
raporu çıkarma yeteneği.
:::

:::ozet
- Address Editor = master başına segment listesi; base/range/high oku.
- Unmapped slave = fiziksel var, yazılıma yok. Otuz saniyelik kontrol.
- Validate Design çakışmaları yakalar; temiz validate şarttır.
- Export Hardware: Fixed + (Pre-synthesis | bitstream'li). .xsa bir ZIP'tir.
- xparameters.h türetilmiştir; şüphede Address Editor ile karşılaştır,
  bayat .xsa'ya dikkat.
:::
