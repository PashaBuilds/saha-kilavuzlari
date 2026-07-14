# Chapter 7 — Interrupts: Notification When an Event Occurs

In Task 3, you read SW19 via polling: the main loop repeatedly called
`buttonRead()`, effectively asking "is it pressed, is it pressed, is it
pressed" without pause. This worked, but it carried a cost — one you may
not have noticed, since the main loop had no other work to perform. This
section makes that cost explicit and introduces the mechanism for
eliminating it: the **interrupt**.

## The Hidden Cost of Polling

Imagine the loop from Task 3, but this time with genuine work in the main
loop as well: collecting data from a sensor, printing telemetry to the
UART, performing a calculation. If you also want to monitor the button via
polling, you face two unfavorable options:

- You interleave frequent calls to `buttonRead()` throughout the loop — a
  portion of CPU time is spent asking "has it happened yet?" even when the
  event never occurs. This resembles stepping out to the door every ten
  seconds to check for a guest who is not coming: tiring, and largely
  wasted effort.
- If you place your primary work inside a lengthy block (a large
  calculation or a long delay, for example), you do not query the button
  at all until that block completes — a **delay** is introduced between
  the moment of the press and the moment it is noticed.

As the system grows and the number of "events" to monitor increases
(button presses, timer ticks, incoming UART data, I2C transaction
completions, and so on), the share of time spent polling grows
correspondingly; an increasing proportion of CPU time is consumed by
"asking." {{svg:sema-14-polling-interrupt.svg|Figure 14 — Polling versus interrupt comparison: the speed of detecting the same event under two CPU operating modes.}}

The distinction in the figure is clear: in the polling lane, the CPU
notices the event only at its next query — the intervening time is lost.
In the interrupt lane, the CPU continues its primary work; the moment the
event occurs, the hardware itself interrupts the CPU, diverts it briefly,
and the CPU then resumes where it left off.

:::analoji A Doorbell Instead of Waiting at the Door
Polling is stepping out to the door every few minutes to check whether a
package has arrived. An interrupt is a door equipped with a bell: you
attend to your own work until the package arrives, and you go to the door
only when the bell rings (the hardware interrupts you). The bell itself is
a piece of hardware — in our environment, that hardware is called the
**GIC**.
:::

## The GIC: Traffic Control for Interrupts

The interrupt controller for the ZCU111's APU (the Cortex-A53 cores) is a
**GIC-400** (Generic Interrupt Controller). Interrupt requests from dozens
of peripherals cannot go directly to the CPU; each must first pass through
the GIC. The GIC performs three functions:

1. **Source routing:** which peripheral's interrupt has occurred, and to
   which CPU core should it be delivered?
2. **Priority:** if multiple interrupts occur simultaneously, which is
   serviced first?
3. **Enable/disable:** each interrupt source can be individually enabled
   or disabled — an interrupt you are not listening for will not disturb
   you.

The GIC-400 has two register blocks: the **GICD (distributor)**, at
address `0xF901_0000`, manages the priority and destination of interrupt
sources; the **GICC (CPU interface)**, at address `0xF902_0000`,
determines whether the running core accepts a given interrupt. The Xilinx
driver (`XScuGic`) hides both blocks behind a single object — you will not
need to manipulate the registers directly, but you should retain the
understanding that the GIC is a piece of hardware with its own register
map.

Each peripheral's identity within the GIC is an **interrupt number**. In
this journey, you will work with three of them:

| Peripheral | GIC Interrupt ID |
|---|---|
| PS GPIO (including SW19) | **48** |
| UART0 | 53 |
| TTC0 channel 0 | **68** |

## The ISR: Short, Sharp, Silent

When an interrupt occurs, the CPU jumps to a function you have written:
the **ISR** (Interrupt Service Routine). Three strict rules apply here:

- **Keep it short.** While an ISR is running, other interrupts either wait
  (depending on priority) or are missed. The ISR's job is to signal that
  "something happened," not to perform the work itself. A well-formed ISR
  typically does the following: set a flag, **acknowledge** the hardware's
  interrupt source (clear it — otherwise the GIC re-triggers the same
  interrupt before it has finished), and exit.
- **Mark shared data `volatile`.** Every variable written by the ISR and
  read by the main loop must be `volatile` — this is exactly where the
  lesson from Chapter 5 proves essential. Without `volatile`, the compiler
  may cache the main loop's read and never update it again; the flag will
  appear never to change.
- **No `printf`/`xil_printf` within the ISR.** Writing to the UART (recall
  Chapter 4) involves waiting for the possibility that the TX FIFO is full
  — meaning that a UART write inside the ISR can stall it until the FIFO
  drains. Introducing a wait of indeterminate duration into a function
  that must remain short is a direct violation of the "keep it short"
  rule. Leave any text to be printed to the main loop.

:::tuzak The Classic "I Forgot to Acknowledge" Case
If you set the flag in the ISR but forget to clear the hardware's
interrupt status (acknowledge it), the GIC reports "interrupt still
active" the moment the ISR exits and immediately re-enters it — an
endless interrupt storm. The system appears to have frozen, but in
reality it is entering the same ISR thousands of times per second.
Omitting the acknowledgment is, in this profession, a classic root cause
behind the question "why isn't anything progressing."
:::

