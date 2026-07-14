# Chapter 6 — Embedded C Practices II: Memory and Cache

Chapter 5 covered the language's patterns for communicating with hardware:
`volatile`, bit operations, and correctly sized types. This chapter moves
from the subtleties of the language to the realities of memory — every
variable you declare and every function call you make occupies a location
within the memory map introduced in Chapter 3. By the end of this chapter,
you will be able to answer two questions: where does a given variable
actually reside, and why does the value the CPU sees sometimes differ from
the value stored in DDR.

## Stack, Heap, and Static: Three Memory Regions

Every variable in a C program resides in one of three regions:

- **Stack.** Local variables within a function reside here; space is
  allocated automatically on entry and released automatically on exit. On
  a desktop system, the operating system may raise a page fault and alert
  you when the stack overflows; in our bare-metal environment, no such
  protection exists — the stack can silently overrun into adjacent memory
  (typically the heap or other static data). You will encounter this
  failure directly in Task 10.
- **Static/global (.data and .bss).** Variables declared outside any
  function, or marked with the `static` keyword, occupy a fixed address
  for the lifetime of the program. Variables with an explicit initial
  value are placed in the `.data` section (stored in the ELF file with
  their actual values); variables that begin at zero are placed in the
  `.bss` section (which occupies no space in the ELF file — it carries
  only a "zero this many bytes" instruction, executed at startup).
- **Heap.** Memory allocated and released at run time via `malloc`/`free`.
  It is used liberally on desktop systems; in our environment, it is
  approached with caution.

