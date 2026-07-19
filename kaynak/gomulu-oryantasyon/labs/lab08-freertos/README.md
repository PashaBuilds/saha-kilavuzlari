# lab08-freertos — Görev 8: İlk FreeRTOS Uygulaman

## Ne yapar

Üç FreeRTOS task'ı birlikte çalışır:

- **heartbeatTask** — DS50 LED'ini (PS MIO23) `vTaskDelay` ile 500 ms
  periyotla yakıp söndürür (busy loop yok).
- **statusTask** — her 2 saniyede bir UART'a durum satırı basar.
- **buttonHandlerTask** — SW19 (PS MIO22) basıldığında ISR'nin
  `xSemaphoreGiveFromISR` ile verdiği binary semaphore'u
  `xSemaphoreTake` ile bekler; basış olduğu anda bir satır basar.

## Nasıl derlenir

1. Platform component: OS = **`freertos10_xilinx`**, işlemci
   `psu_cortexa53_0`; Görev 0-7'de kullandığın `.xsa`'nın aynısını
   kullan (yalnızca PS gerekir, bu lab PL kullanmaz).
2. Application component: boş uygulama + bu klasördeki `src/main.c`.
3. Build et, JTAG ile yükle, UART terminalini 115200-8N1 ile aç.

## Konsol notu

FreeRTOS lab'leri konsol çıktısı için standart `xil_printf` kullanır
(BSP, STDOUT'u UART0'a yönlendirir); `printf`'e ya da kendi `uart_ps`
modülüne ihtiyacın yok.

## Beklenen çıktı

DS50 her 500 ms'de bir düzenli yanıp sönerken, terminale her 2 saniyede
bir `[Status] period N -- heartbeatTask and buttonHandlerTask running`
satırı akar; SW19'a her basışta araya bir
`[Button] SW19 pressed (N times)` satırı girer — üç iş birbirini
engellemeden, kesintisiz yürür.