{{svg:sema-15-interrupt-yasam.svg|Figure 15 — Interrupt life cycle: six steps from the event to the main loop processing the flag; the requirement to keep the ISR short is highlighted, along with an incorrect example.}}

## Interrupt Latency: How "Immediate" Is Immediate?

An interrupt responds far more quickly than polling, but it is not **zero
latency**. The hardware signaling the interrupt to the GIC, the GIC
prioritizing it, the CPU suspending its current work and saving its
context, and the jump to the ISR — all of this takes several
microseconds. This is called **interrupt latency**. In this journey, that
duration is small enough to be imperceptible (not remotely comparable to
the detection delay of polling, which can run into seconds), but in
real-time systems, even these microseconds can drive a design decision —
one of the reasons the RPU (Cortex-R5F) exists is to make this latency
more predictable (recall Chapter 2).

## Edge or Level?

An interrupt source can trigger the CPU in one of two ways. **Edge
triggering** captures the instant the signal changes (for example, a
transition from 0 to 1) — it fires once and does not fire again even if
the signal remains high. **Level triggering** fires continuously while the
signal remains at a given level — the GIC persistently issues the
interrupt until you remove that level (clear the flag). Edge triggering is
natural for "it happened once" events such as a button press; level
triggering may be more appropriate for "something is still pending"
conditions, such as data present in the RX FIFO. The
`XGpioPs_SetIntrTypePin()` function supports both; in Task 4, you will use
rising edge for SW19.

## The Pattern for Bringing Up the GIC

A fixed setup sequence recurs in every interrupt-based lab (Task 4, Task
5, and later in Tasks 8-9):

```c
XScuGic_Config* spGicConfig;
spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
XScuGic_CfgInitialize(&G_sGic, spGicConfig, spGicConfig->CpuBaseAddress);

Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
    (Xil_ExceptionHandler)XScuGic_InterruptHandler, &G_sGic);
Xil_ExceptionEnable();

XScuGic_Connect(&G_sGic, KESME_ID, (Xil_ExceptionHandler)benimIsr, (void*)&sCallBackRef);
XScuGic_Enable(&G_sGic, KESME_ID);
```

Five steps, always in the same order: **look up (LookupConfig) →
initialize (CfgInitialize) → bind the CPU's IRQ exception to the GIC's
general handler (Xil_ExceptionRegisterHandler) → bind your ISR to a
specific interrupt ID (Connect) → enable that interrupt (Enable)**. You do
not need to memorize this pattern — you need to be able to recognize it.
The final two lines repeat for every new interrupt source; the first
three are performed once.

You have now seen the interrupt mechanism. It is time to apply it to the
button from Task 3 — and then to become familiar with a self-triggering
interrupt source that fires at regular intervals: the timer.

:::gorev no=4 zorluk=2 baslik="Button Interrupt" kisa="Button Interrupt"
[Objective]
Convert the SW19 button read via polling in Task 3 into a GPIO interrupt
connected through the GIC: the button press should be detected without
delay while the main loop is occupied with its own work.

