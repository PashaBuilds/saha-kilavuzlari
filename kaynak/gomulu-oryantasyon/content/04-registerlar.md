# Chapter 4 — Registers: The Language of Communicating with Hardware

You have seen the memory map: everything has an address. In this chapter,
you will learn what lies behind those addresses — **registers**. A
register is a small box through which hardware communicates with the CPU;
by the end of this chapter, you will be able to read and interpret a
register map document, and you will make a piece of real hardware respond
to your own code.

## Memory-Mapped I/O: An Address Is Really a Door

**Memory-mapped I/O** means that a peripheral's registers can be read from
and written to via a memory address, exactly like a variable in RAM. In
other words, writing `1` to address `0xFF0A0040` and writing
`myCounter = 1;` are, from the CPU's point of view, nearly identical
operations — the difference is that the address is connected not to RAM
but to a GPIO controller, and the instant you write to it, a physical pin
changes level in the real world.

{{svg:sema-07-adres-kapi.svg|Figure 7 — "Address = door number": the path of a read/write operation from the CPU, over the address bus, to a peripheral register.}}

As an analogy, this resembles locating a street address: the CPU places a
"door number" (address) on the address bus, and the "building" (peripheral)
at that number responds. Knock on door number `0xFF00_0000` and UART0
answers; knock on door number `0xFF0A_0000` and GPIO answers. If you write
the wrong door number, either no one answers, or someone entirely
unexpected does.

## Inside a Register: Bit Fields and Access Types

Each register is a 32-bit box, and each bit (or group of bits) carries a
distinct meaning. In the UART's SR (Channel Status) register, bit 4 =
TXFULL (whether the transmit FIFO (First In First Out — the ordered
buffer in which hardware temporarily holds data) is full), bit 1 =
RXEMPTY (whether the receive FIFO is empty), and so on.

