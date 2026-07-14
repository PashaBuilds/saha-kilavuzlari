# Chapter 14 — Capstone Project

Across eleven tasks, you came to know the board piece by piece: you read
registers, printed text to UART with your own code, configured a button
interrupt, communicated with a real I2C chip, drove an IP block in the PL,
and moved data between tasks in FreeRTOS using queues and semaphores. Each
task isolated a single skill — deliberately, because attempting to learn
everything at once means learning nothing well. The sole purpose of the
Capstone Project is to remove that isolation: you will now use all of it
at once, within a single project, with each piece depending on the others.
This is a full rehearsal of the first real assignment a newly hired
engineer receives on a team — no one will hand you a step-by-step
procedure; you will be given a set of requirements and a set of acceptance
criteria, and the rest is your design.

## Why This Project Exists

The table below shows where each skill from previous chapters resurfaces
in this project. If you get stuck somewhere, check this table first — it
tells you which chapter to revisit.

| Skill | Learned in | Used in This Project |
|---|---|---|
| Reading register maps, `volatile` pointers, xparameters.h | Chapters 4-5 | INA226 register access, all hardware drivers |
| Bit operations (set/clear/toggle/test) | Chapter 5 | LED status encoding, register field reads |
| Memory/stack discipline | Chapter 6 | Task stack sizing (R10) |
| Polling-based input reading | Chapter 6 | CLI's RX polling task (R7) |
| GIC configuration, ISR writing rules | Chapter 7 | SW19 button interrupt (R5) |
| TTC periodic interrupt | Chapter 7 | Periodic measurement/telemetry timing (R2, R8) |
| I2C protocol, datasheet reading | Chapter 8 | Reading measurements from the INA226 (R2, R3) |
| Communicating with an IP in the PL (AXI GPIO) | Chapter 9 | Advanced LED display (R4, optional layer) |
| FreeRTOS tasks/queues/semaphores | Chapter 10 | Backbone of the entire architecture (R1, R9) |
| Vitis/debugging skills | Chapter 11 | Throughout development and verification |
| Defensive programming, README/commit culture | Chapter 12 | Delivery standard (DELIVERABLE) |

## Requirements

Project name: **Board Health Monitor**. Write a FreeRTOS application that
monitors the board's power health, reports it over UART, and visualizes it
with LEDs. The following ten requirements are written to be measurable;
each must be individually demonstrable at the demo.

**R1.** The system must run on the Xilinx FreeRTOS BSP
(`freertos10_xilinx`) and include at least three separate tasks: a
measurement-collection task, an LED display task, and a UART/CLI task
(telemetry printing and command parsing may live in the same task or in
separate tasks — see Free Design Space).

**R2.** A task must periodically read at least two INA226 power monitors
over PS I2C0, after routing the PCA9544A mux (U23, address 0x75) to
channel 0: **VCCINT (0x40)** and **VCC1V8 (0x42)** — you may optionally
add another rail from `_arastirma.md` §4.

**R3.** The value read from the INA226 Bus Voltage register (offset 0x02,
LSB 1.25 mV) must be converted to a bus voltage in mV.

**R4.** The LED display task must operate at a minimum of two levels:
- **Basic level** (mandatory for everyone): status encoding using DS50
  (MIO23) alone — for example, steady on = healthy, slow blink = warning,
  fast blink = error.
- **Advanced level** (if you have the Task 7 bitstream): using the 8 PL
  LEDs (via AXI GPIO) as a bar graph to show a measurement level or
  additional status information.

**R5.** The SW19 button (MIO22, GIC IRQ 48) must operate on an
interrupt-driven basis; each press must change the display/telemetry mode
(for example, "VCCINT view" ↔ "VCC1V8 view" ↔ "overall summary"), with
software debounce.

**R6.** A telemetry line must be printed periodically over UART0 (at
minimum, tick/time information plus the current mode plus the relevant
measurement values).

**R7.** A line-buffered mini command line (CLI) must run over UART and
support at least the following commands: `status` (prints the current
measurement and mode summary), `led on` / `led off` (stops/starts the
display task), `rate <ms>` (changes the measurement/telemetry period). An
unrecognized command must print a meaningful error message.