{{svg:sema-12-bellek-yerlesimi.svg|Figure 12 — Stack/heap/static memory layout: the ELF file's .text/.rodata/.data/.bss sections are placed into RAM via the linker script; the heap grows upward and the stack grows downward.}}

:::ekip-notu In Our Environment: malloc Either Never or Only at Startup
On a desktop application, you can use `malloc`/`free` freely; the
operating system cleans up after you. In bare-metal development, no such
safety net exists: fragmentation, unpredictable latency (the heap manager
offers no guarantee on how long a given call will take), and the "memory
exhausted with no warning" scenario are all your responsibility. The
practical rule on our team is as follows: either **avoid malloc entirely**
(allocate all buffers as fixed-size arrays at compile time), or allocate
memory **once, at startup only**, and never call `free` for the remainder
of the program's execution. Entering a malloc/free cycle mid-runtime
invites problems that are best avoided in embedded development.
:::

## Introduction to the Linker Script: Placing the ELF into the Memory Map

The compiler translates your `.c` files into `.o` (object) files; at this
stage, however, these files do not yet contain information about which
address a given function will occupy. This task is performed by the
**linker**, and the file that instructs the linker on which section to
place at which address is called the **linker script** (in Xilinx tools,
typically named `lscript.ld`, automatically generated from the platform's
.xsa file).

The **ELF** file produced by compilation is divided into several standard
sections: `.text` (compiled machine code), `.rodata` (read-only constants,
such as string literals), `.data` and `.bss` (the static variables
described above), and space reserved for the heap and stack. The linker
script assigns each of these an address range from the memory map
introduced in Chapter 3 — in a typical bare-metal project, all of them are
placed in DDR Low (the region starting at `0x0`); OCM, owing to its
limited size, is generally reserved for special cases such as the FSBL.
Vitis generates this file for you based on the platform's memory map, and
in most cases you will work without modifying it directly. Knowing that it
exists and what it does, however, is invaluable when you encounter an
error such as "program does not fit at this address."

## Cache: An Ally of Speed, an Adversary of Consistency

The **cache** is a small but very fast memory that sits between the CPU
and DDR. Every access to DDR is slow relative to CPU speed; the cache
narrows this gap by keeping frequently used data close to the CPU. Under
normal conditions, the cache is entirely transparent — it performs its
function without any action on your part, and your program runs faster.

This transparency holds as long as a single writer — the CPU — accesses
memory. The problem arises when a **second writer** enters the picture:
for example, a **DMA** (Direct Memory Access, a hardware unit that
transfers data directly to memory, bypassing the CPU) engine, or an IP
block in the PL, writes directly to DDR. The CPU's cache has no knowledge
of this write; when the CPU subsequently reads that address, it returns
the **stale** copy held in the cache rather than the newly written data in
DDR.

{{svg:sema-13-cache-dma.svg|Figure 13 — Cache hierarchy and consistency: the CPU reading stale data from cache after DMA writes new data to DDR, and the return to correct reads following an invalidate.}}

This is the "DMA wrote, but the CPU is reading stale data" scenario, and
it is one of the classic sources of error in embedded development. The
remedy is to instruct the CPU to discard its cached copy for the given
address range and genuinely access DDR on the next read — this operation
is called **invalidate**. A converse need also exists: the CPU has written
data that still resides only in cache, and you need a DMA engine to read
that data from DDR — in this case, the CPU's "dirty" cached data (not yet
written to DDR) must be written out to DDR, an operation called **flush**.

The Xilinx standalone BSP (BSP — Board Support Package; the intermediate
layer that contains or generates peripheral drivers, startup code, and
xparameters.h; discussed in detail in Chapter 11) provides these
operations as ready-made functions: `Xil_DCacheInvalidateRange(address,
length)` and `Xil_DCacheFlushRange(address, length)`. The rule is simple:
**invalidate a region written by DMA before the CPU reads it; flush a
region written by the CPU before DMA reads it.**

:::derin-dalis On the A53, FlushRange Is Actually InvalidateRange
The ARMv8 (Cortex-A53) standalone BSP contains a notable detail: the
`Xil_DCacheFlushRange` function is defined directly in the source code as
an alias (macro) for `Xil_DCacheInvalidateRange` —
`#define Xil_DCacheFlushRange Xil_DCacheInvalidateRange`. In other words,
although the name suggests "flush," on the A53 this macro actually
performs a range-invalidate operation (which, on ARMv8, is implemented as
a "clean+invalidate" that cleans before invalidating). The practical
implication: in A53 code, you may encounter both names, and both resolve
to the same hardware operation — but the name does not always accurately
reflect the conceptual operation it invokes. Source: `content/_arastirma.md` §10.
:::

## Alignment: The Address Boundary

**Alignment** is the requirement that the starting address of a piece of
data be a multiple of its own size — for example, a 4-byte `unsigned int`
must reside at an address that is a multiple of 4, and an 8-byte
`unsigned long long` at an address that is a multiple of 8. On most ARM
architectures, unaligned access works but is slower (or, in some cases,
does not work at all); DMA transfers, on the other hand, frequently
**require** a specific alignment (for example, the cache line size —
typically 64 bytes). The compiler handles alignment of ordinary variables
automatically; when you need to align a buffer intended for DMA manually,
you use an attribute such as `__attribute__((aligned(64)))`. For now, it
is sufficient to be familiar with the concept — it will reappear when DMA
is addressed in Chapter 9.

:::tuzak "It Works in Debug but Not in Release" — a Familiar Pattern
You will hear this statement — and make it yourself — repeatedly over the
course of an embedded career. It has two common root causes, both of
which trace back to material covered in these two chapters. **(1) Missing
`volatile`** — a debug build is typically compiled with `-O0` (no
optimization); the compiler does not eliminate ostensibly redundant reads
or writes, and the code works "by accident." A release build is compiled
at a more aggressive level, such as `-O2`; the compiler applies the
optimization described in Chapter 5, and if `volatile` is missing, a read
silently disappears. **(2) Cache/DMA consistency** — a debug build
generally runs a slower, more predictable execution path (or the cache is
disabled in some debug configurations); once speed increases in the
release build, the window in which the CPU reads stale data from cache
becomes a real problem. Both cases illustrate the same principle: the code
was not correct to begin with, and the optimization level merely exposed a
pre-existing defect that -O0 had been concealing.
:::

You now understand where memory is placed and when the cache can and
cannot be trusted. It is time to put this into practice: this time, you
will read the board's single input device — the button.

:::gorev no=3 zorluk=1 baslik="Read the Button (Polling)" kisa="Read the Button"
[Objective]
Read the SW19 button (PS MIO22) via polling and reflect its state on the
DS50 LED (PS MIO23); print a debounced press counter to the UART.

[Prerequisites]
Chapter 6 has been read; Task 2 is complete (`uart_ps` module is ready and
functioning).

[Steps]
1. Recall from Chapter 2 that the board's 8 LEDs, 5 buttons, and DIP
   switch are on PL pins — this task again uses only the single PS button
   (SW19) and the single PS LED (DS50); the 8-LED running-light pattern is
   reserved for Task 7.
2. Write the `button_ps.h/.c` module: in `buttonInit()`, configure the
   `XGpioPs` driver (familiar from Task 1) via `LookupConfig` +
   `CfgInitialize`; set SW19 as input and DS50 as output (plus output
   enable).
3. In `buttonRead()`, read SW19 via `XGpioPs_ReadPin`; in `ledPsWrite()`,
   drive DS50 via `XGpioPs_WritePin`.
4. In `main()`, read SW19 every few milliseconds (`usleep`, `sleep.h`); if
   the raw value read remains consistent across several successive
   iterations and differs from the current stable state, treat the
   transition as genuine (counter-based debounce — see the analogy
   below), update the LED, and increment a counter on every transition
   toward the pressed state.
5. When the counter changes, print a status line using your `uart_ps`
   module (reusing the output of Task 2).

:::analoji Debounce Resembles Determining Whether a Doorbell "Really" Rang
A single press of a mechanically noisy doorbell button can cause the bell
to ring several times in rapid succession; you nonetheless conclude that
"someone rang once," not three times. Your brain accomplishes this by
disregarding brief fluctuations and checking whether the state "is still
the same a moment later." Counter-based debounce operates on the same
principle: it does not trust a raw reading immediately, but waits until
the same value is observed across several consecutive iterations.
:::

[Success Criteria]
DS50 remains lit for as long as the button is held down and turns off the
moment it is released; after exactly 10 button presses, the UART counter
reads exactly "10" — not 11 or 12 due to bounce.

[Self-Check]
- On what basis did you choose the debounce duration (sampling interval x
  number of consecutive iterations)? What would happen if it were too
  short, and what would happen if it were too long?
- While this polling loop runs, the CPU cannot perform any other work —
  how long does each loop iteration take, and what fraction of CPU time is
  spent on this waiting?
- If you wrote the raw value returned by `buttonRead()` directly to the
  LED without debouncing, what visible difference would you observe?

[If You Get Stuck]
::ipucu Hint 1 — LED Never Lights or Stays Lit
Did you configure the direction (DIRM) and output-enable (OEN) registers
for the correct pins — SW19 (MIO22) as input, DS50 (MIO23) as output? Did
you check the return value of `buttonInit()`? If it does not return
`XST_SUCCESS`, check `xparameters.h` to confirm that
`XPAR_XGPIOPS_0_DEVICE_ID` is correct.
::/
::ipucu Hint 2 — Counter Skips (Reads 11-12 for 10 Presses)
`DEBOUNCE_ESIK` (the consecutive-identical-reading threshold) may be too
small — a bounce can last long enough across several consecutive
iterations to be mistaken for a genuine transition. Increase the
threshold and reconsider it together with the sampling interval (how
often, in microseconds, you read); the product of the two is your
debounce window.
::/
::cozum Full Solution — lab03-button
The following files read SW19/DS50 via debounced polling and print to
UART (the `uart_ps` module is an exact copy from lab02):
{{kod:lab03-button/src/button_ps.h}}
{{kod:lab03-button/src/button_ps.c}}
{{kod:lab03-button/src/main.c}}
::/
:::

Because you queried the button every few milliseconds, the CPU spent
nearly all of its time asking that question — you have now seen the cost
of polling. It is time for interrupts: in Chapter 7, the same button will
notify you without occupying the CPU at all.