{{svg:sema-08-register-bit.svg|Figure 8 — Anatomy of a 32-bit register's bit fields: the TXFULL/TXEMPTY/RXFULL/RXEMPTY bits from the UART SR highlighted; below, the R/W, RO, and W1C badges.}}

In addition to bit fields, every register has its own **access type**. You
will frequently encounter three of them:

- **R/W (Read/Write):** Both readable and writable, just like an ordinary
  variable. CR (0x00) is like this — you write to it to enable TX/RX.
- **RO (Read-Only):** Readable only; hardware updates it, and you cannot
  write to it. SR (0x2C) is like this — you *ask* whether the TX FIFO is
  full, you do not *tell* the hardware.
- **W1C (Write-1-to-Clear):** An unusual pattern that can be confusing at
  first sight. In this register, writing 1 to a bit **clears** it; bits
  you write 0 to remain unchanged. ISR (0x14) works this way: to clear an
  interrupt flag, you write 1 to that bit — writing 0 does nothing. In
  other words, the verb "clear" here means "write a 1 to it"; this is
  counterintuitive, but it is a very common pattern in embedded systems.

In Chapter 5, you will learn to read and write these bits using masks;
for now, it is enough to know them by their correct names.

## Reading a Register Map Document

Hardware designers (or Xilinx) publish a **register map** document for
each peripheral: which register sits at which **offset** (the
displacement from the base address), what its **reset value** is after
power-on, and what its **access type** — which you have just learned — is.
A small excerpt from the actual register map of the ZynqMP UART:

{{svg:sema-09-register-map-okuma.svg|Figure 9 — A lesson in reading a register map document: offset/access/reset annotations on the UART register table.}}

| Register | Offset | Access | Reset | Description |
|---|---|---|---|---|
| CR (Control) | 0x00 | R/W | 0x00000128 | TX/RX enable, reset bits |
| MR (Mode) | 0x04 | R/W | 0x00000000 | Baud source, data/stop bit count |
| SR (Channel Status) | 0x2C | RO | — | TX/RX FIFO status (TXFULL, RXEMPTY...) |
| ISR (Interrupt Status) | 0x14 | **W1C** | 0x00000000 | Interrupt flags |

All four columns are critical: the **offset** is the number to add to the
base address; **access** tells you what you may do with the register;
**reset value** tells you what you will find in the register the instant
the board powers on; **description** tells you the register's purpose.
Writing code without reading these is comparable to setting up a device
without reading its manual — it sometimes works, but it costs you hours
far more often.

## Base Address + Offset Arithmetic

The actual address of a register follows from a single formula:

```metin
actual_address = base_address + offset
```

Example: the GPIO controller's base address is `0xFF0A_0000`. Bank 0's
data register (DATA_0) is at offset `0x40`. The actual address:
`0xFF0A_0000 + 0x40 = 0xFF0A_0040`. You do not need to perform this
addition by hand every time — as you will see shortly, driver functions or
ready-made constants do it for you — but reading a register map is not
possible without understanding the formula itself.

:::tuzak Confusing the Offset with the Base Address
Register map documents often list the offset alone (such as `0x2C`) and
give the base address in a separate table. A line that confuses the two —
writing directly to `0x2C`, or copying UART1's base address into UART0
code — compiles, appears to run, and leaves you programming the wrong
peripheral. Before using any register address, ask yourself: "which base
address plus which offset is this?"
:::

## xparameters.h: We Do Not Write Addresses by Hand

So where do you obtain these base addresses in code? You do not write
them by hand — Vitis automatically generates the **`xparameters.h`**
header file from the hardware definition (.xsa); the address, interrupt
number, and identifier of every peripheral are available here as
ready-made constants. Naming differs slightly between two Vitis flows:

- **Classic flow** (Vitis Classic, 2023.1 and earlier): each device is
  identified by a **DEVICE_ID**, e.g. `XPAR_XUARTPS_0_DEVICE_ID`. You
  pass this identifier to the driver's `LookupConfig` function, which
  returns a configuration structure containing the base address.
- **SDT flow** (System Device Tree — the current method used by the
  Vitis Unified IDE): devices are referred to directly by base address,
  e.g. `XPAR_XUARTPS_0_BASEADDR`. In this case, `LookupConfig` takes the
  address itself as its parameter.

The underlying logic is the same in both: **do not write the address by
hand — take it from the generated header.** An address you write by hand
becomes silently incorrect when the hardware design changes (or when the
code moves to a different project); a constant from `xparameters.h`, in
contrast, updates automatically together with the hardware.

## A Concrete Example: Sending a Character from UART0

Let us now tie all of these concepts to a single concrete operation:
sending the character 'A' at the register level through UART0
(`0xFF00_0000`). What happens behind the driver functions is exactly this:

1. **Read the SR register** (base + `0x2C`).
2. **Check the TXFULL bit** (mask `0x10`). If the bit is 1, the transmit
   FIFO is full — repeat this step until room opens up (this is
   precisely the "polling" pattern you will meet in Chapter 6; its cost,
   and a comparison with interrupts, is covered in Chapter 7).
3. Once TXFULL is zero, **write the ASCII value of the character 'A'** to
   the FIFO register (base + `0x30`).

The hardware takes over from there: it serially transmits the character
out through the physical TX pin. These three steps — read status, wait,
write — form a pattern you will encounter more times in embedded systems
than you could count.

You have now accumulated enough theory. It is time to put it into
practice: your first task is to apply the register logic from this
chapter to a real LED.

## A First Look at Vitis: Opening a Project, Building, and Deploying to the Board

You will open Vitis for the first time shortly, in Task 1; let us describe
the sequence of clicks in advance so that it does not feel unfamiliar when
you encounter it. What Vitis is, the BSP (board support package) concept,
the debugger, Run/Debug configurations, and disassembly are covered in
full depth in Chapter 11 — what is described here is only the sequence of
clicks itself; for now, it is enough to click with an understanding of
what each step does.

On first launch, Vitis asks you to choose a **workspace**: a folder that
holds your projects, settings, and build outputs. Once the workspace is
open, the first task is to select the platform your team has prepared for
you — this is derived from a .xsa file that carries the hardware
description; you do not design the platform, the hardware designer does,
and you select it from a list.

With the platform selected, you open a new **empty application** project:
the "empty application" template does not bring any sample code — it
gives you a shell that you fill from scratch, and this is nearly always
the template you will choose throughout this program. Vitis automatically
links this project to the platform you selected and asks which processor
core it should run on (throughout this program, this will nearly always
be one of the APU's Cortex-A53 cores).

Once the project is open, you place your source files in the project's
`src/` folder — this is exactly why you will copy the solution file there
when you reach a task. You then press the **Build** button; if there are
errors, you see them as red lines in the Console/Problems panel, and if
the build is clean, an executable output is produced and a new
Debug/Release folder appears in the project tree.

Once the build is clean, it is time to deploy to the board: right-click
the project, then **Run As → Launch on Hardware (JTAG)**. Vitis connects
to the board over JTAG, loads what you built, and runs it; an LED on the
board begins to blink, or a line appears in the terminal you opened in
Task 0 — this is the proof that your code has genuinely reached the
board.

This sequence — workspace, select platform, open an empty project, place
code in `src/`, Build, Run As → Launch on Hardware — will pass through
your hands repeatedly from Task 1 through Task 10. Read it step by step
the first time; after a few tasks, your hands will know it by heart.

:::gorev no=1 zorluk=1 baslik="Light an LED (Hello Hardware)" kisa="Light an LED"
[Objective]
Compile a bare-metal application in Vitis, deploy it to the board, and
blink the DS50 LED (PS MIO23) at a 500 ms period (500 ms on / 500 ms
off).

[Prerequisites]
Chapters 3 and 4 read; Task 0 completed (board in JTAG mode, terminal
connection ready).

[Steps]
1. In Vitis, select the ready-made **platform** (hardware definition,
   .xsa) your team has provided — we will examine the
   platform/application-project relationship in full in Chapter 11; for
   now, think of it as "the hardware's description."
2. Open a new **empty application** project and link it to the platform
   you selected.
3. Copy this task's solution file, `lab01-led/src/main.c`, into the
   project's `src/` folder.
4. **Build** the project.
5. **Deploy to the board and run it over JTAG** (Run As → Launch on
   Hardware). We will go into JTAG/debug details step by step in Chapter
   11; these five steps are enough for now.
6. (optional) Open the UART terminal with the settings from Task 0 and
   confirm the "Task 1" line is printed.

   :::derin-dalis Doing the Same Thing Directly with Registers
   Driver functions such as `XGpioPs_WritePin` perform, on your behalf,
   exactly the base+offset arithmetic and read-modify-write operation you
   learned in Chapter 4. If you want to see what lies behind these calls,
   here is an alternative solution that lights the same LED directly
   through a `volatile` pointer (volatile — the compiler must genuinely
   read/write this address on every access; details in Chapter 5), using
   the DIRM_0, OEN_0, and DATA_0 register offsets verified with sources
   in `content/_arastirma-ek-B.md`:
   {{kod:lab01-led/src/main_registers.c}}
   If you are curious, compile this file as a separate application
   project and confirm that DS50 blinks the same way — the behavior
   produced by the two approaches is identical; only the path there
   differs.
   :::

[Success Criteria]
DS50 blinks once per second: 500 ms on, 500 ms off, a regular rhythm
clearly visible to the eye.

[Self-Check]
- If you wrote to the DATA_0 register directly with `=` (i.e., without
  `|=`) instead of using `XGpioPs_WritePin`, what would happen to the
  other MIO pins besides MIO23?
- What are the MASK_DATA (LSW/MSW) registers for, and how do they differ
  from DATA_0?
- If you skipped the `SetDirectionPin` and `SetOutputEnablePin` calls and
  called `WritePin` directly, would the LED light up? Why or why not?

[If You Get Stuck]
::ipucu Hint 1 — If You Confused the Platform/Application Relationship
A "platform component" carries the hardware definition (.xsa) and the
operating-system choice; an "application component" is your own code,
linked to it. If you linked to the wrong or an empty platform, the build
error usually shows up as missing `XPAR_` definitions — check your
platform selection first.
::/
::ipucu Hint 2 — If It Compiles but the LED Does Not Light Up
Did you actually check the return values of `XGpioPs_LookupConfig` and
`XGpioPs_CfgInitialize`? If you see an "ERROR" line on the UART terminal,
verify `DEVICE_ID` against `xparameters.h`. If nothing appears on the
terminal at all, go back to the port/baud settings from Task 0 — the code
may be running fine while the terminal is looking at the wrong port.
::/
::cozum Full Solution — lab01-led
The file below blinks DS50 at a 500 ms period using the `XGpioPs` driver;
it uses the classic (DEVICE_ID) flow, and the SDT difference is noted in
a comment.
{{kod:lab01-led/src/main.c}}
::/
:::

You have read registers from the register map and addressed them by
hand; but the C language's relationship with hardware at this level is
full of subtleties — `volatile`, bit operations, fixed-width types. The
subtleties awaiting you on the C side are the subject of the next
chapter.
