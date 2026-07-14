# Chapter 13 — Horizon Tour

Chapter 12 addressed professional culture: defensive code, Git workflow,
and asking effective questions. You are now equipped to handle the daily
work of embedded development. This journey has not, however, covered
everything — nor could it. This chapter is not a conclusion but a horizon
tour: a brief window into seven concepts you will encounter by name
throughout your career that this document has not taught you. The goal is
not to make you an expert in them; it is so that when someone raises these
terms in a meeting, your response is "I am familiar with it, though I have
not yet gone deep," rather than "I have never heard of it." One last pause
before the Capstone Project (Chapter 14).

## DMA and Scatter-Gather

Why this matters: at some point you will need to move data without
occupying the CPU, and the answer will be DMA (Direct Memory Access —
hardware that transfers data between memory regions without CPU
involvement). Chapter 6 touched on the coherency problem between the cache
and DDR; DMA is precisely the hardware behind that problem — the CPU
initiates a transfer, moves on to other work, and is notified by an
interrupt when the transfer completes. In practice, data rarely sits in a
single contiguous memory block; a network packet or an image frame may be
scattered across multiple, non-contiguous addresses. **Scatter-gather**
lets you build a chain of **descriptors** that instruct the DMA controller:
"read this much from this address, then jump to that address and continue
reading from there" — a single DMA operation can gather scattered pieces
into one destination or scatter a single source across multiple
destinations. When you are ready, consult the series' *Memory Architecture
Field Guide*; it covers how DMA interacts with the memory map in detail.

## Watchdog

Why this matters: the day your board leaves your desk for the field, at a
customer site, no one there will be able to press a reset button. A
**watchdog** is a timer that your software "feeds" (or "kicks") at regular
intervals to signal "I am still alive"; if a feed does not arrive — because
the software has locked up, entered an infinite loop, or an ISR never
returned — the hardware resets itself. The ZynqMP has its own watchdog IP;
consult the TRM (Technical Reference Manual) for address and register
details, as this document only introduces the concept. Be aware of the
pitfall as well: if the feeding logic is placed incorrectly (for example,
if a task that has genuinely hung is the one performing the feed), the
watchdog saves nothing — it merely lies. In a correct design, the feed
originates from a point that verifies the system is genuinely healthy.

## DDR, QSPI, eMMC: Distinguishing the Storage Family

Why this matters: the question "which memory is used here" will surface in
your very first hardware-selection meeting, and confusing the three can
become an expensive mistake. **DDR** (Double Data Rate RAM) is fast but
**volatile**: its contents are lost when power is removed, and it serves as
the board's working memory. **QSPI** (Quad SPI flash) is slow but
persistent; given its small capacity, it typically holds the boot image
(boot.bin, Chapter 3). **eMMC** (embedded MultiMediaCard) offers far
greater capacity than QSPI and provides block-based persistent storage —
large enough to host a Linux root filesystem — but is not as simply
accessed as QSPI; it requires a controller and a file-system layer. Think
of the three together: DDR is "your current working memory," QSPI is "the
recipe for how the board boots," and eMMC is "the storage for persistent
files." When you are ready, consult the series' *Memory Architecture Field
Guide*; there you will find a comparative view of where each of the three
sits in the address map and its speed class.

## Device Tree and the Linux-Based Zynq World

Why this matters: the world you have inhabited throughout this document has
been **bare-metal** (no operating system) and FreeRTOS; but the same Zynq
board can also lead an entirely different life — running a full **Linux**
kernel. In that world, the way you describe hardware changes: the constants
in `xparameters.h` are replaced by the **device tree** (`.dts`/`.dtb`
files); which peripheral sits at which address and uses which interrupt is
no longer determined by compile-time constants but by this tree, read by
the kernel at runtime. In the Xilinx/AMD ecosystem, the tool that combines
this Linux image, root filesystem, and device tree is **PetaLinux** — know
that it exists; it has its own configuration workflow and learning curve.
Which world you choose ("bare-metal, RTOS, or Linux") depends on
requirements: stay close to FreeRTOS if you need strict timing guarantees;
accept the added complexity of Linux if you need a network stack, a file
system, or multiple user-space processes. When you are ready, consult the
series' *Ethernet Field Guide*; networking is frequently the primary reason
a Linux-based Zynq system exists at all.

## Secure Boot and Cryptography