**R8.** The `rate <ms>` command must take effect at runtime and must be
bounded to a reasonable range (for example, 100–5000 ms); a value outside
the range must be rejected with feedback to the user.

**R9.** Data sharing between tasks must use FreeRTOS synchronization
objects (queue, semaphore, mutex); a design in which multiple tasks access
a shared variable directly, without locking (carrying race-condition risk),
is not acceptable.

**R10.** The system must run continuously for at least 5 minutes without a
crash, a hang, or a stack overflow. `configCHECK_FOR_STACK_OVERFLOW` must
remain enabled, and task stack sizes must be chosen deliberately (applying
the discipline taught in Chapters 6 and 10).

## Acceptance Criteria

Each of the following must be individually demonstrable at the demo, by
observation:

- On power-up, a welcome message appears on UART, followed shortly by the
  first telemetry line.
- The `status` command correctly prints the current measurement values and
  the current mode.
- The `led on` / `led off` commands visibly stop and restart the LED
  display.
- After `rate 200`, the frequency of telemetry lines visibly increases;
  after `rate 2000`, it visibly decreases.
- Pressing SW19 changes the mode immediately — the button response is not
  delayed even while the main loop/task is busy with other work (this is
  where interrupts prove their advantage over polling, as promised in
  Chapter 7).
- The VCCINT and VCC1V8 readings from the INA226 fall within an
  engineering-reasonable range (roughly ±10% of the nominal value).
- The system runs for the duration of the demo (at least 10 minutes)
  without crashing or hanging.

## Free Design Space

Every requirement up to this point has told you *what* to do, not *how* to
do it. How many tasks you use, how you name your queues, which FreeRTOS
object carries the mode change, how you write the CLI parser — all of that
is yours to decide. The diagram below shows one possible architecture; **it
is a suggestion, not something you are required to copy**. You can satisfy
these requirements with three tasks or with five; what matters is the
clean synchronization that R9 requires.

{{svg:sema-25-mezuniyet-mimari.svg|Figure 25 — Suggested Capstone Project architecture: FreeRTOS tasks, queues, ISR/semaphore mode transitions, and hardware connections}}

If you do not have the Task 7 bitstream, or did not have time to set up
the PL LED bar, the basic level of R4 (DS50 only) is on its own a
sufficient deliverable — the advanced level is a bonus, not a requirement.
Additional touches such as adding more measurement rails or a third CLI
command (for example, `help`) are also part of the free design space;
exceeding the requirements is always acceptable, falling short of them is
not.

## Deliverable

You will submit two parts:

1. **A short README** (think of it as a file like the ones in the other
   `labs/` labs — except this one you write yourself). It must include:
   - The project's purpose and a brief architecture summary (how many
     tasks, which queues/semaphores).
   - Hardware/software requirements (Vitis version, which .xsa/bitstream
     is needed, if any).
   - How to build and load it onto the board (Vitis project type, steps).
   - The CLI command list and a sample of expected output.
   - Known limitations ("I did not implement X because..." — honesty is
     valued here, as Chapter 12 taught).
2. **A 10-minute live demo in front of the team.** Walk through the
   acceptance criteria in order, and be ready to answer questions live.
   This is a rehearsal of the "it's done" demo you will give in a real job
   setting.

## If You Get Stuck

We are not providing solution code — the entire point of this project is
for you to build your own design. But here are three pointers so you avoid
three common architectural pitfalls:

- **Give UART to a single task.** Both telemetry printing (TX) and CLI
  reading (RX) share the same physical peripheral; if two different tasks
  call `XUartPs_Send` at the same time, the output can interleave and
  corrupt. There is no need to build a separate interrupt path for the RX
  side — a `XUartPs_Recv` **polling** task that returns with a small delay,
  accumulating characters into a line buffer and parsing the command once
  it sees `\r`/`\n`, is sufficient and reasonable at this scale.
- **Separate measurement collection, display, and the CLI with queues.**
  The value the measurement task reads from the INA226 should not reach
  other tasks through a directly shared global variable, but through a
  queue (or, at minimum, a mutex-protected shared structure). Likewise,
  commands parsed by the CLI (`led on`, `rate <ms>`) should reach the
  relevant task as a queue message — this is the natural consequence of
  R9's "no lock-free sharing" rule.
