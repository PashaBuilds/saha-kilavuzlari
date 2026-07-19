# lab05-timer — GÖREV 5: Timer ile Heartbeat

## Ne yapar

TTC0 kanal 0'ı (taban `0xFF11_0000`) 1 Hz periyodik interrupt üretecek
şekilde yapılandırır. Her tick'te `tickIsr()` koşar, DS50'yi (PS MIO23)
toggle'lar ve UART'a bir `tick N` satırı basılır — Görev 4'teki GIC
kalıbının aynısı, yalnız bu kez interrupt kaynağı buton değil timer'dır
(GIC ID **68**).

`src/uart_ps.h` ve `src/uart_ps.c`, lab02-uart'tan birebir kopyadır.

## Interval hesabı

TTC'nin Interval register'ı ZynqMP'de **32-bit**tir; tipik LPD saat
hızlarında (onlarca MHz) bu genişlik, **prescaler olmadan** 1 Hz kadar
düşük bir tick frekansına inmeye yeter:

```
Interval = (XPAR_XTTCPS_0_CLOCK_HZ / hedef_tick_hz) - 1
```

`XPAR_XTTCPS_0_CLOCK_HZ`, platformun `.xsa`'sından üretilen gerçek TTC
giriş saatidir — bu kodda hiçbir MHz değeri hard-code edilmemiştir;
`xparameters.h`'den okunur. Bu makronun değerini kendi platformunda
bulup hesabı kâğıt üzerinde yeniden yapmak Görev 5'in "Kendini sına"
sorusudur.

## Kurulum sırası

```c
XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
XTtcPs_CfgInitialize(&S_sTtc, ...);
XTtcPs_SetOptions(&S_sTtc, XTTCPS_OPTION_INTERVAL_MODE);
XTtcPs_SetInterval(&S_sTtc, uiInterval);
XTtcPs_EnableInterrupts(&S_sTtc, XTTCPS_IXR_INTERVAL_MASK);
/* --- Bölüm 7'nin beş adımlı GIC kalıbı, interrupt ID 68 --- */
XTtcPs_Start(&S_sTtc);
```

`tickIsr()` üç satırdır: durumu `XTtcPs_GetInterruptStatus` ile oku,
`XTtcPs_ClearInterruptStatus` ile alındı bilgisi ver ve `volatile`
bayrağı kur. UART'a yazmak ve LED'i toggle'lamak tamamen ana döngünün
işidir — ISR kısa kalır.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform**u (.xsa, standalone) seç.
2. Yeni bir **boş uygulama** projesi aç ve bu platforma bağla.
3. Bu klasördeki `src/` altındaki üç dosyayı (`uart_ps.h`, `uart_ps.c`,
   `main.c`) projenin `src/` klasörüne kopyala.
4. Projeyi **build** et, sonra JTAG üzerinden karta yükle ve çalıştır.

## Beklenen çıktı

```
--- TASK 5: Heartbeat via Timer ---
TTC0 channel 0, 1 Hz. DS50 beats like a heart.

tick 1
tick 2
tick 3
```

Terminalde saniyede tam bir yeni satır belirir; DS50 her tick'te
toggle'lanır ve 2 saniyede bir tam yanıp sönme çevrimi tamamlar —
düzenli, kesintisiz bir kalp atışı ritmi.
