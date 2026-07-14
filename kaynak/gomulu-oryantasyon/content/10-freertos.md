# Chapter 10 — Operating Systems: From Bare-Metal to FreeRTOS

Everything you have written so far has been **bare-metal** — no operating
system, a single `main()`, an infinite loop, with occasional interrupts. In
Tasks 4 and 5, you put this to good use: a button interrupt set a flag, a
timer interrupt incremented a counter, and the main loop checked the flags
and carried out its work. In a small system, this architecture is both
sufficient and easy to follow. This chapter addresses where that
architecture begins to break down, and its solution: **FreeRTOS**. Because
the material is substantial, the chapter is split into two sessions: first,
we build FreeRTOS's core mechanics (task, priority, scheduler, tick), and
you put this into practice on the board; then we move on to the tools for
sharing data and events between tasks (queue, semaphore, mutex) and their
classic pitfalls.

## Part One: The RTOS Kernel

In this first session we pursue a single question: how does FreeRTOS
recognize, run, and schedule a task? We deliberately defer inter-task
communication (queue, semaphore, mutex) to the second session — you should
first have a solid grasp of a single task's life cycle before building
anything on top of it.

## Flag Soup: The Limits of Bare-Metal

As the number of tasks grows, the superloop-plus-ISR architecture falls
into a pattern: a new flag for every new job, a new `if` in the main loop.
Once there are five or six jobs, the loop turns into **flag soup** — a
state in which questions such as "which flag was set when, in what order
should they be checked, does one delay another" can no longer be answered.
Worse, no job carries a timing guarantee. If the job at the start of the
loop takes a long time, the job at the end runs correspondingly late —
nobody tells you this, and it is not visible from the code; it simply
surfaces one day as the question "why does this button sometimes respond
late."

{{svg:sema-21-superdongu-rtos.svg|Figure 21 — Side-by-side comparison of a bare-metal superloop and the FreeRTOS scheduler: running "at the same time" is, on a single core, rapid time-slicing.}}

## Why an RTOS

**RTOS (Real-Time Operating System)** exists to solve one problem: managing
multiple **logical jobs** on a single CPU such that each meets its own
timing expectations. The key word is **blocking**. In the bare-metal
world, "wait" usually meant spinning the CPU in an empty loop (something
like `while (!flag);`) — the CPU does no useful work during that time. In
the RTOS world, "wait" means a state in which the job **voluntarily gives
up the CPU**, and the scheduler hands the CPU to other work for that
duration. The same word, an entirely different behavior.

## The FreeRTOS Kernel: Task, Priority, Tick

FreeRTOS's fundamental unit is the **task** — not to be confused with the
word "job" used above for the bare-metal discussion; here it is FreeRTOS's
official term. Each task is an independently running function with its own
stack, and at any given moment it is in one of four states:

- **Running** — currently executing on the CPU (on a single core, only one
  task can be Running at a time).
- **Ready** — ready to run, waiting its turn.
- **Blocked** — waiting for an event (a timeout, incoming data, a resource
  becoming free); it is not a candidate for the CPU until that event
  occurs.
- **Suspended** — excluded from scheduling; it waits for nothing until
  something explicitly resumes it.

You assign each task a **priority**. FreeRTOS's scheduler is **preemptive**
— the highest-priority task in the Ready state always takes the CPU; if a
higher-priority task becomes Ready while a lower-priority task is running,
the scheduler interrupts the lower-priority task immediately. The **tick**
determines how frequently this preemption decision is made: it is the
regular interrupt produced by a periodic hardware timer.
`configTICK_RATE_HZ` defaults to **100 Hz** in our BSP (`freertos10_xilinx`)
— meaning the scheduler reviews the "who should run now" decision 100
times per second.

You have seen how tasks come into being, how they are prioritized, and how
the scheduler orders them; it is now time to put this into practice. In
Task 8 you will bring up three tasks simultaneously, including one
carrying a signal from SW19 — we will cover the detailed mechanics of how
that signal is transported in the second session; for now, the steps in
the task card are all you need.

:::gorev no=8 zorluk=2 baslik="Your First FreeRTOS Application" kisa="First FreeRTOS"
[Objective]
Run three FreeRTOS tasks (heartbeat, status, button handler) in the same
system without interfering with one another.

[Prerequisites]
Part One of Chapter 10 read; you are familiar with the GIC/GPIO interrupt
logic you set up in Task 4 (button interrupt).

[Steps]
1. Create your platform component in Vitis with OS = `freertos10_xilinx`
   (processor `psu_cortexa53_0`).
2. Write the `heartbeatTask` task: it should toggle the DS50 LED (MIO23)
   every 500 ms using `vTaskDelay` — **no waiting with an empty loop**.
3. Write the `statusTask` task: it should print a status line to the UART
   every 2 seconds.
4. Create a binary semaphore for SW19 (MIO22); give it from within the ISR
   using `xSemaphoreGiveFromISR`, and call `portYIELD_FROM_ISR` at the
   end.