Why this matters: as long as your board sits on a lab bench connected to
JTAG, "anyone can load any code" is not a real concern. Once a product
ships, however, someone loading counterfeit firmware onto your device to
resell it, or to run malicious code, becomes a serious threat. **Secure
boot** is the process by which the BootROM you encountered in Chapter 3
cryptographically verifies the FSBL (and every subsequent image in the
chain) before executing it: an image is **signed** with a private key, and
that signature is checked at every boot against a public key or a **hash**
(a fixed-length fingerprint generated from a piece of data) stored in the
device's embedded key store or in **e-fuses** (permanent, irreversible bit
fuses written into the chip); if the signature does not verify, the device
refuses to boot. This is called a **chain of trust** — no layer executes
the next without first verifying it. You will not think about this at all
during the lab phase, but underestimating it once a product ships in the
field is one of the most expensive mistakes to reverse.

## JESD204 and PCIe: High-Speed Interfaces

Why this matters: the RF sampling capability of your ZCU111, briefly shown
as a "superpower" in Chapter 2, operates entirely through these
interfaces. **JESD204** (revisions B/C) is an industry-standard protocol
that carries gigabit-scale data over serial lanes between high-speed
ADC/DAC (analog-to-digital / digital-to-analog converter) chips and an
FPGA — this is the path through which the RF-ADC/RF-DAC blocks inside the
RFSoC deliver their data to the PL side. **PCIe** (PCI Express) is more
general-purpose: a high-bandwidth, packet-based interface for connecting
cards to each other or to a motherboard, and the standard way to attach
accelerator cards in server-class systems. What both have in common: they
are far more complex physical-layer designs than AXI's (Chapter 9)
straightforward valid/ready handshake — multi-channel, requiring
synchronization and **link training** (the automatic calibration of a
connection). This is beyond the scope of this document, but recognizing it
as "the next tier up from AXI" when you hear the name is enough for now.
When you are ready, consult the series' *RF Sampling Field Guide*; you will
find JESD204's actual application on the ZCU111 covered there.

## Unit Testing and CI

Why this matters: up to now, every line you have written has been run and
observed directly on real hardware — but as a team grows, manually flashing
and testing every change on a board no longer scales. A healthy embedded
codebase deliberately separates the layer that touches hardware (register
access, driver calls) from the layer that does not (protocol parsing,
state-machine logic, CLI command parsing — the kind of code you will write
in Chapter 14). The second layer can be tested with **unit test**
frameworks on an ordinary computer, without any board attached; this in
turn connects to **CI** (Continuous Integration): every commit triggers an
automated build and test run, catching defects before they reach a human.
On our team, asking "can this function be separated from the hardware" is
an early step in the design process — the answer is usually yes, and that
separation improves both testability and code readability at once.

## Just Know the Name

Do not try to memorize the concepts in this chapter — the goal is simply
that you recall what each one means when someone mentions it by name:

| Concept | One sentence: what it does |
|---|---|
| DMA | Hardware unit that transfers data between memory regions without occupying the CPU. |
| Scatter-gather | A descriptor chain that instructs a DMA controller to gather/scatter non-contiguous memory blocks in a single operation. |
| Watchdog | A timer that resets the hardware automatically if the software stops signaling "I am still alive." |
| DDR | The board's fast but volatile (cleared on power loss) working memory. |
| QSPI | Slow but persistent flash memory, typically holding the boot image (boot.bin). |
| eMMC | Block-based persistent storage far larger than QSPI; hosts the Linux root filesystem. |
| Device tree | A hardware tree that tells Linux, at runtime, which peripheral sits at which address/interrupt. |
| PetaLinux | Xilinx/AMD's tool set for building a Linux image, root filesystem, and device tree together. |
| Secure boot | A chain in which each boot step verifies the signature of the next before loading it. |
| e-fuse | Permanent, irreversible bit fuses written into a chip; can store a verification key or hash. |
| Hash | A fixed-length fingerprint generated from data, used to verify its integrity. |
| Chain of trust | A security model in which no layer executes the next without first verifying it. |
| JESD204 | A protocol carrying gigabit-scale data over serial lanes between high-speed ADC/DAC chips and an FPGA. |
| PCIe | A high-bandwidth, packet-based, general-purpose interface between cards or a card and a motherboard. |
| Link training | The automatic calibration process of a high-speed serial connection. |
| Unit test | A method for testing hardware-independent code on an ordinary computer without a board. |
| CI (Continuous Integration) | A system that runs an automated build and test on every commit, catching defects before they reach a human. |
| TRM (Technical Reference Manual) | The manufacturer's official, complete source for a chip's register and address details. |
| Root filesystem | The storage area holding the file/directory hierarchy required for Linux to run. |

You are not expected to master all seven concepts today; this chapter's
only job was to leave a hook in your mind for each one. Now it is time to
combine every skill you have gained — reading registers, configuring
interrupts, communicating over I2C, writing FreeRTOS tasks — into a single
project. The Capstone Project is next.
