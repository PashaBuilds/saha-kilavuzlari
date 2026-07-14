# Chapter 9 — PS ↔ PL: AXI and the World of IP

In Chapter 8, you worked at the wire level: UART, SPI, I2C — protocols that
connect the board to the outside world. Now we turn *inward*, into the chip
itself. In Chapter 2, we noted that the PS and PL are joined through **AXI**
bridges, with the detail deferred to Chapter 9. This is that chapter. By the
end, you will know how to communicate with an IP block provided by a
hardware engineer — and you will fulfill the commitment made at the close of
Chapter 2 by lighting all 8 LEDs.

## AXI: The Common Language of PS and PL

**AXI (Advanced eXtensible Interface)** is the name of Arm's family of
on-chip data buses; on the Zynq, every data exchange between the PS and the
PL takes place through some variant of this protocol. Before going into
detail, fix one intuition in mind: AXI is built on a **valid/ready
handshake**. The sending side states "I have valid data" (**VALID**); the
receiving side states "I am ready to accept it" (**READY**). Not a single
bit crosses over until both signals are high at the same time — either side
may make the other wait, and neither can force data through. This resembles
the "can you hear me" — "I can hear you" handshake on a phone call: if one
party speaks while the other has already hung up, the message is lost.

{{svg:sema-20-axi-el-sikisma.svg|Figure 20 — AXI valid/ready handshake timing diagram (top) and the journey of a read request from the PS to an AXI GPIO in the PL (bottom).}}

In AXI, read and write operations travel over separate **channels** (an
address channel, a data channel, and, for writes, an additional "response"
channel) — the full detail is not important for now. What matters to you is
this: when you read or write a register, all of these handshakes take place
behind a single CPU load/store instruction (`Xil_In32`/`Xil_Out32`, or
direct `volatile` pointer access). Register access is exactly what you
learned in Chapter 4; AXI is simply the mechanism that carries that access
through to the PL.

## How a PL IP Block Appears from the PS

When a hardware engineer places a circuit in the PL (a signal-processing
block, a motor driver, or a simple LED controller), that circuit appears to
the PS in exactly one way: **a set of registers accessed through an address
window**. In Vivado (the design tool used by hardware engineers), every IP
block is assigned a base address and a size through the Address Editor;
this window appears in your `xparameters.h` as a line of the form
`XPAR_<name>_BASEADDR`. Communicating with an IP block in the PL is
therefore no different from the workflow you learned in Chapter 4: take
the base address, add the offset, and read or write. The difference is
that this time the address is not fixed in silicon — it is a window that
**varies with the design**.

On our team, this workflow is well defined: the statement "a hardware
engineer delivered an IP block" is not, on its own, sufficient. You require
two additional items — the **.xsa** file that accompanies the bitstream
(the platform definition that carries the address windows into
`xparameters.h`) and the IP block's **register map** (which offset does
what, and what each bit means). Without both, what you have is nothing
more than a "black box."

:::ekip-notu An IP Block Is Not Accepted Without an Offset Table
On our team, when a hardware engineer tells you, "I have placed the IP
block in the PL, go ahead and use it," the first question is: "Where is
the register map?" For an off-the-shelf IP block (such as AXI GPIO), the
vendor's product guide (referred to by a "PGxxx" number for Xilinx) serves
this purpose. For a custom-designed IP block, the hardware engineer is
expected to provide, at minimum, an offset table and a note describing the
meaning of every bit — this is the most fundamental contract between
software and hardware. You should not consider an IP block "accepted"
until you have requested this table; asking "what did that bit do again"
days later is a loss you could have avoided with a single question at the
outset.
:::

## Standard IP Blocks: A Box of Ready-Made Parts

Not every IP block is designed from scratch; Xilinx (and third parties)
maintain libraries of ready-made IP blocks for commonly used functions,
which the hardware engineer drags into place in Vivado. The three you are
most likely to encounter in your work:

- **AXI GPIO** — the simplest IP block, allowing you to read and write PL
  pins from the PS; it is also the subject of Task 7. It has its own
  register map (covered shortly); it shares the same *concept* as PS GPIO
  (Chapters 4–7) but is a separate piece of hardware with a separate
  driver family (`XGpio`, not `XGpioPs`).
- **AXI Timer** — a timer that resides in the PL, similar to the PS's TTC
  (Chapter 7), but instantiable in whatever quantity and configuration the
  hardware engineer requires.
- **AXI BRAM Controller** — provides AXI access to the PL's Block RAM
  (embedded memory within the FPGA fabric); you can think of it as a small
  shared memory.

All three belong to the same family: viewed from the PS, each is simply an
address window and a register map. Learning one teaches you how to work
with the others as well.

## The Door Opens: All 8 LEDs Now Accessible

In Chapter 2, we noted plainly that the board's 8 user LEDs (DS11–DS18)
are wired to PL pins and are not accessible from the PS without a
bitstream. Throughout Tasks 1–5, you worked with DS50 alone. That
limitation is lifted here: in the bitstream prepared by the team, an
**AXI GPIO** IP block is connected to the `GPIO_LED[7:0]` pins — that is,
to DS11–DS18. You will read this IP block's register map and apply the
same Chapter 4 approach (base address + offset) once again; the only
difference is that this time the address comes from a `.xsa` file.

:::derin-dalis AXI-Lite, AXI4, and AXI-Stream: Three Variants, Three Purposes
The AXI family has three members you will most commonly encounter in the
PS–PL world; all three share the same valid/ready concept, but they serve
different workloads:

