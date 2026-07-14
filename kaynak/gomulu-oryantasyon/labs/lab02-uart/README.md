# lab02-uart — TASK 2: UART "Hello World" and What's Behind printf

## What it does

A two-stage demonstration over PS UART0:

1. A single line via `xil_printf` — shows that the ready-made, lightweight
   printf works out of the box (see the note about lack of `%f` support in
   the comment inside `main.c`).
2. A multi-line welcome banner printed by your own `uart_ps` module (at
   register level, without using the `XUartPs` driver).

The `uart_ps` module consists of three functions (`uart_ps.h`):

```c
void uartInit(void);
void uartSendChar(char cChar);
void uartSendString(const char* cpString);
```

`uartSendChar` waits until the TXFULL bit (`0x10`) in UART0's Channel
Status Register (`SR`, offset `0x2C`) clears, then writes the character to
the FIFO register (offset `0x30`). `uartSendString` sends `'\r'` before
`'\n'` whenever it encounters `'\n'` — so the terminal actually returns the
cursor to the left margin.

**Note:** `uartInit()` does not reconfigure UART0's baud rate (115200) or
frame format (8N1). When the board boots, the FSBL and the standalone BSP
already leave UART0 configured this way — the fact that `xil_printf` works
without any additional setup is proof of this. `uartInit()` merely declares
the register base used by this module as "ready"; if you want a genuine
from-scratch init (Control/Mode/Baud Rate Generator registers), this is
where you would add it.

## How to build

In the Vitis Unified IDE:

1. Select the ready-made **platform** (.xsa, standalone) provided by the
   team.
2. Open a new **empty application** project and link it to this platform.
3. Copy `src/uart_ps.h`, `src/uart_ps.c`, and `src/main.c` from this folder
   into the project's `src/` folder.
4. **Build** the project, then load it onto the board via JTAG and run it
   (Run As → Launch on Hardware) — the same flow you set up in Task 0/1.

## Expected output

With the terminal connected at 115200-8N1 (Task 0), running the board
produces output similar to:

```
xil_printf ready: UART0 already configured by the platform.

========================================
  Welcome to the team - ZCU111 / PS UART0
  These lines were printed by your uart_ps module.
  The TXFULL bit was checked, and data was written to the FIFO.
========================================

```

The first line comes from `xil_printf`; the rest of the banner comes from
the `uart_ps` module.
