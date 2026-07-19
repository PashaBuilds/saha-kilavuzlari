# lab06-i2c — GÖREV 6: I2C ile Gerçek Bir Çiple Konuş

## Ne yapar

PS I2C0 (MIO14-15) üzerinden gerçek bir I2C ağacına iniyoruz:

```
PS I2C0  →  PCA9544A mux (U23, adres 0x75), kanal 0  →  INA226 (adres 0x40, VCCINT)
```

`ina226Init()`, I2C0'ı 100 kHz'e yapılandırır, mux'a kanal-0 seçim
baytını yazar, sonra INA226'nın Manufacturer ID register'ını (0xFE)
okuyup **0x5449** ("TI") ile doğrular. Kimlik uyuşmazsa `main.c` ölçüme
hiç geçmez — mux/adres/kablolama sorunu, herhangi bir ölçüm alınmadan
ÖNCE net bir hata mesajıyla yakalanır. Doğrulama geçince Bus Voltage
register'ı (0x02) saniyede bir okunur, LSB = 1.25 mV ile milivolta
çevrilir ve UART'a basılır.

`ina226.h/.c` API'si, `_gorev-zinciri.md` sözleşmesiyle birebir aynıdır:

```c
int ina226Init(void);
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);
```

`src/uart_ps.h` ve `src/uart_ps.c`, lab02-uart'tan birebir kopyadır.

## PCA9544A kontrol baytı

TI PCA9544A datasheet'inin kontrol register'ında (SCPS146G, §8.6
Register Map, Tablo 8-1) bit 2 "enable", bit 1:0 kanal numarasıdır:

| B2 | B1 | B0 | Komut |
|---|---|---|---|
| 0 | X | X | Kanal seçili değil (POR sonrası varsayılan) |
| 1 | 0 | 0 | **Kanal 0 etkin** |
| 1 | 0 | 1 | Kanal 1 etkin |
| 1 | 1 | 0 | Kanal 2 etkin |
| 1 | 1 | 1 | Kanal 3 etkin |

Kanal 0'ı seçen bayt: **0x04** (`0b0000_0100`). Teyit notu ve kaynak:
`content/_arastirma-ek-D.md` §D.4.

## Register pointer kalıbı

INA226 çok register'lı bir aygıttır: önce hangi register'ı istediğini
belirten tek baytlık bir "pointer" yazarsın, sonra o register'ın
içeriğini ayrı bir okuma işlemiyle alırsın. `ina226RegRead()` bu iki
adımı sarmalar (`XIicPs_MasterSendPolled` + `XIicPs_MasterRecvPolled`)
ve gelen 2 baytı big-endian (MSB önce) birleştirir.

## Sonsuz bekleme yasak

Bölüm 12'nin savunmacı programlama dersi burada erkenden devreye girer:
`i2cSendLimited()` / `i2cRecvLimited()`, her I2C işlemini en fazla
**5 kez** (`I2C_DENEME_SINIRI`) dener; denemeler arasında kısa bir
bekleme vardır (`XIicPs_BusIsBusy` kontrolüyle birlikte). Beş deneme de
başarısız olursa fonksiyon hata döner — donanım hiç cevap vermese bile
program asla sonsuza dek asılı kalmaz.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform**u (.xsa, standalone) seç.
2. Yeni bir **boş uygulama** projesi aç ve bu platforma bağla.
3. Bu klasördeki `src/` altındaki beş dosyayı (`uart_ps.h`,
   `uart_ps.c`, `ina226.h`, `ina226.c`, `main.c`) projenin `src/`
   klasörüne kopyala.
4. Projeyi build et ve JTAG üzerinden karta yükleyip çalıştır.

## Beklenen çıktı

```
--- TASK 6: Talk to a Real Chip over I2C ---
PS I2C0 -> PCA9544A(0x75) channel 0 -> INA226(0x40)

INA226 identity verified (0x5449). Measurement starting.

VCCINT = 851 mV
VCCINT = 849 mV
VCCINT = 850 mV
```

VCCINT nominal 0.85 V'tur; değer kartın anlık yüküne göre birkaç mV
oynayabilir ama 850 mV civarında seyretmelidir. Saniyede bir yeni satır
gelir.
