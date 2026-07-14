# Appendix B — Glossary

An alphabetical list of technical terms used throughout the document. Each
entry points to the chapter where the term is first treated in depth — the
full definition, with context, can be found there.

**ACK** — In I2C, the acknowledgment bit by which the receiver pulls the
SDA line low to signal "byte received"; its counterpart is NACK
(Chapter 8).

**AXI** — The standard hardware bus (Advanced eXtensible Interface)
between the PS and PL, and among IP blocks within the PL; operates over
read/write channels using a valid/ready handshake (Chapter 9).

**bare-metal** — An execution model with no underlying operating system,
in which the application drives the hardware directly; the environment of
this document's earliest tasks (Chapter 10).

**baud** — In UART, the number of symbols transmitted per second; both
ends must agree on the same baud rate before communicating (Chapter 8).

**bitstream** — A binary file that configures the PL (the FPGA fabric)
according to a specific hardware design; loaded by the FSBL during boot
(Chapter 3).

**boot.bin** — The boot image file read by the BootROM from the board,
bundling the FSBL and, where applicable, the bitstream and application
(Chapter 3).

**BootROM** — Immutable code embedded in the chip that executes first
after reset; it examines the boot mode pins and loads the FSBL (Chapter 3).

**bring-up** — The process of powering up a new board or subsystem for
the first time and verifying its basic functions (Chapter 1).

**BSP** — Board Support Package; a collection of driver and header files
generated for a hardware platform; underlies the application project in
Vitis (Chapter 11).

**cache** — A small, fast memory layer that bridges the speed gap between
the CPU and main memory; can be a source of coherency issues with DMA
(Chapter 6).

**context switch** — The register/state-swap operation by which the
scheduler suspends one task and begins executing another (Chapter 10).

**datasheet** — A manufacturer document defining a chip's registers,
electrical characteristics, and behavior; core reading material for
embedded software engineers (Chapter 8).

**debounce** — A software or hardware technique for filtering the
spurious, rapid transitions a mechanical button or switch produces when
pressed (Chapter 6).

**debugger** — A tool that allows a program to be stepped through,
breakpoints to be set, and register and memory state to be inspected;
operates over JTAG in Vitis (Chapter 11).

**device tree** — A description tree that tells the Linux kernel which
addresses and interrupts hardware devices occupy; can be considered the
Linux counterpart of `xparameters.h` in the bare-metal world (Chapter 13).

**DMA** — Direct Memory Access; hardware that transfers data between
memories without occupying the CPU (Chapter 6).

**driver** — A software layer that wraps a hardware unit's registers and
exposes a clean function interface to the layers above it (Chapter 1).

**edge/level triggering** — The distinction between an interrupt
triggering on a signal transition (edge — rising/falling) versus on a
signal state (level — as long as it remains high/low) (Chapter 7).

**EMIO** — Extended MIO; a means of routing signals such as GPIO out
through the PL when the PS's built-in MIO pin count is insufficient
(Chapter 9).

**FIFO** — First In First Out; a hardware buffer, used in peripherals
such as UART, that accumulates data in order and releases it in the same
order (Chapter 5).

**FPGA** — Field-Programmable Gate Array; the reconfigurable hardware
fabric on which the PL physically resides (Chapter 2).

**FSBL** — First Stage Bootloader; the initial software stage, loaded
into OCM by the BootROM, that initializes DDR and the PL (with the
bitstream, if present) and then starts the application (Chapter 3).

**GIC** — Generic Interrupt Controller; hardware that prioritizes
interrupt sources and routes them to the appropriate core (Chapter 7).

**GPIO** — General Purpose Input/Output; a general-purpose digital pin
whose direction and state are configurable in software (Chapter 4).

**heap** — A memory region allocated dynamically at run time; used
cautiously in embedded systems (Chapter 6).

**I2C** — A two-wire (SDA/SCL) synchronous serial protocol supporting
multiple devices, with addressing and an ACK/NACK mechanism (Chapter 8).

**interrupt** — A signal sent by hardware to the CPU to indicate "an
event has occurred, attend to it immediately"; the alternative to polling
(Chapter 7).

**IP** — Intellectual Property; a pre-built or custom-designed hardware
block residing in the PL that performs a specific function, such as AXI
GPIO (Chapter 9).

**ISR** — Interrupt Service Routine; a dedicated function that executes
when an interrupt occurs and should be kept short (Chapter 7).

**JTAG** — An industry-standard serial access interface used for
programming and debugging the board; on the ZCU111 it is carried over the
same USB cable (Chapter 2).

