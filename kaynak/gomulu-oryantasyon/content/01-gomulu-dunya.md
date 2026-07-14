# Chapter 1 — The Embedded World and Your Role

In Chapter 0 we stated that "embedded software is learned through
practice." But before hands touch the board, one question needs
clarifying: what exactly will you be doing from this point forward? This
chapter provides the broader context — what an embedded system is, where
it diverges from the software world you are accustomed to, and what
responsibilities fall to you in this domain.

## What is an embedded system?

An embedded system is a computer built into a device to perform a specific
function, and one that most often gives no outward sign of its presence.
It has no keyboard, in most cases no screen, and certainly no "install
app" menu; it performs a single function, every day, for the lifetime of
the device, without exception.

Since waking up this morning, you have likely used dozens of them: the
alarm on the phone that woke you, the temperature control in the kettle at
breakfast, the elevator's floor logic on your way out, the ABS controller
behind your car's brake pedal, the Bluetooth headset in your ear, the POS
terminal that processed your lunch payment, and the cell tower that keeps
your phone connected throughout the day. Each contains a processor, large
or small, running the kind of software we write.

{{svg:sema-01-evren.svg|Figure 1 — The embedded systems landscape: at the center, a sensor to MCU/SoC to actuator chain, surrounded by embedded devices encountered in daily life.}}

The core of the definition is the three-part chain shown in the figure. The
**sensor** measures the external world: temperature, pressure, a button
press, an antenna signal. The **MCU** (microcontroller unit) at the
center, or its larger counterpart the **SoC** (system on chip), reads the
measurement and makes a decision. The **actuator** applies that decision
to the world: turning a motor, opening a valve, lighting an LED, driving
an antenna. The code you write sits at the center of this loop, and the
loop runs for as long as the device remains powered.

:::analoji Pocketknife and scalpel
A desktop computer is a Swiss Army knife: capable of many tasks, dedicated
to none. An embedded system is a scalpel: it performs a single task, but
must be flawless and predictable at that task. If the pocketknife jams,
you fold it and put it back in your pocket; the scalpel does not have the
luxury of announcing, mid-procedure, that it is temporarily unavailable.
:::

## Four major differences from desktop software

The C programs you wrote at university ran in the accommodating embrace of
an operating system: you requested memory and received it, you wrote to
the screen and it appeared, the program crashed and no harm was done. In
the embedded world, this changes across four dimensions.

**1. Resource constraints.** RAM on the desktop is measured in gigabytes;
in the embedded world it is more often measured in kilobytes, and the
processor may run at megahertz rather than gigahertz. To be clear: the
ZCU111 in front of you is at the premium end of this spectrum — it has
four cores and gigabytes of DDR memory. But the embedded mindset is not
about the specific board; it is a habit of accounting for every byte and
every microsecond, a discipline you will build here because your next
project may not afford the same luxury.

**2. Real time.** In embedded systems, a correct answer delivered late is
the same as a wrong answer. An ABS controller must detect wheel lockup and
release brake pressure within milliseconds; "I'll get to it shortly" is
not an option. For this reason, embedded engineers design not only for
*what* is computed but also for *how long* it takes to compute. This
concept becomes concrete in Chapter 7 (interrupts) and Chapter 10
(FreeRTOS).

**3. Proximity to hardware.** On the desktop, a thick cushion of operating
system, drivers, and libraries separates you from the hardware. In the
embedded world, that cushion is thin or absent entirely: you program
hardware directly at the register level (the small control and status
cells inside a peripheral — the main subject of Chapter 4). Even printing
text to the screen with `printf` flows through a UART that you yourself
brought up.

**4. Responsibility.** A desktop program that crashes gets restarted. In an
embedded system, a faulty software update can brick the device (rendering
it permanently inoperable). Moreover, the device may be deployed in the
field: atop a tower, inside a vehicle, in a customer's hand. The statement
"I'll ship the fix tomorrow" is meaningless without physical access to the
device.

:::saha-notu Bricking stories are real
Every embedded team has a bricking story in its history: a wrong boot
image, a flash write interrupted midway, a release shipped untested
because "it was such a small change." We do not share this to alarm you —
the ZCU111 on your desk is a development board, recoverable from nearly
any state via JTAG, and you should not hesitate to experiment with it. A
production board is a different matter, which is why the governing rule in
our domain is: if you changed it, test it.
:::

## Your job description

So what does an "embedded software engineer" actually do in this domain?
Let us summarize it in five verbs; you will experience each of them
firsthand over the coming weeks.

- **Writing drivers.** Communicating with a peripheral at the register
  level and converting that into clean functions for the rest of the team
  to use: being the person who writes `uartSendChar()`. You will write
  your first driver in Task 2.
- **Communicating with hardware engineers through the register map.** The
  register map is the contract between us and the hardware team: which
  address, which bit, what meaning. The hardware engineer designs an IP in
  the FPGA and hands you the register table; you convert that table into
  code. We cover this workflow in Chapter 9.
- **Bring-up.** Giving a new board or a new IP its first breath of life
  when it arrives on the bench: is the clock running, does the processor
  come up, does the first byte appear on UART? Task 0 is your first small
  bring-up exercise.
- **Debugging.** Diagnosing faults — often without a screen, sometimes
  without even `printf`. Debugger, LEDs, UART, and, when needed, an
  oscilloscope; we cover this toolkit in Chapter 11.
- **Integration.** Resolving the familiar scenario where every individual
  part is correct yet the system as a whole is not: bringing the pieces
  together into one system and debugging interface errors.

Let us map this list onto layers. The figure below shows the software
layers of an embedded system: hardware at the bottom, drivers above it,
middleware above that (protocol stacks, RTOS, and other shared services),
and the application at the top.

{{svg:sema-02-katmanlar.svg|Figure 2 — Layers of responsibility: the embedded software engineer works primarily in the driver and middleware layers; the desktop software engineer's work rarely touches the hardware directly.}}

The desktop software engineer works in the topmost layer; the operating
system renders everything beneath it invisible. We, by contrast, work
predominantly in the driver and middleware layers: one hand on the
registers, the other extending a clean interface to the application. We do
work in the application layer as well — but what defines us is the ability
to manage the two layers beneath it with confidence.

:::ekip-notu The life cycle of a task on our team
A typical task proceeds as follows: (1) you receive the task — most often
phrased as "this peripheral needs a driver" or "bring up this IP"; (2) you
read the register map and the device datasheet — before writing code, not
after; (3) you write the driver; (4) bring-up: the code runs on the actual
board for the first time, and it is normal for it not to work on the first
attempt; (5) you test it — your success criterion is defined up front; (6)
you submit it for code review (expectations are discussed in Chapter 12);
(7) integration: your component meets the rest of the system. Notice that
"writing code" is only one of seven steps. This document prepares you for
exactly this cycle.
:::

If these descriptions still feel abstract, that is expected; they will
become concrete through the tasks ahead. Next, we turn to the stage on
which this work takes place: in the following chapter, we introduce the
board on your desk — Zynq and the ZCU111.
