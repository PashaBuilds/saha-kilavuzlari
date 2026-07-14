# lab03-button — TASK 3: Read Button (Polling)

## What it does

Reads the SW19 button (PS MIO22) via continuous polling, reflects its
state onto the DS50 LED (PS MIO23), and prints the actual press count to
UART using **counter-based debounce**.

The board's 8 user LEDs, 5 buttons, and DIP switch are on **PL pins**
(Chapter 2) — they cannot be accessed from the PS without a bitstream. For
this reason, this task also uses only the single PS button (SW19) and
single PS LED (DS50); the 8-LED chaser arrives once the PL gate opens in
Chapter 9 / Task 7.

The `button_ps` module (`button_ps.h`) matches the signatures in the
`_gorev-zinciri.md` contract exactly:

```c
int          buttonInit(void);
unsigned int buttonRead(void);
void         ledPsWrite(unsigned int uiState);
```

`src/uart_ps.h` and `src/uart_ps.c` are **exact copies from lab02-uart**
(the Task 2 solution) — per the `_gorev-zinciri.md` contract, the copy is
carried over so that each lab folder can be built independently.

## How debounce works

When a mechanical button is pressed or released, the pin does not change
as a single clean edge but rather "bounces" for a few milliseconds — the
contact points vibrate, opening and closing several times. Counting the
raw reading directly could count a single press 2-3 times.

The solution in `main.c` uses **counter-based debounce**: SW19 is read
once every 5 ms (`DEBOUNCE_SAMPLE_INTERVAL_US`); if the value read differs
from the current stable state, a counter (`uiUnstableCount`) is
incremented. Only when this counter sees the same new value for **4
consecutive rounds** (`DEBOUNCE_ESIK`, i.e. a 20 ms stability window) is
the transition accepted as "real" — the LED is updated and, if the
transition is a press, the counter is incremented. An occasional stray
bounce reading resets the counter and triggers nothing.

The 20 ms window is not arbitrary: a typical tactile button's bounce
duration ranges from a few ms to a few tens of ms; 20 ms is both long
enough to absorb the bounce and short enough to register a real press
without a noticeable delay. If you observe a longer or shorter bounce on
your own button, simply adjust `DEBOUNCE_ESIK`.

## How to build

In the Vitis Unified IDE:

1. Select the ready-made **platform** (.xsa, standalone) provided by the
   team.
2. Open a new **empty application** project and link it to this platform.
3. Copy the four files under `src/` in this folder (`button_ps.h`,
   `button_ps.c`, `uart_ps.h`, `uart_ps.c`, `main.c`) into the project's
   `src/` folder.
4. **Build** the project, then load it onto the board via JTAG and run it.

## Expected output

With the terminal connected at 115200-8N1, pressing and releasing SW19 a
few times produces:

```
--- TASK 3: Read Button (Polling) ---
Press SW19: DS50 turns on. Release: it turns off. Count is debounced.

press #1 - DS50 ON
release   - DS50 OFF
press #2 - DS50 ON
release   - DS50 OFF
```

DS50 stays on for as long as the button is held down, and turns off the
instant you release it; if you press it 10 times, the counter reads
exactly `press #10` — never 11 or 12 due to bounce.

## A note on polarity

UG1271 does not explicitly state whether SW19/DS50 is active-high or
active-low (see `content/_arastirma-ek-C.md` §C.1). This code adopts the
**active-high** convention, consistent with the rest of the document: SW19
reads 1 while pressed, and DS50 turns on when written 1. If you observe
the opposite on your board (e.g. the LED is on while the button is NOT
pressed), the single place to change is the return line of `buttonRead()`
in `button_ps.c`.
