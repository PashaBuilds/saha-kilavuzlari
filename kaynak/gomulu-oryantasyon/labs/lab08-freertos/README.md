# lab08-freertos — Görev 8 çözümü: İlk FreeRTOS Uygulaman

## Ne yapar

Üç FreeRTOS task'ı birlikte çalışır:

- **heartbeatTask** — DS50 LED'ini (PS MIO23) 500 ms periyotla `vTaskDelay`
  ile yakıp söndürür (boş döngü yok).
- **statusTask** — her 2 saniyede bir UART'a bir durum satırı basar.
- **buttonHandlerTask** — SW19 butonuna (PS MIO22) basıldığında ISR'in
  `xSemaphoreGiveFromISR` ile verdiği ikili (binary) semaforu
  `xSemaphoreTake` ile bekler; basış anında bir satır basar.

## Nasıl derlenir

1. Platform component: OS = **`freertos10_xilinx`**, işlemci
   `psu_cortexa53_0`; Görev 0-7'de kullandığın aynı `.xsa`'dan (yalnızca PS
   yeterli, bu lab PL kullanmaz).
2. Application component: boş uygulama + bu klasördeki `src/main.c`.
3. Derle, JTAG ile yükle, UART terminalini 115200-8N1'de aç.

## Konsol notu

FreeRTOS lablarında konsol çıktısı için standart `xil_printf` kullanılır
(BSP'nin STDOUT'u UART0'a bağlar); `printf` ya da kendi `uart_ps` modülün
gerekmez.

## Beklenen çıktı

DS50 düzenli 500 ms'de bir yanıp sönerken terminalde her 2 saniyede bir
`[Durum] N. periyot ...` satırı akar; SW19'a her basışında araya
`[Buton] SW19 basildi (N. kez)` satırı girer — üç iş birbirini bozmadan,
kesintisiz çalışır.