[Prerequisites]
Chapter 7 has been read; you have the `uart_ps` module from Task 2 (or
this task's own copy) available; you are familiar with pin read/write via
XGpioPs from Task 1.

[Steps]
1. Open a new bare-metal application project in Vitis (using the same
   .xsa platform as Tasks 1-3). Copy the sources under `lab04-interrupt/src/`
   into the project.
2. Initialize the PS GPIO object (`XGpioPs_CfgInitialize`), setting SW19
   (**MIO22**) as input and DS50 (**MIO23**) as output — identical to the
   setup you performed in Tasks 1 and 3.
3. Set the interrupt type for the SW19 pin to **rising edge**:
   `XGpioPs_SetIntrTypePin(&G_sGpio, 22, XGPIOPS_IRQ_TYPE_EDGE_RISING)`.
4. Set up the GIC using the five-step pattern from this chapter; bind
   `benimIsr` to **interrupt ID 48, the GPIO's interrupt ID**
   (`XScuGic_Connect` + `XScuGic_Enable`), then enable the pin interrupt:
   `XGpioPs_IntrEnablePin(&G_sGpio, 22)`.
5. Write the ISR — and keep it SHORT: confirm with
   `XGpioPs_IntrGetStatusPin` that this pin caused the interrupt, set
   `G_ucButtonFlag = 1`, and acknowledge with `XGpioPs_IntrClearPin`. Do
   nothing else — in particular, do not write to the UART.
6. Simulate "busy" work in the main loop: run a simple counting loop
   (heartbeat) that turns DS50 on and off at regular intervals. On each
   iteration, check `G_ucButtonFlag`; if it is set, increment the press
   counter, write `"button pressed, count = N"` to the UART, and clear the
   flag.

[Success Criteria]
While the main loop is "busy" with the DS50 heartbeat, a new line appears
in the terminal without delay each time the button is pressed; the
counter increments accurately, without skipping or missing presses.

[Self-Check]
- Why do we not call `xil_printf` from the ISR? What within a UART write
  could extend the ISR's execution time?
- If the ISR fires again at the exact moment the main loop clears the
  flag, is there a race condition risk? What, precisely, does `volatile`
  protect against here, and what does it NOT protect against?
- If you had configured SW19 for level triggering instead of rising edge,
  what would change — how many times would the ISR be called while the
  button is held down?

[If You Get Stuck]
::ipucu Hint 1 — No Interrupt Occurs
Check the sequence: direction setting (input), `SetIntrTypePin`,
`XScuGic_Connect`, `XScuGic_Enable`, `XGpioPs_IntrEnablePin` — are all
five present? If any one is missing, either the hardware never generates
the interrupt or the GIC never delivers it to the CPU. Forgetting the
`Xil_ExceptionEnable()` call produces the same silent failure.
::/
::ipucu Hint 2 — Interrupt Fires Once, Then Never Again
The acknowledgment (`XGpioPs_IntrClearPin`) is most likely missing or
being performed on the wrong pin. The GIC also has its own "end of
interrupt" step, but `XScuGic_InterruptHandler` handles that for you —
you are responsible only for clearing the GPIO's own status bit.
::/
::cozum Full Solution — lab04-interrupt
The `main.c` below binds the GPIO interrupt to the GIC, sets only a flag
within the ISR, and manages the heartbeat and press counter in the main
loop.
{{kod:lab04-interrupt/src/main.c}}
::/
:::

:::gorev no=5 zorluk=2 baslik="Heartbeat with a Timer" kisa="Timer Heartbeat"
[Objective]
Configure TTC0 channel 0 to generate a 1 Hz periodic interrupt; print a
line to the UART on every tick and drive DS50 in a heartbeat pattern —
entirely interrupt-driven, with no waiting in the main loop.

[Prerequisites]
Task 4 is complete (you have the GIC setup pattern in hand); the
TTC/interval section of Chapter 7 has been read.

[Steps]
1. Copy the sources under `lab05-timer/src/` into a new bare-metal
   project.
2. Initialize the `XTtcPs` object on TTC0 channel 0 (`XTtcPs_LookupConfig`
   + `XTtcPs_CfgInitialize`, base address **0xFF11_0000**); place the
   counter into "interval mode" (`XTtcPs_SetOptions`).
3. **Calculate the interval value for 1 Hz:**
   `Interval = (XPAR_XTTCPS_0_CLOCK_HZ / 1) - 1`. This macro carries your
   platform's actual TTC input clock — read it from `xparameters.h`; do
   not assume a hand-picked MHz figure here. Write it using
   `XTtcPs_SetInterval`.
4. Enable the interrupt:
   `XTtcPs_EnableInterrupts(&G_sTtc, XTTCPS_IXR_INTERVAL_MASK)`. Set up
   the GIC using the five-step pattern from Task 4; this time, **the
   interrupt ID is 68** (TTC0 channel 0).
5. Start the counter with `XTtcPs_Start`. In the ISR, only set
   `G_ucTickFlag = 1` and acknowledge the status via
   `XTtcPs_InterruptHandler` (or by reading the ISR bit directly).
6. In the `main()` loop, when you see the flag: increment the tick
   counter, print `"tick N"` to the UART, and toggle DS50 — this is what
   creates the heartbeat effect.

[Success Criteria]
The terminal outputs exactly one "tick N" line per second; DS50 blinks
with a visible, regular heartbeat rhythm.

[Self-Check]
- Find the value of `XPAR_XTTCPS_0_CLOCK_HZ` on your own platform and
  redo the interval calculation (division plus subtraction) by hand on
  paper — does it match what the code computes?
- If you accidentally doubled the interval value (for example, by
  forgetting the `-1`), in which direction would the tick rate change,
  and by how much?
- We did not use the prescaler at all — why did the 32-bit interval
  register make this unnecessary? Would the same hold at a much lower
  tick frequency (for example, 0.001 Hz)?

[If You Get Stuck]
::ipucu Hint 1 — No Ticks Occur, or a Single Tick Then Nothing
Forgetting the `XTtcPs_Start` call, or omitting the "interval mode"
option (`XTTCPS_OPTION_INTERVAL_MODE`), is a common mistake — if the mode
is not set, the counter may continue counting freely past the interval
without generating an interrupt.
::/
::ipucu Hint 2 — Incorrect Rate (Tick Too Fast or Too Slow)
Look up the actual value of the `XPAR_XTTCPS_0_CLOCK_HZ` macro in
`xparameters.h` and verify the calculation by hand; forgetting the `-1`
in the interval calculation does not shift the tick period by a visually
noticeable amount, but a plain arithmetic error (wrong macro, wrong unit)
typically causes a large deviation.
::/
::cozum Full Solution — lab05-timer
{{kod:lab05-timer/src/main.c}}
::/
:::
