# lab08-freertos — Task 8 solution: Your First FreeRTOS Application

## What it does

Three FreeRTOS tasks run together:

- **heartbeatTask** — toggles the DS50 LED (PS MIO23) on and off with a
  500 ms period using `vTaskDelay` (no busy loop).
- **statusTask** — prints a status line to UART every 2 seconds.
- **buttonHandlerTask** — waits with `xSemaphoreTake` on the binary
  semaphore that the ISR gives via `xSemaphoreGiveFromISR` when SW19
  (PS MIO22) is pressed; prints a line the moment a press occurs.

## How to build

1. Platform component: OS = **`freertos10_xilinx`**, processor
   `psu_cortexa53_0`; use the same `.xsa` you used in Tasks 0-7 (only the
   PS is needed, this lab does not use the PL).
2. Application component: empty application + this folder's `src/main.c`.
3. Build, load via JTAG, open the UART terminal at 115200-8N1.

## Console note

FreeRTOS labs use the standard `xil_printf` for console output (the BSP
routes STDOUT to UART0); you don't need `printf` or your own `uart_ps`
module.

## Expected output

While DS50 blinks steadily every 500 ms, a
`[Status] period N -- heartbeatTask and buttonHandlerTask running` line
streams in the terminal every 2 seconds; each time SW19 is pressed, a
`[Button] SW19 pressed (N times)` line is interleaved — the three jobs
run without interfering with one another, uninterrupted.
