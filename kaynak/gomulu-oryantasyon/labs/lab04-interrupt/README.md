# lab04-interrupt — TASK 4: Button Interrupt

## What it does

Converts the SW19 button (PS MIO22), which Task 3 read via polling, into
a **GIC-400** interrupt. The main loop no longer polls the button at all;
it toggles DS50 (PS MIO23) every 150 ms to simulate a CPU "busy with its
own real work." Every time SW19 is pressed, the hardware itself generates
an interrupt, `buttonIsr()` runs, and the main loop prints the press count
to UART on its next iteration — the heartbeat never stops.

`src/uart_ps.h` and `src/uart_ps.c` are **exact copies from lab02-uart**
(each lab builds independently per `_gorev-zinciri.md`). There is NO
separate `button_ps` module for this lab — since GIC/ISR setup requires
direct access to the `XGpioPs`/`XScuGic` objects, everything is kept in
one place, inside `main.c`.

## Setup order (Chapter 7's five-step GIC pattern)

```c
XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
XScuGic_CfgInitialize(&S_sGic, ...);
Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
    (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
Xil_ExceptionEnable();
XScuGic_Connect(&S_sGic, 48, (Xil_ExceptionHandler)buttonIsr, &S_sGpio);
XScuGic_Enable(&S_sGic, 48);
```

The SW19 pin is configured to trigger on a **rising edge**
(`XGPIOPS_IRQ_TYPE_EDGE_RISING`); the pin-level interrupt
(`XGpioPs_IntrEnablePin`) is enabled last, only after the GIC is fully set
up — order matters here, otherwise there is a risk of generating an
interrupt that nobody is listening for yet.

## Why is the ISR so short?

`buttonIsr()` is three lines: verify that the pin actually fired
(`XGpioPs_IntrGetStatusPin`), set the `volatile` flag, and acknowledge the
hardware (`XGpioPs_IntrClearPin`). There is NO writing to UART, no
computation, no delay — this is the code-level embodiment of Chapter 7's
"no printf in the ISR" rule. It is always the main loop that processes the
flag, increments the counter, and writes to UART.

Pay attention to the order in which the flag is cleared in the main loop:
the code **clears first, then processes**. Had we done the opposite
(process first, then clear), and the ISR fired again during processing,
we would unconditionally clear that new press's flag once done and lose
it.

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
--- TASK 4: Button Interrupt ---
Main loop 'busy' with DS50: press SW19, you'll see an instant reaction.

button pressed, count = 1
button pressed, count = 2
```

DS50 blinks continuously every 150 ms throughout the main loop
(heartbeat); every time you press SW19, a new "button pressed" line
appears within at most one heartbeat cycle (i.e. with no perceptible
delay). The counter increments without skipping or missing a press —
unlike Task 3's debounced polling counter, here the hardware's own edge
detection counts each press exactly once.
