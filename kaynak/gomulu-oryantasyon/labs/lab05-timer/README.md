# lab05-timer — TASK 5: Heartbeat via Timer

## What it does

Configures TTC0 channel 0 (base `0xFF11_0000`) to generate a periodic
interrupt at 1 Hz. On every tick, `tickIsr()` runs, toggles DS50 (PS
MIO23), and prints a `tick N` line to UART — the same GIC pattern as
Task 4, except this time the interrupt source is not the button but the
timer (GIC ID **68**).

`src/uart_ps.h` and `src/uart_ps.c` are exact copies from lab02-uart.

## Interval calculation

The TTC's Interval register is **32-bit** on the ZynqMP; at typical LPD
clock speeds (tens of MHz), this width is sufficient to reach a tick
frequency as low as 1 Hz **without a prescaler**:

```
Interval = (XPAR_XTTCPS_0_CLOCK_HZ / target_tick_hz) - 1
```

`XPAR_XTTCPS_0_CLOCK_HZ` is the actual TTC input clock generated from the
platform's `.xsa` — no MHz figure is hardcoded in this code; it is read
from `xparameters.h`. Finding this macro's value on your own platform and
reproducing the calculation on paper is Task 5's "Self-Check" question.

## Setup order

```c
XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
XTtcPs_CfgInitialize(&S_sTtc, ...);
XTtcPs_SetOptions(&S_sTtc, XTTCPS_OPTION_INTERVAL_MODE);
XTtcPs_SetInterval(&S_sTtc, uiInterval);
XTtcPs_EnableInterrupts(&S_sTtc, XTTCPS_IXR_INTERVAL_MASK);
/* --- Chapter 7's five-step GIC pattern, interrupt ID 68 --- */
XTtcPs_Start(&S_sTtc);
```

`tickIsr()` is three lines: read the status with
`XTtcPs_GetInterruptStatus`, acknowledge it with
`XTtcPs_ClearInterruptStatus`, and set the `volatile` flag. Writing to
UART and toggling the LED are entirely the main loop's job — the ISR
stays short.

## How to build

In the Vitis Unified IDE:

1. Select the ready-made **platform** (.xsa, standalone) provided by the
   team.
2. Open a new **empty application** project and link it to this platform.
3. Copy the three files under `src/` in this folder (`uart_ps.h`,
   `uart_ps.c`, `main.c`) into the project's `src/` folder.
4. **Build** the project, then load it onto the board via JTAG and run it.

## Expected output

```
--- TASK 5: Heartbeat via Timer ---
TTC0 channel 0, 1 Hz. DS50 beats like a heart.

tick 1
tick 2
tick 3
```

A new line appears in the terminal exactly once per second; DS50 toggles
on every tick, completing one full blink cycle every 2 seconds — a
steady, uninterrupted heartbeat rhythm.