- **Carry the mode change with a semaphore or an event; do not process it
  inside the ISR.** The SW19 ISR must stay short (Chapter 7's rule applies
  here too): the ISR should only give a binary semaphore via the
  `FromISR` API, while the mode-change logic itself (deciding which screen
  to switch to, updating the LED pattern) runs in a task waiting on that
  semaphore.

:::gorev no=mezuniyet zorluk=3 baslik="Board Health Monitor" kisa="Board Health Monitor"
[Objective]
Design and bring to a working state a standalone "Board Health Monitor"
application on FreeRTOS that collects power measurements over I2C, displays
status on LEDs, changes mode via the SW19 interrupt, and provides both
periodic telemetry and a mini CLI over UART.
[Prerequisites]
Task 0 through Task 10 must be complete: I2C reading, interrupt
configuration, FreeRTOS task/queue/semaphore skills, and (if available)
AXI GPIO skills all come together here.
[Requirements]
- At least 3 FreeRTOS tasks: measurement collection, LED display, UART/CLI
  (R1, R9).
- Periodic reads of VCCINT (0x40) and VCC1V8 (0x42) from the INA226,
  converted to mV (R2, R3).
- Two-level LED display: DS50 basic level + PL LED bar advanced level,
  optional (R4).
- Mode change via the SW19 interrupt (R5).
- Periodic UART telemetry plus a `status` / `led on` / `led off` /
  `rate <ms>` mini CLI (R6, R7, R8).
- 5 minutes of continuous, synchronized operation with no lock-free
  sharing (R9, R10).

For the full requirements list (R1–R10) and acceptance criteria, see the
top of this chapter.
[Acceptance Criteria]
- UART welcome message plus first telemetry line on startup.
- The `status`, `led on`, `led off`, and `rate <ms>` commands work as
  expected.
- SW19 changes the mode instantly (even while the system is busy).
- VCCINT/VCC1V8 readings fall within a reasonable range.
- The system runs without crashing throughout the 10-minute demo.
[Deliverable]
A short README (purpose, architecture summary, build/load steps, CLI
command list, known limitations) plus a 10-minute live demo in front of
the team.
[Self-Check]
- Why did you hand off the mode change to a semaphore instead of handling
  it directly inside the ISR? Which task(s) would have been at risk if you
  had handled it directly?
- If you had kept the `rate <ms>` value in a shared global variable instead
  of using a queue, in which scenario would a race condition have arisen?
- What would you have observed if two separate tasks (one for telemetry,
  one for CLI responses) printed to UART directly? How did you prevent
  this?
[If You Get Stuck]
::ipucu Hint 1 — Sketch the architecture before coding it
Before touching the keyboard, draw your tasks, the queues/semaphores
between them, and the hardware each one uses as a box-and-arrow diagram
(try your own version before looking at Figure 25). If you cannot answer
"where does this data go from and to" clearly on paper, you will not be
able to answer it in code either.
::/
::ipucu Hint 2 — Start small, grow layer by layer
Begin with just two tasks: measurement collection and printing to UART
(connected by a queue). Once these two run reliably, add the LED display
task, then the SW19 interrupt, and finally the CLI parser. Verify that the
previous layer still works each time you add a new one — Chapter 12's
advice to "proceed in small steps" is nowhere more valuable than here.
::/
:::

You have seen the board, read the requirements, and studied the diagram.
Now it is your turn at the keyboard.

---

If you have reached this point: congratulations. The board that
intimidated you on your first day at your desk is now yours to command —
you have read its registers, configured its interrupts, spoken its
protocols, and written your own FreeRTOS application. This document ends
here, but your learning does not; next comes your **first real assignment**
on the team, and this time, likely, no one will prepare a task card for
you — you will break it down yourself. Take two resources with you when you
need them: this document's **Appendix A — Quick Reference** (a summary you
can keep at your desk) and the **field guides** introduced in Chapter 13 —
Memory Architecture, Ethernet, RF Sampling — there for the depths this
journey deliberately left for you to explore on your own.

Good luck. Welcome to the team.
