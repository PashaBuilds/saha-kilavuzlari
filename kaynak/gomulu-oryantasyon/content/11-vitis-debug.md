# Chapter 11 — The Toolbox: Vitis and Debug

You have used Vitis repeatedly since Chapter 4, but always in pieces: a
project appeared in front of you somehow each time, you pressed the build
button, and the code made its way onto the board. It is now time to pause
and assemble these pieces into a single map — because in Task 10 you will
need every corner of that map at once.

## Concept Map: Workspace, Platform, Application

Vitis revolves around three concepts, and each requires the others.

The **workspace** is the folder on disk where you keep your projects; each
time you open Vitis, you choose which workspace to work with. You do not
share a workspace with your teammates — everyone has their own copy on
their own disk; what is shared are the source files in the git repository.

The **platform component** is the translation of hardware into software.
The hardware engineer exports a **.xsa** file from Vivado (the hardware
definition — which peripherals exist, which IP blocks are loaded in the
PL, clock frequencies, the memory map); you add this .xsa to Vitis as a
platform. Vitis then generates a **BSP** (board support package — the
intermediate layer containing the peripheral drivers and startup files;
`xparameters.h` is generated directly from this) on top of it. The
platform also carries the operating-system choice: standalone (no
operating system, used for most of our journey) or freertos10_xilinx (the
FreeRTOS BSP you were introduced to in Chapter 10).

The **application component** is where your `main.c` and its companion
files live. It attaches to a platform — gaining access to the drivers and
addresses the platform generates — but compiles independently of the
platform. You can build multiple application components on top of the
same platform: one a trial "hello world" project, another your actual
work.

{{svg:sema-23-vitis-anatomi.svg|Figure 23 — Vitis concept map: the platform component generated from the .xsa (BSP + hardware definition), the application component built on top of it; on the right, the debug chain connecting to the board over JTAG/hw_server.}}

Once you grasp this three-way relationship, Vitis's menus stop being
buttons you click at random and settle into a logical sequence: platform
first, then application, then build.

## Unified IDE or Classic?

A few releases ago, Vitis moved to a new interface named the **Unified
IDE**; this interface has recently become the default, and the older
**Classic Vitis IDE** is being deprecated. The concept map is identical
between the two — the platform/application distinction, the JTAG flow,
and the debugger logic do not change — but the menu paths and the internal
structure of project files differ (`.mss`/`.mld` files in Classic, a
CMake-based structure in Unified).

:::ekip-notu Use Whichever Version the Team Uses
This document does not mandate a specific version number for you — as
stated in Chapter 0, you learned the setup from the team, so work with
whichever Vitis version the team uses. The menu name on your screen may
look slightly different from what is described here; if the underlying
concept is the same (create platform, create application, build, start
debug), you are on the right track. Asking a senior colleague about a menu
name you are unsure of is better than guessing wrong and losing half an
hour.
:::

## Opening a Project, Building, and Run/Debug Configurations

When you open a new application, Vitis offers ready-made templates; the
**Hello World** template is ideal for your first attempt — a tiny,
build-ready project that prints a greeting message over UART. For your own
projects, you start from this template and move in the source files you
have been writing since Task 1.

Building compiles your source files with the cross compiler (a compiler
that runs on your computer but produces machine code for the Arm core)
and produces an **ELF** (executable output file). If the build succeeds,
you can send this ELF to the board in two ways:

- **Run configuration:** loads the ELF onto the board and runs it
  directly. It is fast, but when something goes wrong, all you have to go
  on is the UART output.
- **Debug configuration:** loads the ELF onto the board but halts the core
  at the start (typically at the first line of `main()`) and attaches the
  debugger. You will use this second option throughout Task 10.

The difference may seem like a minor detail, but it is worth making into a
habit: when confronted with the question "why isn't this working," your
reflex should be to switch to Debug, not to keep retrying Run.

## JTAG: One Cable, Two Jobs

The single J83 micro-USB cable you connected to your board in Task 0
performs two jobs at once: **Port A** of the board's **FT4232** bridge
carries JTAG (programming and debug access), while **Port B** carries the
PS UART0 that your terminal output reads. That means your UART window
keeps streaming over the same cable even while a debug session is open —
you do not need to hunt for a second cable.

Vitis's communication with the board over JTAG passes through a background
process named **hw_server**; Vivado's Hardware Manager connects to the
same hw_server, meaning the two tools can share the board in sequence
(having both try to program the board at the same time causes conflicts —
proceed one at a time).

## Face to Face with the Debugger: From Breakpoints to Disassembly

When you start a debug configuration, a view with four key elements
appears:

