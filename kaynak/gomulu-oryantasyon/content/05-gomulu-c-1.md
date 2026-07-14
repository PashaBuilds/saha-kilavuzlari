# Chapter 5 — Embedded C Practices I: Where the Language Meets Hardware

You have read registers from the register map and addressed them by hand;
but the C language's relationship with hardware at this level is full of
subtleties — this chapter covers the first of them. The C you learned at
university mostly operates on the assumption that "values sit in memory,
and I read/write them." Hardware registers break this assumption: the
value of a register can change in the background, without a single line
of your code executing — a button is pressed, an interrupt arrives, a DMA
(DMA — Direct Memory Access; hardware that writes directly to memory,
bypassing the CPU; details in Chapters 6 and 9) transfers data. In this
chapter, you will learn the tools that let C communicate with this
reality.

## volatile: Telling the Compiler That Its Optimizations Do Not Apply Here

Compilers are not lazy — quite the opposite, they perform aggressive
optimization. If a compiler observes that a variable is read several
times in succession and can "prove" that the variable does not change in
between (it sees no write in the code's own flow), it does not repeat the
read: it holds the value once in a CPU register and silently eliminates
the subsequent reads. For an ordinary variable, this is an excellent
optimization — it avoids unnecessary memory accesses. But consider the
following code:

```c
unsigned int uiFlag = 0;
while (uiFlag == 0)
{
    /* waiting for uiFlag to be set from somewhere */
}
```

The compiler sees that `uiFlag` is never written inside the loop and may
reason, "this value never changes, so I will evaluate the condition once
and fix the result" — the outcome is either never entering the loop, or
being stuck in it forever, even though an ISR or hardware may actually
change `uiFlag`. The `volatile` keyword prevents exactly this: it tells
the compiler, "the value at this address can change from somewhere you
cannot see; genuinely read/write it on every access, and do not rely on a
previous read."

{{svg:sema-10-volatile.svg|Figure 10 — The story of volatile: the same -O2 optimization eliminates the read in code without volatile, and forces a fresh read on every iteration in code with volatile.}}

There are two typical places where you need `volatile`: **hardware
registers** (every read must be a genuine query of hardware state) and
**variables shared between an ISR (interrupt service routine) and the
main code** (you will experience this firsthand in Chapter 7). In both
cases, the common thread is the same: the value can be changed by someone
"from the outside."

:::tuzak A Flag Without volatile Is a Bug That "Appears to Work"
If you read a flag set by an ISR in the main loop without `volatile`, the
code compiles, and may even appear to work at -O0 (an unoptimized build)
— because -O0 does not eliminate redundant reads in the first place. The
instant you enable optimization (such as -O2), the same code appears to
hang. This is one of the most frequent root causes of the classic "works
in debug, fails in release" problem; we will discuss that classic problem
firsthand in Chapter 6.
:::

## Bit Operations: Addressing a Single Bit of a Register

Most of a register's 32 bits each (or each group of bits) carries a
separate meaning — TXFULL is one bit, RXEMPTY is another. Four basic
operations are enough to address a single bit without disturbing the rest
of the register:

| Operation | Expression | What it does |
|---|---|---|
| SET | `uiReg |= MASK;` | Sets the relevant bit to 1, leaves the others untouched |
| CLEAR | `uiReg &= ~MASK;` | Sets the relevant bit to 0, leaves the others untouched |
| TOGGLE | `uiReg ^= MASK;` | Inverts the relevant bit |
| TEST | `if (uiReg & MASK)` | Asks whether the relevant bit is 1, changes nothing |

{{svg:sema-11-bit-islemleri.svg|Figure 11 — Visual reference for bit operations: before/mask/after 8-bit boxes for SET, CLEAR, TOGGLE, and TEST.}}

Generating the mask from a bit number, rather than writing it by hand as
`0x10`, significantly improves readability. On our team, nearly every
project includes the following macro set:

```c
#define BIT(n)          (1u << (n))
#define BIT_SET(reg, n)     ((reg) |=  BIT(n))
#define BIT_CLEAR(reg, n)   ((reg) &= ~BIT(n))
#define BIT_TOGGLE(reg, n)  ((reg) ^=  BIT(n))
#define BIT_TEST(reg, n)    (((reg) & BIT(n)) != 0u)
```

Writing `BIT_SET(UART0_SR, 4)` is both more readable than writing
`UART0_SR |= 0x10` and directly shows the link between the bit number and
the register map document — if the document says "bit 4 = TXFULL," having
your code also say "bit 4" saves time for you (or a colleague) reading
the code again six months later.

## Type Width: Why You Should Care (and Why We Use Plain Types)

The C standard does not guarantee how many bits `int` has — it may be 16,
32, or even 64 bits on some platforms; it depends on the compiler and the
platform. If a register is 32 bits wide and you access it with a type
whose width you do not know, you may silently read or write the wrong
number of bytes — hardware never forgives this. The real lesson here is
not a specific type name: it is **being certain how many bits the access
is.**

The advice you will generally hear is: "use `<stdint.h>`'s fixed-width
types (such as `uint32_t`)." **Our team resolves this differently:** our
standard forbids `stdint.h` types and uses **plain C types** —
`unsigned char`, `unsigned short`, `unsigned int`, `unsigned long long`.
Why is this safe? Because you are writing for a single target: ZynqMP
plus a single toolchain. In that fixed world, the width of every plain
type is certain and known — `unsigned int` is **always 32 bits** on your
target. Since the width is already fixed, there is no need for
`uint32_t`'s extra abstraction; plain types give the codebase a single,
consistent type vocabulary. In other words, you access a register with
`unsigned int` — not a blind `int`, but a type whose width you have
chosen *knowingly*.

:::ekip-notu No stdint — but Understand the Principle
One day, on a different team, you will see `uint32_t`, and that is
correct too — both worlds are different implementations of the same
principle: "access with a type whose width you know." On our team, the
rule is clear: `unsigned char`/`unsigned short`/`unsigned int`/
`unsigned long long` in place of
`uint8_t`/`uint16_t`/`uint32_t`/`uint64_t`. The one exception is **Xilinx
library signatures:** Xilinx headers define their own typedefs,
`u8`/`u32` (these are not `stdint` — they are the library's own types);
when you encounter a signature such as `XUartPs_Send(..., u8* ...)`, you
use Xilinx's type for that parameter. But in your **own** variables, you
always fall back to the plain type (`unsigned int uiOffset`).
:::

## Bitfield Structs: Their Appeal and Their Pitfalls

C lets you define bit fields inside a struct:

```c
typedef struct
{
    unsigned int uiEnable : 1;
    unsigned int uiMode   : 2;
    unsigned int uiRsvd   : 29;
} SUartCrBits;
```

At first glance, this is appealing: writing `sCr.uiEnable = 1;` looks far
more readable than dealing with masks. But the C standard does not define
the order in which these bits are packed inside the struct (from the
front or from the back, and how alignment works) — this is a decision
left to the compiler and the platform ("implementation-defined"). The
same struct may pack its bits in the reverse order on a different
compiler or a different architecture; your code then silently reads and
writes the wrong bits.

:::tuzak A Bitfield's Bit Order Is Not Portable
Even if modeling a register with a bitfield struct appears to "work" on
your desktop, the bit-packing order can change when that code is moved to
a different compiler or a different architecture; the code then silently
reads and writes the wrong bits. This is an unavoidable side effect of
bitfields — a cost you must be aware of when using them.
:::

**On our team, bitfield structs are common practice.** Writing
`sCr.uiEnable = 1;` is both far more readable than mask arithmetic and
makes the intent immediately clear; as a codebase grows, this readability
is a genuine gain. We accept the portability warning above knowingly: our
product code is compiled for a single toolchain (AMD/Xilinx) and a single
target architecture (ZynqMP) — the bit order does not change in a fixed
world we control, so that risk is effectively eliminated for us. Still,
remember two rules: **(1)** never use a bitfield struct for a data format
that moves across compilers or architectures (a network packet, a record
written to a file, a structure shared with another chip) — there, the
lack of a bit-order guarantee turns into a real bug; **(2)** when you
model a new register with a bitfield, verify once, during initial
bring-up, that the fields genuinely align with the hardware layout. The
mask macros (`BIT_SET`/`BIT_CLEAR`/`BIT_TEST`) remain within reach: for
isolated bit touches, or when absolute portability is required, they are
the more direct tool. The two are not competitors — they are two tools in
the same kit.

## Pointer-Based Register Access Patterns

The C equivalent of the base + offset arithmetic you saw in Chapter 4 is
a `volatile` pointer pointing at a fixed address:

```c
#define UART0_SR (*(volatile unsigned int*)(0xFF000000U + 0x2CU))
```

Read this line piece by piece: `0xFF000000U + 0x2CU` computes the actual
address; `(volatile unsigned int*)` interprets this address as "a 32-bit
location that must genuinely be read/written on every access"; the
leading `*` **dereferences** that address, meaning "the value at that
location itself." The result: every time you use the name `UART0_SR`, the
compiler takes you directly to that address — `UART0_SR & 0x10` is a
read, `UART0_SR = 0` is a write. You will use this exact pattern in the
`uart_ps.c` module (Task 2).

Some registers are read-only (recall the RO access type from Chapter 4)
— hardware updates them, and you cannot write to them. The way to express
this in C is the `const volatile` combination:

```c
#define UART0_SR_RO (*(const volatile unsigned int*)(0xFF000000U + 0x2CU))
```

`volatile` still says "genuinely read on every access"; `const` adds the
instruction "produce a compile error if there is any attempt to write
through this pointer." The two do not conflict — one guarantees the
*frequency* of access, the other guarantees its *direction*.

:::ekip-notu These Are Checked in Code Review
On our team, code is also checked by machine (a naming linter plus
clang-format/clang-tidy); violations do not pass review. In summary:

- **Function names** are camelCase, no underscores, English:
  `uartSendChar`, `ina226Init` — not snake_case, such as
  `uart_send_char`.
- **Variables** use a type prefix plus a camelCase body: `uc` (unsigned
  char), `c` (char), `us`/`s` (short), `ui`/`i` (int), `ul`/`ull` (the
  `long` types). A pointer adds `p` to the type prefix (`char*` → `cp`,
  `unsigned int*` → `uip`); a struct pointer uses `sp` (`XIicPs* spIic`);
  an array adds `Arr`; `static` → `S_`, global → `G_` goes at the very
  front (`G_uiTickCount`). Examples: `unsigned int uiIndex`,
  `char* cpString`.
- **Types** are plain C types; `stdint.h` (`uint32_t`) is forbidden (see
  the note above).
- **typedef**: struct → `S` (`SUartCrBits`), enum → `E` (`EState`).
- **Format:** Allman braces, 4-space indentation, lines ≤ 100 characters,
  a space after control keywords, the pointer asterisk attached to the
  type (`XIicPs* sp`), CRLF line endings, `\r\n` in `printf` output.
- **Doxygen** is mandatory on public functions (`@brief`, `@param`,
  `@return`).

These are not an aesthetic fixation: in a codebase spanning hundreds of
files, you can tell what a variable holds and what a function does just
by its name, without opening the file — and because the linter enforces
this for you, review time is spent on substance rather than formatting.
:::

You have now learned the basic vocabulary of C that speaks to hardware:
`volatile`, bit operations, correctly sized types, and pointer-based
addressing. It is time for practice: time to print something from the
UART with your own hands.

:::gorev no=2 zorluk=1 baslik="UART Hello World and What Lies Behind printf" kisa="UART Hello World"
[Objective]
Print a line from UART0 with `xil_printf`, then print a multi-line
welcome banner using your own register-level `uart_ps` module.

[Prerequisites]
Chapters 4 and 5 read; Task 1 completed (the flow for opening an empty
application project in Vitis is familiar to you).

[Steps]
1. Open a new **empty application** project in Vitis and link it to your
   team's platform.
2. Copy this task's solution files — `lab02-uart/src/uart_ps.h`,
   `uart_ps.c`, and `main.c` — into the project's `src/` folder. If you
   would rather try it yourself first, attempt writing your own
   `uart_ps.c` before using the hint ladder below.
3. In `uartSendChar()`, first read the **SR register** (base
   `0xFF000000` + offset `0x2C`), wait until the **TXFULL bit** (mask
   `0x10`) is zero, then write the character to the **FIFO register**
   (offset `0x30`) — this is exactly Chapter 4's final example.
4. Write `uartSendString()` so that it sends the string character by
   character to `uartSendChar()`, sending `'\r'` before `'\n'` whenever
   it encounters `'\n'` (explain why this is necessary in a code
   comment).
5. In `main()`, first print a single line with `xil_printf`, then print
   a several-line welcome banner using your own `uartInit()` /
   `uartSendString()` functions.
6. Build the project, deploy it to the board over JTAG, and open the
   terminal with the settings from Task 0.

[Success Criteria]
On the terminal, you see the `xil_printf` line first, followed by the
multi-line welcome banner printed by your own functions.

[Self-Check]
- What would happen if you did not wait for the TXFULL bit to drop
  (skipped the check)? What happens to characters you write while the
  FIFO is full?
- Why does `%f` not work inside `xil_printf`? (Hint: the answer is in a
  comment in `main.c`, but make your own guess first.)
- Your `uartInit()` function is in fact almost empty — explain in one
  sentence why this is a deliberate design choice rather than something
  "missing."

[If You Get Stuck]
::ipucu Hint 1 — The TXFULL Wait Loop Does Not Work / Never Ends
Are you applying the mask (`0x10`) to the correct address of the SR
register (base + `0x2C`, not `0x30`)? Did you write the `while` condition
as "wait while TXFULL is 1," or did you accidentally write the reverse?
Are you reading SR through a `volatile` pointer — if not, the compiler
may eliminate the read and leave you in an infinite loop (Chapter 5's
central lesson shows up right here).
::/
::ipucu Hint 2 — I'm Sending '\n' but the Terminal Line Does Not Return to Column Zero
Terminals interpret `'\n'` (line feed) as "move down one line, same
column"; to actually return the line to the start, you also need to send
`'\r'` (carriage return). In `uartSendString()`, try calling
`uartSendChar('\r')` first the instant you see a `'\n'` character, then
sending the `'\n'`.
::/
::cozum Full Solution — lab02-uart
The three files below drive UART0 at the register level and print the
welcome banner:
{{kod:lab02-uart/src/uart_ps.h}}
{{kod:lab02-uart/src/uart_ps.c}}
{{kod:lab02-uart/src/main.c}}
::/
:::