5. Write the `buttonHandlerTask` task: it should wait on the semaphore
   with `xSemaphoreTake` and print a line on every press.
6. Create all three tasks with `xTaskCreate`, and start the scheduler with
   `vTaskStartScheduler()`.

[Success Criteria]
DS50 blinks regularly every 500 ms, a status line appears on the terminal
every 2 seconds, and a button line is interleaved on every SW19 press —
all three jobs run without interfering with one another.

[Self-Check]
- What is the difference, from the CPU's perspective, between waiting
  with `vTaskDelay` and waiting in an empty `while` loop?
- What would you lose if you used a global flag, as in bare-metal, instead
  of a semaphore?
- `statusTask` and `heartbeatTask` share the same priority — does this
  create a problem? Why or why not?

[If You Get Stuck]
::ipucu Hint 1 — The LED does not blink, or the terminal prints nothing
Confirm that the GPIO and GIC setup before `vTaskStartScheduler()`
(direction configuration, interrupt binding) is no different from Task 4
in the bare-metal chapters. Code called before the scheduler starts is
still ordinary bare-metal code.
::/
::ipucu Hint 2 — The button line never appears
Do not forget to call `XGpioPs_IntrClearPin` inside the ISR — an uncleared
interrupt keeps the GIC locked and it will never fire again. Make sure the
`BaseType_t` variable you pass to `portYIELD_FROM_ISR` is initialized to
`pdFALSE` at the start of the ISR.
::/
::cozum Full Solution — lab08-freertos
`labs/lab08-freertos/src/main.c` demonstrates all three tasks, the
GIC/GPIO setup, and the FromISR flow end to end.
{{kod:lab08-freertos/src/main.c}}
::/
:::

So far you have seen how individual tasks come into being, how they are
prioritized, and how the scheduler switches between them — in Task 8 you
also built this yourself, carrying a signal from SW19 to a task through a
semaphore. In real systems, however, tasks do not operate in isolation
like separate islands; they need to share data and events. In the second
session, we turn to the three fundamental tools for this sharing, along
with the classic pitfalls that accompany them.

## Part Two: Inter-Task Communication and Pitfalls

In this session you will see what the semaphore you created for SW19 in
Task 8 actually is, how it forms a family together with the queue and the
mutex, and which pitfalls that family is exposed to. The diagram below
summarizes this entire second session at a glance: the task state machine,
now shown together with the transitions triggered by the queue, semaphore,
mutex, and ISR.

{{svg:sema-22-freertos-nesneleri.svg|Figure 22 — Map of FreeRTOS core objects: the task state machine together with the transitions triggered by the queue, semaphore, mutex, and ISR.}}

## Queue, Semaphore, Mutex: Which One, and When

Tasks run in isolation from one another, but real systems must share data
and events. FreeRTOS provides three fundamental objects for this purpose,
and each answers a different question:

- **Queue** — for *carrying data*. One task places a copy of the data with
  `xQueueSend`; another task retrieves it with `xQueueReceive`, in FIFO
  order, over a fixed-size buffer. This is the answer to "safely carry
  this measurement from there to here."
- **Semaphore** — for *signaling an event*; it carries no data. A binary
  semaphore says "something happened" (an interrupt arrived, a job
  finished); a counting semaphore says "this many resources/events have
  accumulated." This is the answer to "the button was pressed, wake up" —
  the SW19 semaphore in Task 8 is exactly this.
- **Mutex (mutual exclusion)** — for *protecting a shared resource*. It
  appears to use the same API as a binary semaphore, but its meaning is
  different: the task that takes a mutex is expected to give it back
  ("I have locked this resource; I will release it when I am done"),
  whereas a semaphore carries no notion of "ownership." You will shortly
  see why this distinction matters (priority inversion).

## From ISR to Task: The FromISR Family

The rule you learned in Chapter 7 still applies: keep the ISR (interrupt
service routine) short — do not call `xil_printf` inside it, and do not
perform long-running work there. In FreeRTOS, ISRs "notify" by moving a
task from Blocked to Ready, but you **cannot** use the normal
`xQueueSend`/`xSemaphoreGive` calls inside an ISR — these are written with
assumptions that may block the scheduler and are not safe in an interrupt
context. Instead, every object has a **FromISR** counterpart:
`xQueueSendFromISR`, `xSemaphoreGiveFromISR`. These functions report,
through an output parameter, whether the operation woke a task of higher
priority than the one that was interrupted; at the end of the ISR, a call
to `portYIELD_FROM_ISR()` tells the scheduler, if the answer is yes, to
switch to that task as soon as the ISR exits. You already set this up
with the SW19 button in Task 8 — now you are seeing the mechanism behind
what you built by hand.