- **Breakpoint:** you tell a line of code "stop when you reach here." The
  core freezes when it reaches that line, and you examine the state.
- **Step over / step into:** when moving to the next line, you choose
  between skipping over a function call without entering it (over) or
  diving into it and stepping through it as well (into).
- **Variable, register, and memory windows:** you watch the current
  variable values, the processor's registers, and the raw contents of any
  memory address you choose, live. The registers we described in Chapter 4
  as "address = door number" are now visible on screen as real numbers.
- **Disassembly:** a window showing which processor instructions your C
  lines were translated into by the compiler.

Most newcomers regard this last item with apprehension — "I cannot read
assembly." The reality is that you do not need to read it, only
*recognize* it. When you see `LDR`/`STR`, note "read from memory / write
to memory" and move on. What is genuinely valuable is this: you can see
with your own eyes, in the disassembly, that a read of a variable you did
not mark `volatile` is eliminated entirely by the compiler — the concrete
proof of the story told in Chapter 5 (Figure 10) stands right there on
your screen.

:::derin-dalis Tracing volatile in the Disassembly
Place two compilations side by side. Code that reads a non-`volatile` flag
in a loop typically produces something like the following once
optimization is enabled (`-O2`) — the variable is loaded into a register
once, and memory is never visited again for the rest of the loop:

```metin
; G_ucFlag NOT volatile, -O2
LDR   w0, [x1]        ; loaded ONCE
loopContinue:
b.eq  loopContinue     ; the same register is checked from then on
```

Once `volatile` is added, the compiler genuinely goes to memory on every
iteration of the loop:

```metin
; G_ucFlag volatile, -O2
loopStart:
LDR   w0, [x1]        ; reloaded on EVERY iteration
b.eq  loopStart
```

You will encounter exactly this dilemma in Task 10; the disassembly window
will be the place where your suspicion turns into proof.
:::

## XSCT/xsdb: The Console Behind the Console

Underneath Vitis, behind the IDE's graphical interface, runs **XSCT**
(Xilinx Software Command-Line Tool); the command-line interface used for
interactive target control is **xsdb**. In your daily work you do not need
to invoke XSCT by hand — Vitis runs it for you — but if you ever need to
write automation or query a detail the IDE does not surface, the XSCT
console window inside the IDE exists for exactly that purpose. For now,
simply be aware that it exists; when a teammate tells you to "check it
from xsct," you will know where to look.

{{svg:sema-24-debug-akisi.svg|Figure 24 — Debug session cycle: connect JTAG → set breakpoint → run/halt → step through → watch register/memory/variables → form a hypothesis → fix and rebuild; with "four tools" badges at the side.}}

:::saha-notu Four Tools
When you set out to hunt a bug, you have four tools at your disposal, and
each serves a different purpose. **printf** (printing a line to UART) is
fast but slows down execution and is dangerous inside an ISR. The **LED**
is a single-bit signal that barely disturbs timing at all — toggling it at
a specific point can answer the question "did execution reach here" even
under an oscilloscope. The **debugger** halts execution and lets you
inspect state, but because it freezes the flow of time, it can mask
real-time bugs. The **logic analyzer** observes from the outside without
disturbing the line at all — the most honest witness, but the most
demanding to set up. A good embedded developer knows how to choose among
these four; you will learn firsthand, in Task 10, which symptom calls for
which tool.
:::

Your toolbox is now complete; the theory ends here, and the investigation
begins.

:::gorev no=10 zorluk=3 baslik="Bug Hunt" kisa="Bug Hunt"
[Objective]
Find and fix the 4 real defects in the `lab10-bughunt` project, and write a
one-sentence root cause for each.

[Prerequisites]
Chapters 4–11 read; Tasks 1, 2, 4, and 5 completed (you are now familiar
with register access, UART, interrupts, and the TTC).

[Steps]
1. Examine the `labs/lab10-bughunt/` project — it was left behind by the
   intern who preceded you. Read the specification and the observed
   symptoms in `README.md` carefully: the project compiles and loads onto
   the board, but four aspects of its behavior do not match expectations.
2. Open the project as an application component in your own Vitis
   workspace, build it, and load it onto the board with a **Debug
   configuration** (full steps are in the README).
3. Before guessing at the four findings, run the system and observe it
   with your own eyes; for each symptom, first decide for yourself which
   tool (printf, LED, debugger, logic analyzer) is best suited to it.
4. Find and fix all four defects. Retest the system from the start after
   each fix — fixing one defect can sometimes change the symptom of
   another.
5. Write a one-sentence root cause for each defect (not *what* happened,
   but *why* it happened).

