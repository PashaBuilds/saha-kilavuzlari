# lab05-timer — GÖREV 5: Timer ile Kalp Atışı

## Ne yapar

TTC0 kanal 0'ı (taban `0xFF11_0000`) 1 Hz'de periyodik kesme üretecek
şekilde kurar. Her tikte `tickIsr()` çalışır, DS50'yi (PS MIO23) tersine
çevirir ve UART'a `tick N` satırı bastırır — Görev 4'teki GIC deseninin
aynısı, bu sefer kesme kaynağı buton değil zamanlayıcı (GIC ID **68**).

`src/uart_ps.h` ve `src/uart_ps.c`, lab02-uart'tan birebir kopyadır.

## Interval hesabı

TTC'nin Interval yazmacı ZynqMP'de **32-bit**'tir; tipik LPD saat
hızlarında (onlarca MHz) bu genişlik 1 Hz gibi düşük bir tik frekansına
**prescaler'sız** ulaşmaya yeter:

```
Interval = (XPAR_XTTCPS_0_CLOCK_HZ / hedef_tick_hz) - 1
```

`XPAR_XTTCPS_0_CLOCK_HZ`, platformun `.xsa`'sından üretilen gerçek TTC giriş
saatidir — bu kodda elle bir MHz rakamı varsayılmıyor; `xparameters.h`'tan
okunuyor. Kendi platformunda bu makronun değerini bulup hesabı kâğıt
üzerinde tekrarlamak Görev 5'in "kendini sına" sorusudur.

## Kurulum sırası

```c
XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
XTtcPs_CfgInitialize(&S_sTtc, ...);
XTtcPs_SetOptions(&S_sTtc, XTTCPS_OPTION_INTERVAL_MODE);
XTtcPs_SetInterval(&S_sTtc, uiInterval);
XTtcPs_EnableInterrupts(&S_sTtc, XTTCPS_IXR_INTERVAL_MASK);
/* --- Bölüm 7'nin beşli GIC deseni, kesme ID 68 --- */
XTtcPs_Start(&S_sTtc);
```

`tickIsr()` üç satırdır: `XTtcPs_GetInterruptStatus` ile durumu oku,
`XTtcPs_ClearInterruptStatus` ile ack'le, `volatile` bayrağı set et. UART
yazma ve LED çevirme işi tamamen ana döngüde — ISR kısa kalır.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform** (.xsa, standalone) seçilir.
2. Yeni bir **boş (empty) uygulama** projesi açılır ve bu platforma bağlanır.
3. Bu klasördeki `src/` altındaki üç dosya (`uart_ps.h`, `uart_ps.c`,
   `main.c`) projenin `src/` klasörüne kopyalanır.
4. Proje derlenir (Build) ve JTAG üzerinden karta yüklenip çalıştırılır.

## Beklenen çıktı

```
--- GOREV 5: Timer ile Kalp Atisi ---
TTC0 kanal 0, 1 Hz. DS50 kalp gibi atiyor.

tick 1
tick 2
tick 3
```

Terminalde tam olarak saniyede bir yeni satır akar; DS50 her tikte tersine
döner, yani 2 saniyede bir tam bir yanıp-sönme çevrimi tamamlar — düzenli,
kesintisiz bir kalp atışı ritmi.
