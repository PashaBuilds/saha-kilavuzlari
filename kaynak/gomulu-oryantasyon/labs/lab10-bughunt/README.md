# lab10-bughunt — Bug Hunt (Task 10)

This project was left behind by the intern who preceded you. Before
leaving the team, this was their last piece of work: a TTC0-based
counter, the SW19 button, and UART status lines — sounds familiar,
because it is built from the same pieces as Task 4 and Task 5. The code
**compiles** and **loads** onto the board. But when you run the project,
you will see that something is going wrong in four places.

What is asked of you: act like a detective. Do not stare at the symptom
and change code blindly; first decide which weapon (printf, LED,
debugger, logic analyzer — Chapter 11) fits which symptom, then follow
the trail.

> **Find it yourself first.** This README gives you the **specification**
> and the **observed symptoms**, not the solution. You can reach the
> solution through the hint ladder of the Task 10 card in Chapter 11, or
> through `SOLUTION.md` in this folder — but do not jump there before
> struggling on your own for at least half an hour. The real learning
> happens when you find the bug yourself.

## Project structure

```
lab10-bughunt/
├── README.md            (this file)
├── SOLUTION.md              (full solution to the 4 bugs — the bottom of the hint ladder)
└── src/
    ├── main.c            main loop, GIC setup, system health summary
    ├── uart_ps.h/.c       minimal driver for PS UART0 (register level)
    ├── gpio_led_button.h/.c  DS50 LED + SW19 button, interrupt-based
    ├── timer.h/.c   TTC0 channel 0, interrupt once per second
    └── lscript.ld         stack/heap sizing section (see note below)
```

## How to build

In Vitis, open a new **application component** (platform: standalone,
processor: `psu_cortexa53_0`, empty template — do not select Hello
World, you will use your own sources). Copy all files under `src/` into
the project's source folder, and build. Compare `lscript.ld` against
your project's own linker script's relevant STACK/HEAP section — Vitis
generates a complete `lscript.ld` for you from the platform; the file
here is only a summary showing the part relevant to this lab.

## Specification (expected behavior)

- **TTC0 channel 0** prints a `tick N` line to UART once per second (N
  an increasing counter).
- Pressing **SW19** prints a `button: M` line to UART (M the total press
  count) and toggles the **DS50** LED's state.
- The counters (`tick` and `button`) always increment correctly and
  completely.
- The system runs stably, uninterrupted, for hours.

## Observed symptoms

The intern's notes read as follows (complaints you need to verify
yourself):

1. **"The button does not respond at all in the optimized build."** In
   the debug build (`-O0`) the button appears to work, but in the
   release build (`-O2`) nothing happens when SW19 is pressed.
2. **"Ticks sometimes skip or arrive late."** `tick N` lines mostly come
   in correctly, but occasionally a number is skipped or a line comes
   out later than expected — especially worsening when the button is
   pressed frequently.
3. **"DS50 lights up once and never turns off again."** On the first
   button press the LED lights up, but on subsequent presses, when it
   should turn off, it stays lit.
4. **"The system crashes randomly after a few minutes."** Sometimes
   five minutes, sometimes twenty — there seems to be no fixed trigger,
   but sooner or later the system locks up or starts printing
   nonsensical values.

## Task

Find the four different root causes behind these four symptoms, fix
them, and write a one-sentence root cause for each. The full task
description, success criteria, and self-check questions are on the
**Task 10 — Bug Hunt** card in Chapter 11.
