# Chapter 3 — How the System Boots: Boot Process and Memory Map

In Task 0, you powered on the board (or intentionally left it in JTAG mode,
which prevents it from booting on its own). In that instant, before you had
written a single line of code, an extensive sequence of operations began
inside the board. This chapter follows that sequence step by step and
introduces the resulting picture — the memory map. Before you can
communicate with registers, you need to answer the question "what resides
at which address"; this chapter provides exactly that answer. There are two
parts: first we examine the sequence itself (the boot chain), then we
examine the resulting picture (the memory map).

## Chapter 3 · Part One: From Reset to main() (the Boot Chain)

## From Reset to main(): Four Stages

On the Zynq UltraScale+, the first code that executes the moment reset is
released is not code you wrote — it is a chain of code embedded in the
chip's own silicon, which you cannot modify. There are four stages, in
sequence:

1. **PMU ROM.** The PMU (Platform Management Unit) is a small controller
   that operates independently of the CPU cores. The PMU ROM code, which
   takes over as soon as reset is released, establishes the power
   sequencing and clock trees — the platform's basic configuration is in
   place before the CPUs even "wake up."
2. **CSU ROM (BootROM).** Control then passes to the primary boot code:
   the CSU ROM reads the boot mode (mode pins) from the position of the
   SW6 switch and locates and loads the **FSBL** from the selected
   external device (JTAG, QSPI flash, or SD card).
3. **FSBL (First Stage Boot Loader).** This is where code that is closest
   to your software world begins. The FSBL initializes DDR memory
   (configures the controller, performs memory training), loads the PL
   bitstream if one is present and configures the FPGA fabric, and
   finally places your application in memory and jumps to it.
4. **The application** (or, as an intermediate layer, **ATF**). In a
   bare-metal hello-world, the FSBL loads and runs your application
   directly; on a system running Linux, an ATF (ARM Trusted Firmware)
   layer follows the FSBL, then U-Boot/Linux. Since this program works
   exclusively in bare-metal, your `main()` will be the point the FSBL
   jumps to directly.

{{svg:sema-05-boot-akisi.svg|Figure 5 — Boot flow timeline: PMU ROM → CSU ROM (BootROM) → FSBL → (ATF) → application; below, the contents of boot.bin; at the bottom, the SW6 boot-source branching.}}

The FSBL is itself a program that must be loaded somewhere: since DDR is
not yet ready, the BootROM loads it into **OCM** (On-Chip Memory, 256 KB);
its start address is precisely `0xFFFC_0000` (you will find the full range
in the address summary at the end of the chapter). The logic here is
straightforward: the code responsible for initializing DDR cannot itself
reside in DDR, so a small memory block that is always ready on the chip
(OCM) is reserved for this purpose.

## boot.bin: Three Components in a Single File

When the board powers on, the BootROM reads a single file: **boot.bin**.
This file is in fact composed of three distinct components arranged in
sequence: the **FSBL**, the **PL bitstream** (if present), and **your
application**. Vitis (or, in the classic flow, the bootgen tool) packages
these three components into a single file for you; this is the same single
file that is written to an SD card or QSPI flash. In JTAG boot mode, you
skip even this packaging step — Vitis loads the FSBL and your application
directly onto the board through the debugger; the boot.bin concept
demonstrates its real value in "self-booting" scenarios such as SD or
QSPI.

## Boot Modes: The Language of the SW6 Switch

The board reads which source to boot from off a 4-pole DIP switch named
**SW6**. Each switch corresponds to one mode bit, and the logic is
inverted: **when a switch is in the ON position, the corresponding bit is
0.** This means that an "all ON" appearance can be misleading — it in fact
represents "all zero."

| Boot Mode | Mode Pins [3:0] | SW6 [4:1] |
|---|---|---|
| JTAG | 0000 | ON, ON, ON, ON |
| QSPI32 (factory default) | 0010 | ON, ON, OFF, ON |
| SD | 1110 | OFF, OFF, OFF, ON |

If you set the board to the JTAG position in Task 0, you personally
verified the first row of the table. The board ships from the factory in
the QSPI32 position — meaning you likely had to flip a switch. The SD card
slot is **J100**; to boot from SD, you place boot.bin on the card, set SW6
to the SD position, and power-cycle the board.

At this point, you have seen how the board brings itself up on its own:
from the PMU to the CSU ROM, from there to the FSBL, and from there to
your `main()`. We now move to Part Two: how the CPU perceives the world
once the system is up — that is, the memory map.

## Chapter 3 · Part Two: Everything Has an Address (the Memory Map)

## The Memory Map: Everything Has an Address

