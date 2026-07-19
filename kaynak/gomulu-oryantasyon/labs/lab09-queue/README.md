# lab09-queue — Görev 9 çözümü: Queue ile Producer/Consumer

## Ne yapar

**producerTask**, kartın VCCINT güç rayının bus gerilimini (mV) her
500 ms'de bir `ina226ReadBusVoltageMv()` ile ölçer ve zaman damgasıyla
birlikte `SMeasurementPacket` paketi olarak `xQueueSend` ile kuyruğa
koyar. **consumerTask**, `xQueueReceive` ile bekler, paketi biçimler ve
UART'a basar. UART'a yalnızca `consumerTask` yazdığı için satırlar asla
iç içe geçmez — bu "doğal serileştirme" mimarinin yan kazancıdır ve
kodda da vurgulanır.

## `ina226.h` / `ina226.c` — lab06 ile aynı modül

Bu modül PS I2C0 → PCA9544A mux (U23, `0x75`) → kanal 0 → INA226
(`0x40`, VCCINT rayı) yolunu yürür ve Bus Voltage register'ını (`0x02`,
LSB 1.25 mV) okur; `ina226Init()` önce Manufacturer ID register'ını
doğrular (`0xFE` → beklenen `0x5449`, ASCII "TI"). API sözleşmesi
`content/_gorev-zinciri.md`'de sabittir:

```c
int ina226Init(void);
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);
```

Bu, Görev 6'nın (`lab06-i2c`) çözümüyle **aynı modüldür** — kendi
sıralamanda Görev 6 henüz yazılmamış olsa bile bu dosyalar sözleşmeye
birebir uyar; Görev 6'yı tamamladığında iki kopyanın davranışı örtüşür.
PCA9544A kontrol baytının (`0x04` = enable + kanal 0) kaynağı
`content/_arastirma-ek-E.md`'de web aramasıyla teyitlidir.

## Nasıl derlenir

1. Platform component: OS = `freertos10_xilinx`, işlemci
   `psu_cortexa53_0`.
2. Application component: boş uygulama + bu klasördeki `src/main.c`,
   `src/ina226.h`, `src/ina226.c`.
3. Build et, JTAG ile yükle, UART terminalini 115200-8N1 ile aç.

## Konsol notu

Diğer FreeRTOS lab'leri gibi bu lab de konsol çıktısı için `xil_printf`
kullanır.

## Beklenen çıktı

Terminale düzenli aralıklarla zaman damgalı mV satırları akar:

```
[    1500 ms] VCCINT =  852 mV
[    2000 ms] VCCINT =  851 mV
[    2500 ms] VCCINT =  852 mV
```

Producer ile consumer farklı hızlarda koşsa bile (örneğin consumer
UART'a yazarken kısa süre geride kalsa), kuyruk tampon görevi görür;
veri kaybolmaz — kuyruk gerçekten dolarsa Producer bunu sessizce veri
atmak yerine `[Producer] queue full, this measurement was dropped`
satırıyla açıkça bildirir.
