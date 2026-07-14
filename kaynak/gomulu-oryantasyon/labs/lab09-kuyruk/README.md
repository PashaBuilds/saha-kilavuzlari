# lab09-kuyruk — Görev 9 çözümü: Queue ile Üretici/Tüketici

## Ne yapar

**producerTask** task'ı her 500 ms'de bir `ina226ReadBusVoltageMv()` ile
kartın VCCINT güç rayının bus gerilimini (mV) ölçer, zaman damgasıyla
birlikte bir `SMeasurementPacket` paketi olarak `xQueueSend` ile kuyruğa
koyar. **consumerTask** task'ı `xQueueReceive` ile bekler, paketi
biçimlendirip UART'a basar. UART'a yalnızca `consumerTask` yazdığı için
satırlar asla birbirine karışmaz — bu "doğal serileşme" mimarinin bir yan
faydasıdır, ayrıca kod içinde de vurgulanır.

## `ina226.h` / `ina226.c` — lab06 ile aynı modül

Bu modül, PS I2C0 → PCA9544A mux (U23, `0x75`) → kanal 0 → INA226
(`0x40`, VCCINT rayı) yolunu yürüyüp Bus Voltage yazmacını (`0x02`,
LSB 1.25 mV) okur; `ina226Init()` önce Manufacturer ID yazmacını
(`0xFE` → beklenen `0x5449`, ASCII "TI") doğrular. API sözleşmesi
`content/_gorev-zinciri.md`'de sabitlenmiştir:

```c
int ina226Init(void);
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);
```

Bu, Görev 6'nın (`lab06-i2c`) çözümüyle **aynı modüldür** — Görev 6 senin
sıranda henüz yazılmamışsa bile bu dosyalar sözleşmeye birebir uyar; Görev
6'yı tamamladığında iki kopyanın davranışı örtüşecek. PCA9544A kontrol
baytının (`0x04` = etkin + kanal 0) kaynağı `content/_arastirma-ek-E.md`'de
web ile teyitlidir.

## Nasıl derlenir

1. Platform component: OS = `freertos10_xilinx`, işlemci `psu_cortexa53_0`.
2. Application component: boş uygulama + bu klasördeki `src/main.c`,
   `src/ina226.h`, `src/ina226.c`.
3. Derle, JTAG ile yükle, UART terminalini 115200-8N1'de aç.

## Konsol notu

Bu lab da diğer FreeRTOS labları gibi konsol çıktısı için `xil_printf`
kullanır.

## Beklenen çıktı

Terminalde zaman damgalı mV satırları düzenli akar:

```
[    1500 ms] VCCINT =  852 mV
[    2000 ms] VCCINT =  851 mV
[    2500 ms] VCCINT =  852 mV
```

Üretici ve tüketici farklı hızlarda çalışsa da (örneğin tüketici UART
yazarken kısa süre gecikse de) kuyruk tampon görevi görür; veri kaybolmaz —
kuyruk gerçekten dolarsa Üretici bunu `[Uretici] kuyruk dolu` satırıyla
açıkça bildirir, sessizce veri kaybetmez.