- **AXI-Lite**: the simplest member. It reads or writes one register at a
  time and does not support bursts (transferring multiple consecutive
  addresses within a single request). Register-based, low-speed control IP
  blocks such as AXI GPIO use this — it is the interface you work with in
  Task 7.
- **AXI4 (AXI4-Full)**: supports bursts — it can carry multiple
  consecutive data words in a single request (for example, sixteen 32-bit
  words within one handshake sequence). It is used for memory accesses
  that demand high bandwidth (such as BRAM/DDR controllers).
- **AXI-Stream**: has no concept of an address — it carries a continuous,
  ordered stream of data (in place of an address, the logic is simply
  "the next data word"). It is used to move data from IP block to IP block
  between functions that require continuous data flow, such as image
  processing or RF sampling.

It is not practical for the CPU to move large volumes of data (a camera
image, a block of RF samples) by reading individual registers one at a
time — doing so saturates the CPU. This is where **DMA (Direct Memory
Access)** comes in: you instruct it to "move this much data from this
source to that destination," and the transfer proceeds in the background
over AXI4/AXI-Stream without occupying the CPU; the CPU is notified with
an interrupt (Chapter 7) once the transfer completes. DMA itself resurfaces
in Chapter 13 (Horizon Tour); for now, it is enough to recognize the
concept of "bulk data transfer that bypasses the CPU."
:::

The best way to learn a register map is to get your hands dirty. Task 7 is
next.

:::gorev no=7 zorluk=2 baslik="Communicate with an IP Block in the PL" kisa="PL LEDs"
[Objective]
Access the registers of an AXI GPIO IP block in the team-provided bitstream
using a volatile pointer, and produce a left-to-right walking-light pattern
on the 8 user LEDs (DS11–DS18).

[Prerequisites]
Chapter 9 read; Task 0 completed. The hardware side (bitstream/.xsa) is
**provided by the team** for this task — the design is assumed to have an
AXI GPIO IP block connected to the `GPIO_LED[7:0]` pins (see
`labs/lab07-axigpio/README.md`).

[Steps]
1. Create a platform component in Vitis from the `.xsa` file provided by
   the team (OS: `standalone`, processor: `psu_cortexa53_0`).
2. In the generated `xparameters.h`, find the AXI GPIO IP block's base
   address: you are looking for a line of the form
   `XPAR_<instance-name>_BASEADDR`. This is the address window the
   hardware engineer assigned to this IP block in the Vivado Address
   Editor (box 3 in the lower half of Figure 20). The instance name
   depends on the name the hardware engineer gave the IP block in Vivado;
   this lab assumes `axi_gpio_0`.
3. Confirm the AXI GPIO register map — for this document it was verified
   against Xilinx PG144 and recorded, with its source, in
   `content/_arastirma-ek-E.md`: `GPIO_DATA` at offset `0x0000` (data),
   `GPIO_TRI` at offset `0x0004` (direction: bit=0 output, bit=1 input).
4. First write to `GPIO_TRI` to set all 8 bits to output, then write the
   walking-light pattern to `GPIO_DATA` by shifting a single bit in
   sequence — using direct `volatile`/`Xil_Out32` register access, as in
   `labs/lab07-axigpio/src/main.c`.
5. Deep dive (optional but recommended): reimplement the same task using
   Xilinx's ready-made `XGpio` driver (`XGpio_Initialize`,
   `XGpio_SetDataDirection`, `XGpio_DiscreteWrite`); observe that both
   approaches produce identical register traffic.

[Success Criteria]
You observe a regular left-to-right walking-light pattern across the 8
user LEDs (DS11–DS18).

[Self-Check]
- What exactly does the `GPIO_TRI` register do? What happens if you forget
  to configure it?
- If a second AXI GPIO IP block existed in the same bitstream, where would
  you find its address?
- Why can the AXI GPIO's base address vary from design to design, while
  the PS GPIO's base address (`0xFF0A_0000`) is always the same?

[If You Get Stuck]
::ipucu Hint 1 — None of the LEDs light up
First confirm that you have configured `GPIO_TRI` correctly: bits written
as zero become outputs. If you skip the direction setup (or reverse it),
nothing you write to `GPIO_DATA` is reflected externally — the hardware
may be holding you in "input" mode. Second suspect: did you read the base
address correctly, or did you confuse it with the PS GPIO's address
(`0xFF0A_0000`)?
::/
::ipucu Hint 2 — I cannot find the name I am looking for in xparameters.h
The IP instance name in Vivado maps directly to the macro name, but it is
converted to uppercase and hyphens become underscores. List every line
containing `BASEADDR` in the file (`grep BASEADDR xparameters.h`) and
narrow it down until a single candidate resembling an AXI GPIO remains. If
multiple AXI GPIO blocks exist, ask the hardware engineer which one is
connected to the LEDs — this, too, is part of register-map culture.
::/
::cozum Full Solution — lab07-axigpio
`labs/lab07-axigpio/src/main.c` uses a volatile pointer to access the
TRI/DATA register pair; the comment block at the end of the file shows how
to accomplish the same task with the `XGpio` driver.
{{kod:lab07-axigpio/src/main.c}}
::/
:::

You have opened the door to the PL and seen both sides of the hardware.
Now it is time to scale up the software — the next stop is the transition
from a single `main()` function to a genuine operating system.
