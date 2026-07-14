# Chapter 0 — Welcome

Welcome to the team. This document is your companion for the coming weeks.

On your desk (or soon to be on your desk) is a **ZCU111** development board:
a Zynq UltraScale+ RFSoC (Radio Frequency System-on-Chip) sits at its
core — one of the more serious devices in our field. You have covered C at
university and perhaps blinked an LED on an Arduino — a solid starting
point. But the board in front of you is not an Arduino: it contains a
quad-core application processor, two real-time cores, a substantial FPGA
fabric, and dozens of peripherals you have not yet encountered. It is
reasonable to find this intimidating at first glance. This document's task
is to convert that unfamiliarity into working competence with the board
within two weeks.

## How this document works

This is not a reference manual; it is a **journey**. Reading sections
alternate with hands-on tasks performed directly on the board: you read a
concept, then immediately apply it on the board. No reading section
accumulates theory for long without the reader's hands touching the board —
this is a deliberate design choice. Embedded software is learned through
practice.

The milestones of the journey are shown in the map below. Mark the
"Completed" checkbox on your board after finishing each task; the map fills
in as you progress. Your markers persist in this browser (stored via
localStorage, the browser's local storage), so you can close the tab and
resume the next day.

{{ilerleme-panosu}}

You will become familiar with the anatomy of task cards: each card
specifies an **objective**, the **prerequisites** that prepare you for it,
numbered **steps**, and, most importantly, an observable **success
criterion** — either met or not met, with no middle ground. If you get
stuck, a **hint ladder** at the bottom of the card is available: a gentle
pointer first, then a more concrete hint, and finally the full solution.
Use the rungs of the ladder in order; jumping straight to the solution
saves time today but costs more two weeks from now.

:::saha-notu Getting stuck is part of the process
You will get stuck at some point in this journey; this is not a setback but
part of the curriculum itself. In this profession, reading error messages,
searching for documentation that does not exist, and chasing down "why
isn't this working" takes more time than writing code. By the time you
reach Task 10, we will turn this into a systematic exercise.
:::

## Where you will stand at the end of the first two weeks

In concrete terms, by the time you complete this document you will be able
to:

- Explain the **PS/PL separation**, the **boot flow**, and the **memory
  map** of a Zynq-based system at a whiteboard level.
- Create a bare-metal (no operating system) project from scratch in Vitis,
  build it, deploy it to the board via JTAG, obtain output over UART, and
  step through execution with a debugger.
- Read a register map and program hardware using `volatile` pointers,
  applying both polling and interrupt-based approaches.
- Describe how I2C, SPI, and UART operate at the wire level, and read data
  from an actual I2C device on the board.
- Write a small FreeRTOS application using tasks, queues, and semaphores.
- Finally, design and present a small but functional system to the team as
  your **Capstone Project**.

If this list looks ambitious — it is. But every item is broken down into
small, manageable steps that lead you there. No one expects you to write a
driver on day two; what is expected of you on day two is to have completed
Task 0.

## Before you begin: setup checklist

Complete the following on day one. If you get stuck, ask a colleague —
asking for help is not a weakness on this team; it is a mark of efficiency.

1. **Install Vitis.** Confirm the version used by the team with your system
   administrator or team lead and install it (installation can take hours
   and require tens of gigabytes of space; start the download in the
   morning and check back after a break). We cover what Vitis is and its
   conceptual layout in detail in Chapter 11; for now, treat it as
   "compiler plus IDE plus board programmer" and move on.
2. **Board contents.** Unpack the ZCU111 box and remove the power adapter
   and USB cables that ship with the board; we will go through the box
   contents and the physical setup of the board step by step in Task 0. For
   now, open the box, lay out the components on your desk, and hold the
   board by its edges when removing it from the antistatic bag.
3. **Terminal program.** The most basic way to communicate with the board
   is a serial terminal. Our environment is **Windows 10**; PuTTY or Tera
   Term (both free) will serve the purpose. Install one; we will use it in
   Task 0. (Vitis also includes its own serial terminal, which you may use
   if you prefer not to install a separate program.)
4. **Drivers.** The board's USB-UART bridge creates several virtual COM
   ports on Windows. The driver (FTDI VCP) typically installs
   automatically; if Device Manager shows a device flagged with a question
   mark, refer to the hint ladder in Task 0.
5. **Accounts and access.** Verify your access to the team's git server,
   wiki, and file share on day one. We discuss our git workflow in
   Chapter 12.

:::ekip-notu No "output" is expected in the first week
On our team, a new team member's first week is dedicated to learning; this
document constitutes that week. Your team lead will ask about your progress
through the tasks in this document, not about sprint deliverables. Take
your time, but stay engaged.
:::

When you are ready, Chapter 1 begins with the big picture: what exactly is
an embedded system, and what will your role be in this domain?
