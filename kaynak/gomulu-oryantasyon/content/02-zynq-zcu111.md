# Chapter 2 — Meet Zynq and the ZCU111

In Chapter 1 we discussed your role; now let us get acquainted with the
stage. The green board on your desk is called the **ZCU111**, and the
large chip at its core is the **Zynq UltraScale+ RFSoC** (XCZU28DR). By the
end of this chapter you will be able to distinguish the two worlds inside
that chip and describe the purpose of every major component on the board.
At the end of the chapter, your first task awaits: your first physical
contact with the board.

## SoC: an entire system on one chip

In an earlier generation of systems, the processor, memory controller,
peripherals, and specialized circuitry existed as separate chips on a
motherboard. The SoC (system on chip) approach consolidates all of this
into a single silicon package: less board space, lower power, and far
faster internal interconnects. The Zynq family takes this idea a step
further by placing not only a processing system but also a substantial
FPGA within the same package. Two distinct worlds coexist inside the chip:

{{svg:sema-03-zynq-kusbakisi.svg|Figure 3 — Zynq UltraScale+ overview: the fixed Processing System (PS) on the left, the Programmable Logic (PL) on the right, connected by AXI bridges.}}

## PS — Processing System: fixed, ready, familiar

The **PS (Processing System)** is the half of the chip fixed in silicon;
it is present and functional regardless of what you do. It comprises three
main groups:

- **APU (Application Processing Unit):** four **Arm Cortex-A53** cores.
  These are application-class processors capable of running Linux; in this
  journey we will run bare-metal (no operating system) code on them.
- **RPU (Real-time Processing Unit):** two **Arm Cortex-R5F** cores.
  Cores designed for real-time behavior and predictable timing — the
  silicon counterpart of the statement in Chapter 1 that "a correct answer
  delivered late is the same as a wrong answer."
- **Fixed peripherals:** UART, I2C, SPI, and GPIO (General Purpose
  Input/Output) controllers, a DDR memory controller, and more. These are
  likewise fixed in silicon, each with a driver written and validated by
  Xilinx.

PS peripherals reach the outside world through a limited set of dedicated
pins called **MIO** (multiplexed I/O). This detail will become relevant
shortly.

## PL — Programmable Logic: a blank canvas

The **PL (Programmable Logic)** is the FPGA half of the chip: an **FPGA
fabric** woven from millions of small logic cells (the term "fabric"
refers to a reconfigurable hardware weave built from these cells). At
power-up, this fabric is empty; your hardware colleagues design circuits
in Verilog/VHDL, and the toolchain converts that design into a
**bitstream** (a binary file that configures the fabric) — the fabric
becomes a functioning "circuit" only once that bitstream is loaded. The
**IP** blocks (intellectual property cores — off-the-shelf or custom
circuit blocks) designed by hardware engineers live here: a signal
processing chain, a motor control block, or something as modest as an AXI
GPIO.

## The union: AXI

If PS and PL were entirely separate worlds, the chip would lose its point.
The two are connected by **AXI** (Advanced eXtensible Interface — Arm's
on-chip bus standard) bridges. The key consequence for you is this: from
the PS side, an IP in the PL appears as a set of registers visible through
an address window. In other words, communicating with a hardware
engineer's IP amounts to the register read/write operations you will learn
in Chapter 4; we cover the details of the bridge itself in Chapter 9.

## The same task, two worlds: PS peripherals and PL IP

A fact that is initially confusing but ultimately clarifying: the same
function can often be implemented on either side. The PS already includes
a UART; a hardware engineer could just as easily place a UART IP in the
PL. What distinguishes the two?

| | PS peripheral | PL IP |
|---|---|---|
| Presence | Fixed in silicon, always present | Does not exist until the bitstream is loaded |
| Flexibility | Fixed in number and feature set | As many, and as customized, as needed |
| Driver | Ready-made and validated (Xilinx) | Most often written by you, based on the hardware engineer's table |
| Pin access | Limited to MIO pins | Any suitable FPGA pin on the board |

