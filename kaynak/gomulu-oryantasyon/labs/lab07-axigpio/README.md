# lab07-axigpio — Görev 7 çözümü: PL'deki IP ile Konuş

## Ne yapar

PL (programlanabilir lojik) tarafında ekipçe hazırlanmış bir bitstream'de
duran bir **AXI GPIO** IP'sinin `GPIO_LED[7:0]` çıkışlarına (kartın 8
kullanıcı LED'i: DS11–DS18) `volatile` pointer ile doğrudan erişip 8 LED'de
soldan sağa yürüyen ışık oluşturur. `main.c`'nin sonundaki yorum bloğu, aynı
işi Xilinx'in hazır `XGpio` sürücüsüyle yapmanın nasıl görüneceğini gösterir.

## Ön koşul — donanım tarafı

Bu lab, **hazır bir .xsa/bitstream** ile çalışır; donanım tarafı (Vivado
tasarımı, IP entegrasyonu, bitstream üretimi) ekipçe temin edilir. Bu
kaynak dosyaların çalışması için tasarımda şu varsayımlar doğru olmalı:

- Bir **AXI GPIO** IP'si (v2.0, PG144) vardır ve çıkışları PL'deki
  `GPIO_LED[7:0]` pinlerine (DS11–DS18) bağlıdır.
- IP tek kanal (Enable Dual Channel = 0) olarak yapılandırılmış, 8 bit
  genişliğindedir.
- IP'nin Vivado'daki instance adı bu lab'da **`axi_gpio_0`** varsayıldı.
  Kendi projende farklı bir isim görürsen (`led_gpio`, `axi_gpio_led` gibi),
  `main.c`'deki `XPAR_AXI_GPIO_0_BASEADDR` makrosunu kendi projenin
  `xparameters.h`'inde göreceğin gerçek isimle değiştir — bu, Görev 7'nin
  "kendini sına" sorularından birinin tam da konusu.

## Nasıl derlenir

1. Vitis Unified IDE'de ekipten aldığın `.xsa` dosyasından bir **platform
   component** oluştur (OS: `standalone`, işlemci: `psu_cortexa53_0`).
2. Bir **application component** oluştur; şablon olarak boş (Empty)
   uygulamayı seç, ardından bu klasördeki `src/main.c`'yi projenin `src/`
   dizinine kopyala.
3. Projeyi derle; `xparameters.h` platformdan otomatik üretilir — içinde
   `XPAR_AXI_GPIO_0_BASEADDR` (ya da IP'nin gerçek instance adına göre
   türetilmiş eşdeğeri) satırını bulmalısın. Yoksa Adım 2'deki notu
   uygula: doğru makro adını kendi `xparameters.h`'inden al.
4. JTAG üzerinden karta yükle, UART terminalini 115200-8N1'de aç.

## Beklenen çıktı

8 kullanıcı LED'inde (DS11–DS18) soldan sağa doğru tek tek yanan, 150 ms
aralıklarla ilerleyen bir yürüyen ışık deseni; aynı anda terminalde
`LED deseni: 0x01`, `0x02`, `0x04` ... satırları akar.