:::tuzak Stack Overflow: Silent and Dangerous
Each task has its own stack, and that stack is the fixed size you supply
in the `xTaskCreate` call — it does not grow. If your local variables and
function call chain exceed this limit, a **stack overflow** occurs, and
the result is usually not a clear error message but random corruption, a
crash, or an unrelated variable changing unexpectedly. Our BSP's default
is `configCHECK_FOR_STACK_OVERFLOW = 2` — on every context switch (the CPU
saving one task's state and loading another's as it moves between tasks),
FreeRTOS checks whether the stack still preserves a specific pattern, and
calls `vApplicationStackOverflowHook` if it detects an overflow. For a
task you suspect, `uxTaskGetStackHighWaterMark(handle)` returns how close
that task has come to exhausting its stack (the lowest amount of free
space remaining) — the smaller the number, the greater the danger. In
Task 10 (Bug Hunt) you will encounter a live example of this pitfall.
:::

:::derin-dalis Priority Inversion and Priority Inheritance
Consider the following scenario: a low-priority task has taken a mutex and
is using the resource. A high-priority task requests the same mutex and,
naturally, drops into Blocked — it will wait until the low-priority task
finishes and releases the mutex, which is reasonable. But what happens if
a **medium-priority** task now steps in and occupies the CPU? Under the
scheduler's rule, the medium-priority task preempts the low-priority one
(because it has higher priority); the low-priority task cannot release the
mutex, and so the high-priority task continues to wait as well. The
result: the highest-priority task is waiting — not because of a task lower
in priority than itself, but because **a task lower still is holding the
CPU** — the priority order has effectively been inverted. This is called
**priority inversion**, and it can lead to serious timing violations in
real-time systems.

FreeRTOS's mutex (unlike an ordinary semaphore) implements **priority
inheritance**: if a task of higher priority begins waiting on a mutex held
by a lower-priority task, the low-priority task is *temporarily* raised to
the waiting task's priority — so the medium-priority task cannot preempt
it, the mutex is released promptly, and the true waiter proceeds. This is
the real difference underlying the API similarity between semaphore and
mutex: whenever you need to protect a shared resource, always use a
mutex — do not make do with an ordinary semaphore on the assumption that
"it does the same job."
:::

You now have the task/queue/semaphore mechanics in hand; it is time to
combine them in a real producer/consumer pipeline.

:::gorev no=9 zorluk=2 baslik="Producer/Consumer with a Queue" kisa="Queue Flow"
[Objective]
Carry data measured periodically by a producer task to a consumer task
through a queue, producing safe, orderly output.

[Prerequisites]
Part Two of Chapter 10 read; Task 8 completed; you are familiar with
Task 6's `ina226` module (or this lab's own copy of it — see
`labs/lab09-queue/README.md`).

[Steps]
1. Define the `SMeasurementPacket` struct: a timestamp plus a VCCINT mV
   value.
2. Create a queue: `xQueueCreate(length, sizeof(SMeasurementPacket))`.
3. Write the `producerTask` task: take a measurement every 500 ms with
   `ina226ReadBusVoltageMv`, package it, and place it on the queue with
   `xQueueSend`.
4. Write the `consumerTask` task: wait with `xQueueReceive`, then format
   and print the incoming packet with `xil_printf`.
5. Make sure that **only** `consumerTask` writes to the UART — this
   architecturally guarantees that lines do not get interleaved.

[Success Criteria]
Timestamped mV lines flow steadily on the terminal; no data is lost even
if the producer and consumer run at different rates (if the queue is
full, this is reported explicitly rather than being silently dropped).

[Self-Check]
- What does `xQueueSend` do when the queue is full? How would you observe
  this behavior?
- If you took the measurement directly inside `consumerTask` (no queue, a
  single task), what would you lose architecturally?

[If You Get Stuck]
::ipucu Hint 1 — No data flows at all
Make sure you are checking the return value of `ina226Init()`; if the
INA226 identity check (`0x5449`) fails, the producer never sends a
measurement. Check the I2C0/mux setup using the same approach as
Chapter 8 (I2C).
::/
::ipucu Hint 2 — Lines sometimes appear to interleave
Confirm that neither task calls `xil_printf` directly except
`consumerTask`; only it should write. The only thing `producerTask`
should print is a queue-full warning, and that should be rare — occurring
only when the consumer has genuinely fallen behind.
::/
::cozum Full Solution — lab09-queue
`labs/lab09-queue/src/main.c` contains the producer/consumer pair;
`src/ina226.c` contains the INA226 reading module.
{{kod:lab09-queue/src/main.c}}
::/
:::

## Beyond Our World: Commercial RTOSes

FreeRTOS is the most common choice on our team and in the embedded world
generally — it is open source, lightweight, and comes with official
Xilinx support. In domains that require certification, however —
aerospace, medical devices, or automotive, where compliance with standards
such as DO-178C or IEC 62304 is required — commercial, certified RTOSes
such as **VxWorks**, **QNX**, or **Integrity** are preferred; their cost
and support model differ, but their guarantees (documented worst-case
timing, certification artifacts) are indispensable in those domains. They
will not appear in your journey here, but it is enough that you can
recognize them, when you hear the names, as "FreeRTOS's commercial
relatives."

Managing all of these pieces together — tasks, interrupts, queues,
register maps — now requires a better understanding of your tools. The
next stop is Vitis itself.