**linker script** — A script that defines where compiled code (ELF
sections such as `.text`, `.data`, and `.bss`) is placed in the memory
map (Chapter 6).

**memory-mapped I/O** — The design principle whereby peripheral registers
can be read and written as if they were ordinary memory addresses, from
the CPU's point of view (Chapter 4).

**MIO** — Multiplexed I/O; the PS's fixed set of pins that connect
directly to the outside world, each assignable to one of several
functions (Chapter 4).

**MOSI/MISO** — In SPI, the two separate lines that carry data from
master to slave (Master Out Slave In) and from slave to master (Master In
Slave Out) (Chapter 8).

**mutex** — A specialized type of semaphore, held by only one task at a
time, used to protect a shared resource (Chapter 10).

**OCM** — On-Chip Memory; small, fast memory inside the chip that does
not depend on DDR; the FSBL is loaded here (Chapter 3).

**open-drain** — An output type in which a line can only be pulled low
(to 0) and requires an external pull-up resistor to be pulled high; the
basic physical layer of I2C (Chapter 8).

**parity** — An additional bit added to a UART frame for basic error
detection, verifying whether the data bits contain an odd or even number
of 1s (Chapter 8).

**PL** — Programmable Logic; the FPGA fabric side of the Zynq, where
hardware engineers place their own IP blocks (Chapter 2).

**polling** — Continuous, loop-based querying by the CPU of a condition
(e.g., a button state or FIFO occupancy); a simple alternative to
interrupts, but one that occupies the CPU (Chapter 6).

**priority inversion** — A problem in which a high-priority task waiting
on a resource held by a low-priority task is effectively delayed by
intervening medium-priority tasks, behaving as if it had lower priority
(Chapter 10).

**PS** — Processing System; the side of the Zynq containing the fixed
cores (A53/R5) and fixed peripherals (UART, I2C, GPIO, etc.) (Chapter 2).

**pull-up** — A resistor that holds a line at a high (1) level by
default; required on open-drain lines such as I2C (Chapter 8).

**queue** — In FreeRTOS, a synchronized message box operating on FIFO
logic, used to pass data between tasks (or between an ISR and a task)
(Chapter 10).

**register / register map** — A memory cell at a specific address that
controls a peripheral's behavior or reports its status (register); the
complete listing of a peripheral's registers, together with their
offsets, fields, and access type (R/W/RO/W1C) (register map) (Chapter 4).

**RTOS** — Real-Time Operating System; a task/scheduler-based operating
system that provides timing guarantees; this document uses FreeRTOS as
its example (Chapter 10).

**scheduler** — The core RTOS component that decides which task runs and
when (Chapter 10).

**semaphore** — A synchronization object used for event signaling or
resource counting between tasks (or between an ISR and a task)
(Chapter 10).

**SoC** — System-on-Chip; a design approach in which a processor, memory
controller, and peripherals are integrated on a single chip; the Zynq
UltraScale+ is one example (Chapter 2).

**SPI** — A four-wire (SCLK/MOSI/MISO/CS), synchronous, high-speed,
master-slave serial protocol (Chapter 8).

**stack** — A memory region that holds the local variables and return
addresses of function calls, growing and shrinking according to LIFO
logic (Chapter 6).

**task** — In an RTOS, an independently schedulable unit of execution
with its own stack (Chapter 10).

**tick** — The periodic interrupt pulse by which the RTOS scheduler
measures its unit of time (Chapter 10).

**TRM** — Technical Reference Manual; the primary source document
describing a chip's memory map, register set, and architecture in detail
(Chapter 3).

**UART** — Universal Asynchronous Receiver/Transmitter; a two-wire,
asynchronous serial communication protocol requiring agreement on baud
rate (Chapter 8).

**volatile** — A C qualifier that tells the compiler "do not optimize
this variable; genuinely read/write it on every access"; mandatory for
register access (Chapter 5).

**W1C** — Write-1-to-Clear; an access type in which writing 1 to a
register field clears that bit (sets it to 0), while writing 0 has no
effect (Chapter 4).

**watchdog** — A guard timer that automatically resets the system if
software fails to send periodic "feed" signals (Chapter 13).

**XSA** — Xilinx Support Archive; a file exported from Vivado carrying
the PS/PL hardware definition (with or without a bitstream); serves as
the input to a Vitis platform project (Chapter 11).

**xparameters.h** — A header file automatically generated for a Vitis
platform, defining all peripheral base addresses and device IDs as
constants (Chapter 4).