:::analoji A furnished kitchen versus an empty lot
PS is like moving into a house with a kitchen already installed: the stove
is where it is, perhaps not exactly where you would have placed it, but
you can cook today. PL is an empty lot: you build the kitchen you want,
but you cannot even boil water for tea until the architect (the hardware
engineer) has drawn the plans and construction (the bitstream) is
complete.
:::

## Board tour: what is on the ZCU111?

Moving from the chip to the board. The diagram below is not a photograph
but a map — component placement is representative, but identities are
accurate.

{{svg:sema-04-kart-anatomisi.svg|Figure 4 — ZCU111 board anatomy (representative diagram): the DS50/SW19 pair, marked in yellow, is accessible from the PS without a bitstream; the LEDs, buttons, and DIP switch cluster sit on PL pins.}}

- **U1 — RFSoC:** The large package at the center of the board — the
  XCZU28DR you were introduced to above. Both PS and PL reside within this
  single package.
- **DDR4 SODIMM (J50):** The PS's main memory — a 4 GB module in a socketed
  form factor similar to a laptop memory module. You will locate it on the
  memory map in Chapter 3.
- **8 user LEDs (DS11–DS18):** A row of green LEDs. Note: these are
  connected to **PL pins** — we return to this point shortly.
- **DIP switch (SW14) and a 5-button cluster (SW9–SW13):** An 8-position
  switch and five buttons arranged like directional keys. These are also
  on the PL side; we will identify them on the board tour and set them
  aside until Chapter 9.
- **DS50 LED and SW19 button:** The unassuming but, for our purposes, most
  valuable pair on the board. They are connected to PS MIO pins (LED on
  MIO23, button on MIO22) — making them the only LED and button accessible
  from pure PS code, without a bitstream. They will be the primary actors
  in your early tasks.
- **J83 micro-USB:** A single cable doing a great deal of work. The board's
  FT4232 bridge chip exposes four separate ports to your computer over
  this one USB connection: Port A is **JTAG** (the programming/debug
  interface — no external probe required), Port B is **PS UART0** (your
  terminal output flows through here), and the remaining two serve the PL
  UART and the system controller.
- **SD card slot (J100) and boot switch (SW6):** On power-up, the board
  determines its boot source from the position of SW6: JTAG, QSPI flash,
  or SD card. The full boot story is covered in Chapter 3.
- **PMOD connectors (J48/J49):** Expansion sockets familiar from the hobby
  electronics world; small sensor or prototyping boards attach here.
- **Power input:** The board has its own power adapter and power switch;
  it is not powered over USB.

## An honest admission: why the LEDs will not light up right away

We have emphasized this twice already, so let us state it plainly: the
board's 8 LEDs, 5 buttons, and DIP switch are all on PL pins. Since the PL
is an empty fabric at power-up, there is no path from the PS to those LEDs
until a bitstream is loaded. The only user-facing interface reachable from
PS code without a bitstream is the DS50 LED and the SW19 button.

For this reason, your early tasks (Tasks 1–5) will work exclusively with
a single LED and a single button. This may seem unremarkable, but the
constraint itself is the lesson: you will learn the PS/PL separation not
from a slide but from the question "why won't my LED light up?" Be
patient — in Chapter 9 we open the gate to the PL using a bitstream
prepared by the hardware team, and the eight-LED chase pattern awaits you
there (Task 7).

:::tuzak Not every Zynq example on the internet will work on your board
Most "blinking an LED on Zynq" examples found online were written for a
different board, with LEDs wired to different pins (MIO or otherwise).
The code compiles without error, nothing lights up, and hours are lost.
Developing the habit of verifying every board-specific connection against
your own board's user guide (UG1271 for the ZCU111) will save you many
hours of frustration in this profession.
:::

## A window into the RF side

You have likely noticed the RF in the board's name: the RFSoC's defining
capability is a set of radio-frequency data converters embedded directly
in the chip — 8 RF-ADCs (sampling up to 4.096 GSPS) and 8 RF-DACs
(up to 6.554 GSPS). This chip can digitize a signal arriving from an
antenna almost directly; the board's RF signals are routed to SMA
connectors via the XM500 add-on card. This is what sets the ZCU111 apart
from an ordinary development board — but it lies outside the scope of
this journey. We are learning to walk first; when you are ready, consult
the series' *RF Sampling Field Guide*.