You now know the system is up. But how does the CPU express an operation
such as "write to the UART" or "turn on this LED"? The answer is simple
but critical: **everything has an address.** DDR memory, on-chip memory,
the registers of each peripheral, and any IP residing in the PL each have
their own address range. From the CPU's perspective, all of these live in
the same flat address space — writing to RAM and writing to a UART
register are, at the hardware level, the same operation; only the address
differs.

{{svg:sema-06-bellek-haritasi.svg|Figure 6 — Memory map bar: DDR Low (2 GB, 0x0), PL address windows, peripheral register blocks (UART0/UART1/GPIO/TTC0), OCM (0xFFFC_0000); on the right, in a separate bar, DDR High (0x8_0000_0000).}}

The map is divided, broadly, into four regions:

- **OCM — 256 KB.** The first destination of the FSBL that you just saw
  (starting at `0xFFFC_0000`); small but always ready, it does not
  require separate initialization the way DDR does.
- **DDR Low — 2 GB, starting at `0x0`.** The application's primary
  working area: code, the stack, the heap (the dynamic memory pool), and
  data all reside here (the concepts of stack/heap/linker script are
  covered in Chapter 6; for now: a script — the linker script —
  determines where in memory each section is placed). The ZCU111's
  PS-side DDR4 SODIMM is in fact a single 4 GB module, but only the lower
  2 GB of that 4 GB is visible in this region.
- **DDR High — the upper 2 GB of the SODIMM,** an entirely separate
  window starting at `0x8_0000_0000`. It is not a continuation of DDR
  Low; it appears far away in the address space, in a separate corner.
  The gap between them is not physical — it is a consequence of the
  ZynqMP's addressing architecture.
- **Peripherals and PL windows.** The register blocks of PS peripherals
  such as UART0, GPIO, and TTC0 are arranged around `0xFF00_0000` (full
  addresses are in the table at the end of the chapter); IP residing in
  the PL (Chapter 9) is likewise visible through its own address
  windows, according to the hardware designer's layout.

:::analoji A Memory Map Is Like a City Zoning Plan
A zoning plan determines in advance which zone is residential, which is
industrial, and which is a government building; you cannot construct a
building at the wrong address. A memory map operates the same way: DDR is
a large "residential zone" — you may fill it as you see fit; OCM is a
small, valuable central plot; peripherals are government offices, each
with its own address. If you knock on the wrong door (write to the wrong
address), either nothing happens, or something considerably worse does.
:::

:::tuzak Do Not Assume a 4 GB SODIMM Means a Contiguous 4 GB Address Range
The PS DDR4 module on the ZCU111 is physically a single 4 GB part, but in
the memory map it is **not** a single contiguous address block. The lower
half of the SODIMM (2 GB) resides in the DDR Low region, from `0x0` to
`0x7FFF_FFFF`; the upper half (the remaining 2 GB) appears in an entirely
separate window, as DDR High, starting at `0x8_0000_0000`. The addresses
in between are empty — they are not part of the SODIMM. If you assume
this is a single contiguous block and let a buffer or linker script
section overrun that boundary, the compiler will not warn you; on the
board, you will end up with an application that silently writes to the
wrong address.
:::

:::derin-dalis Behind the Scenes: ATF and the PMU
The PMU is a small microcontroller that operates independently of the CPU
cores; it handles power sequencing and clock trees before the CPUs even
come online — the first stage we called PMU ROM is this unit's code. ATF
(ARM Trusted Firmware) is an intermediate layer that can take over after
the FSBL, establishing a secure environment before handing control to the
application or to an operating system (Linux, U-Boot); in our bare-metal
work, this layer is inactive because the FSBL loads the application
directly, but you will certainly encounter it if you work on a Zynq
system running Linux on the team. TrustZone is the name of the
architecture that enforces the hardware's "secure" and "non-secure" world
separation at the chip level — for now, it is enough to know the name.
:::

## Address Summary for This Chapter

All addresses covered in this chapter, at a glance:

| Component | Address / Range | Note |
|---|---|---|
| OCM (on-chip memory) | `0xFFFC_0000`–`0xFFFF_FFFF` | 256 KB, the FSBL's first destination |
| FSBL load address | `0xFFFC_0000` | Same address as the start of OCM |
| DDR Low | `0x0000_0000`–`0x7FFF_FFFF` | 2 GB, the application's primary working area (code, stack, heap, data) |
| DDR High | `0x8_0000_0000`–`0xF_FFFF_FFFF` | Separate 32 GB window; the upper 2 GB of the SODIMM is visible here |
| UART0 | `0xFF00_0000` | PS peripheral register block |
| GPIO | `0xFF0A_0000` | PS peripheral register block |
| TTC0 | `0xFF11_0000` | PS peripheral register block |

You have seen the map; an address is no longer an abstract concept. We
will now knock on each door in turn: every peripheral has its own
registers and its own rules — that is precisely the subject of the next
chapter.
