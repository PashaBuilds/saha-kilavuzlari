# lab06-i2c — GÖREV 6: I2C ile Gerçek Bir Çiple Konuş

## Ne yapar

PS I2C0 (MIO14-15) üzerinden gerçek bir I2C ağacına giriyoruz:

```
PS I2C0  →  PCA9544A mux (U23, adres 0x75), kanal 0  →  INA226 (adres 0x40, VCCINT)
```

`ina226Init()` I2C0'ı 100 kHz'de kurar, mux'a kanal-0 seçim baytını
yazar, sonra INA226'nın Manufacturer ID yazmacını (0xFE) okuyup **0x5449**
("TI") ile doğrular. Kimlik tutmazsa `main.c` hiç ölçüme geçmez — mux/adres/
kablolama sorununu ölçümden ÖNCE, net bir hata mesajıyla yakalarız.
Doğrulama geçtikten sonra saniyede bir Bus Voltage yazmacı (0x02) okunur,
LSB = 1.25 mV ile milivolt'a çevrilir ve UART'a basılır.

`ina226.h/.c` API'si `_gorev-zinciri.md` sözleşmesiyle birebir:

```c
int ina226Init(void);
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);
```

`src/uart_ps.h` ve `src/uart_ps.c`, lab02-uart'tan birebir kopyadır.

## PCA9544A kontrol baytı

TI PCA9544A datasheet'inin (SCPS146G, §8.6 Register Map, Table 8-1) kontrol
yazmacında bit 2 "enable", bit 1:0 kanal numarasıdır:

| B2 | B1 | B0 | Komut |
|---|---|---|---|
| 0 | X | X | Hiçbir kanal seçili değil (POR sonrası varsayılan) |
| 1 | 0 | 0 | **Kanal 0 etkin** |
| 1 | 0 | 1 | Kanal 1 etkin |
| 1 | 1 | 0 | Kanal 2 etkin |
| 1 | 1 | 1 | Kanal 3 etkin |

Kanal 0'ı seçen bayt: **0x04** (`0b0000_0100`). Doğrulama notu ve kaynak:
`content/_arastirma-ek-D.md` §D.4.

## Register pointer deseni

INA226 çok yazmaçlı bir cihazdır: önce tek baytlık bir "pointer" yazarak
hangi yazmacı istediğini söylersin, ardından ayrı bir okuma işlemiyle o
yazmacın içeriğini alırsın. `ina226RegRead()` bu iki adımı
(`XIicPs_MasterSendPolled` + `XIicPs_MasterRecvPolled`) sarmalar ve gelen
2 baytı big-endian (MSB önce) birleştirir.

## Sonsuz bekleme yasak

Bölüm 12'nin savunmacı programlama dersi burada erken devreye giriyor:
`i2cSendLimited()` / `i2cRecvLimited()` her I2C işlemini en fazla
**5 kez** dener (`I2C_DENEME_SINIRI`), aralarında kısa bir bekleme
(`XIicPs_BusIsBusy` kontrolüyle birlikte) yapar. Beş denemede de
başarısız olursa fonksiyon hata döner — donanım hiç yanıt vermese bile
program sonsuza kadar takılı kalmaz.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform** (.xsa, standalone) seçilir.
2. Yeni bir **boş (empty) uygulama** projesi açılır ve bu platforma bağlanır.
3. Bu klasördeki `src/` altındaki beş dosya (`uart_ps.h`, `uart_ps.c`,
   `ina226.h`, `ina226.c`, `main.c`) projenin `src/` klasörüne kopyalanır.
4. Proje derlenir (Build) ve JTAG üzerinden karta yüklenip çalıştırılır.

## Beklenen çıktı

```
--- GOREV 6: I2C ile Gercek Bir Ciple Konus ---
PS I2C0 -> PCA9544A(0x75) kanal 0 -> INA226(0x40)

INA226 kimligi dogrulandi (0x5449). Olcum basliyor.

VCCINT = 851 mV
VCCINT = 849 mV
VCCINT = 850 mV
```

VCCINT nominal 0.85 V'tir; kartın anlık yüküne göre değer birkaç mV
oynayabilir, ama 850 mV civarında akmalıdır. Saniyede bir yeni satır gelir.
