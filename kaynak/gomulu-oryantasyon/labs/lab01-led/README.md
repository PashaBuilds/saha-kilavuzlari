# lab01-led — Task 1: Turn On the LED (Hello Hardware)

## What it does

Blinks the DS50 LED (PS `MIO23`) with a 500 ms on / 500 ms off period. Since
this is the only LED accessible from the PS without loading a bitstream onto
the board, it is the centerpiece of our first lab (see Chapter 2 and Chapter
4 — the 8 user LEDs are on PL pins, and we return to them in Task 7 using AXI
GPIO).

There are two alternative source files, and **they are not compiled at the
same time**:

- `src/main.c` — the **primary solution**. Written using the `XGpioPs`
  driver (`LookupConfig` → `CfgInitialize` → `SetDirectionPin` →
  `SetOutputEnablePin` → `WritePin`).
- `src/main_registers.c` — the deep dive from Chapter 4: performs the same
  task without using any driver, by writing directly to the `DIRM_0`/`OEN_0`/
  `DATA_0` registers through a `volatile` pointer. Place this file in a
  separate, empty application project to see what happens behind the
  driver's abstraction.

## How to build in Vitis

This document covers the full details of Vitis in Chapter 11; here you will
find only the steps needed to complete this task:

1. Select the ready-made **platform** (hardware definition, `.xsa`) provided
   by the team.
2. Open a new **empty application** project and link it to this platform.
3. Copy `src/main.c` into the project's `src/` folder (or
   `main_registers.c` — do not copy both together, since both define
   `main()` and cannot be compiled in the same project).
4. **Build** the project.
5. **Load it onto the board via JTAG and run it** (Run As → Launch on
   Hardware).

## Expected behavior

The DS50 LED blinks at a steady one-second rate: 500 ms on, 500 ms off. If
you open the UART terminal (using the settings from Task 0), you will also
see a welcome line — but the task's success criterion is the LED itself; the
terminal output is an optional verification.

## Notes / verified values

- `DS50_LED_PIN_MIO = 23`, the `XGpioPs` APIs, and the classic
  `LookupConfig` pattern: from `content/_arastirma.md` §1 and §5.
- The `DIRM_0`/`OEN_0`/`DATA_0` offsets in `main_registers.c` (Bank 0:
  `0x204`/`0x208`/`0x040`) were pulled directly from the Xilinx/AMD
  embeddedsw `xgpiops_hw.h` and verified during this session — details and
  formulas are in `content/_arastirma-ek-B.md`.
- `usleep()` (`sleep.h`, standalone BSP, routed to `usleep_A53` on the A53
  target) was also verified from the embeddedsw source during this session —
  see `content/_arastirma-ek-B.md`. No additional library or BSP
  configuration is required.