The board tour is complete; it is time to get hands-on.

:::gorev no=0 zorluk=1 baslik="First Contact" kisa="First Contact"
[Objective]
Physically set up the board, place it in JTAG boot mode, and establish a
working serial terminal connection between your computer and the board on
the correct port.

[Prerequisites]
The setup checklist from Chapter 0 is complete (in particular, a terminal
program is installed); Chapters 1 and 2 have been read.

[Steps]
1. Remove the board from its packaging: do not open the antistatic bag on
   a metal surface, hold the board by its edges, and avoid touching the
   chip or connector pins. A dry, non-conductive desk surface is
   sufficient.
2. **Set the SW6 boot switch to the JTAG position: all four switches ON.**
   The board ships from the factory set to QSPI32 (ON, ON, OFF, ON) — so
   you will most likely need to flip one switch. See Figure 4 for the
   location of SW6 on the board.
3. Connect the power adapter to the board, but do not switch on power yet.
4. Connect the J83 micro-USB connector to your computer.
5. On your computer (Windows 10), locate the serial ports. The FT4232
   bridge exposes multiple COM ports over the single cable; terminal
   output comes from **PS UART0 = Port B** — typically the second of the
   four, though COM numbering varies by machine, so verify it directly (if
   unsure, see Hint 2). The easiest way to view the ports is **Device
   Manager → Ports (COM & LPT)**; alternatively, list them with a single
   PowerShell command:

   ```komut
   Get-CimInstance Win32_SerialPort | Select-Object Name, DeviceID
   ```

6. Connect the terminal program to that port with **115200 baud, 8 data
   bits, no parity, 1 stop bit (115200-8N1)**.
7. Switch on the board's power.

[Success Criteria]
You have identified the correct COM port, and the terminal connection is
open without error; the board's power LEDs illuminate when power is
applied (verify which LEDs indicate power status in the board user guide —
UG1271). Note: the board does not boot on its own in JTAG mode, so no
output appearing in the terminal is expected behavior; teams that power on
the board with a ready-made image on SD/QSPI will see a boot message here
instead.

[Self-Check]
- If you had left SW6 in the SD position instead of JTAG, what would the
  board attempt to do at power-up? (Hint: the full answer is in Chapter 3.)
- A single micro-USB cable carries both JTAG and UART — how is this
  possible, and which chip on the board provides it?
- In the 115200-8N1 setting, what do "8", "N", and "1" stand for? (You
  will see their wire-level counterparts in Chapter 8; for now, treat this
  as a terminal setting.)

[If You Get Stuck]
::ipucu Hint 1 — No serial port appears at all (driver issue)
Rule out the simple suspects first: is the cable actually a data cable
(some micro-USB cables carry power only), have you tried a different USB
port, and is the board's power switch on (the bridge chip may draw its
power from the board — if it is off, switch it on, then unplug and
reconnect the cable)? If these check out, the issue is most likely the
FTDI driver: if Device Manager shows a device with a yellow exclamation
mark or labeled "Unknown device," download and install FTDI's **VCP
(Virtual COM Port)** driver from FTDI's official site, then unplug and
reconnect the cable — new entries should appear under "Ports (COM & LPT)."
::/
::ipucu Hint 2 — Four ports appear; which one is correct?
You are looking for the FT4232's **second interface** (Port B). Under
"Ports (COM & LPT)" in Device Manager, you will see multiple "USB Serial
Port (COMx)" entries belonging to the same USB bridge; right-click a COM
port and check **Properties → Details → "Location information"** (or "Bus
reported device description") to see which interface (A/B/C/D) it
corresponds to — you are looking for Port B. Shortcut: sort the COM
numbers in ascending order; the second one is usually Port B. If you are
still unsure, note all of them down: in Task 1, when you receive the first
output from the board, you will determine with certainty which port is
active, and you will not need to guess again.
::/
:::

The board is set up on your desk, the terminal is connected, and the boot
switch is waiting in JTAG mode. So what happens inside the chip the moment
you switch on power? That is the exact subject of the next chapter.