[Success Criteria]
The project fully conforms to the specification: a "tick N" line is
printed once per second via TTC0, a "button: M" line appears and DS50
toggles on every SW19 press, the counters increment correctly, and the
system runs stably for hours — and you have 4 root-cause sentences for the
4 defects.

[Self-Check]
- Which of these four defects could you not have found without a
  debugger, using UART output alone? Why?
- Which defect's visibility is affected by the difference between a
  release build (optimized, `-O2`) and a debug build (`-O0`), and which
  one does it conceal?
- Why does the fourth defect's symptom appear not immediately, but only
  after the system has been running for "a while"?

[If You Get Stuck]
::ipucu Hint 1 — Which tool for which symptom
Consider the four symptoms one at a time. The statement "the button does
not respond at all in the optimized build" should lead you directly to
question what the compiler is doing — the disassembly window comes into
play here. "The tick sometimes skips or arrives late" concerns timing —
specifically, how long the interrupts take — and can be measured with an
LED or a timestamp. "DS50 lights once and never turns off again" is a
pure logic error; looking at a single line of source is enough. "The
system crashes randomly" is a classic memory/stack suspicion — the memory
window and `lscript.ld` are your allies.
::/
::ipucu Hint 2 — Concrete leads
(1) Look at the definition of the `G_ucButtonFlag` flag: it is missing a
qualifier. (2) Look inside the button ISR: two things are present that
should not be there, and both take time. (3) Find the line that toggles
the LED: the bit operator in use says "turn on," not "toggle." (4) Find
the function that begins with an 8 KB local array, and compare it against
the stack size in `lscript.ld`.
::/
::cozum Full Solution — 4 Defects: Location, Root Cause, Fix
### 1. `G_ucButtonFlag` Is Not volatile

**Location:** `src/gpio_led_button.h` (global variable definition); used in
the main loop in `src/main.c` and in the button ISR in
`src/gpio_led_button.c`.

**Root cause:** The variable is shared between the ISR and the main loop
but is not marked `volatile`; under `-O2` optimization, the compiler
assumes the variable will not change again within the main loop and
caches its value in a register, so even though the ISR updates memory,
the main loop never observes it.

**Fix:**
```c
/* before */
unsigned char G_ucButtonFlag = 0;
/* after */
volatile unsigned char G_ucButtonFlag = 0;
```

### 2. Long-Running Work in the Button ISR (xil_printf + Delay Loop)

**Location:** `src/gpio_led_button.c`, the `buttonIsr()` function.

**Root cause:** An `xil_printf` call added inside the ISR under the
justification of "a quick status line," together with an empty delay
loop, keeps the interrupt running far longer than it should; during this
time, higher-priority TTC interrupts are delayed or missed, which causes
the tick counter to skip or arrive late.

**Fix:** The ISR should only set the flag and increment the counter; move
the printing work to the main loop — see `labs/lab10-bughunt/SOLUTION.md` for
the detailed diff.

### 3. `|=` Used Instead of Toggle for DS50

**Location:** `src/gpio_led_button.c`, the `ledDs50Toggle()` function.

**Root cause:** The line that is supposed to invert the state uses `|=`
instead of `^=`; `|= 1` pins the state to 1 on every call, meaning that
once the LED turns on, it never turns off again.

**Fix:**
```c
/* before */
G_uiDs50State |= 1;
/* after */
G_uiDs50State ^= 1;
```

### 4. An 8 KB Local Array → Stack Overflow

**Location:** `src/main.c`, the `printHealthSummary()` function; for
comparison, `_STACK_SIZE` in `src/lscript.ld`.

**Root cause:** Every time the function is called, an 8 KB
`cArrHistoryBuffer` array is allocated on the stack; the stack space
reserved in `lscript.ld` for this project is too narrow to hold it
together with the other call frames stacked on top of it. The overflow
corrupts the adjacent memory region; because what gets corrupted depends
on the stack depth at the moment of the call (whether an interrupt
happened to intervene or not), the crash does not occur immediately but
appears randomly after the system has been running for a while.

**Fix:** Reduce the buffer to the actual requirement:
```c
/* before */
char cArrHistoryBuffer[8192];
/* after */
char cArrHistoryBuffer[128];
```
For a durable fix, also review the `_STACK_SIZE` value in `lscript.ld`
against the project's actual worst-case call depth. Full explanation:
`labs/lab10-bughunt/SOLUTION.md`.
::/
:::

Having found and fixed all four defects, you now genuinely know your
toolbox — you have become someone who opens the debugger without
hesitation, does not flinch at disassembly, and knows which tool to reach
for given a particular symptom. You know the tools; now it is time for the
conventions of the craft: a good embedded developer is defined not only by
working code, but by the ability to work effectively within a team.
