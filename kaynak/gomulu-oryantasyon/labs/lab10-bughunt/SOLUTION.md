# SOLUTION.md — lab10-bughunt (Task 10) full solution

This file is the bottom rung of the hint ladder. Before arriving here,
make sure you have tried the specification and symptoms in `README.md`
on your own for at least one pass.

Below, all four bugs follow the same order: **location**, **symptom**,
**root cause** (one sentence), **fix**.

---

## Bug 1 — `G_ucButtonFlag` is not volatile

**Location:** `src/gpio_led_button.h`, the global variable declaration
(`extern unsigned char G_ucButtonFlag;`); its definition at the top of
`src/gpio_led_button.c`. It is read in `src/main.c`'s main loop and
written in `buttonIsr()`.

**Symptom:** In the debug build (`-O0`) the button appears to work; but
in the release build (`-O2`), pressing SW19 does nothing.

**Root cause:** The variable is shared between an ISR and the main
loop but is not marked `volatile`; under `-O2` optimization, the
compiler assumes this variable cannot change in memory within the main
loop, caches its value in a register, and never re-reads memory for the
rest of the loop — even though the ISR updates memory, the main loop
never sees it.

**Fix:**

```c
/* src/gpio_led_button.h — before */
extern unsigned char  G_ucButtonFlag;

/* src/gpio_led_button.h — after */
extern volatile unsigned char  G_ucButtonFlag;
```

```c
/* src/gpio_led_button.c — before */
unsigned char  G_ucButtonFlag = 0;

/* src/gpio_led_button.c — after */
volatile unsigned char  G_ucButtonFlag = 0;
```

The declaration (header) and the definition (source file) must carry
the same qualifier; don't forget to change both.

---

## Bug 2 — long work in the button ISR (xil_printf/uart + a delay loop)

**Location:** `src/gpio_led_button.c`, the `buttonIsr()` function — the
`uartSendString("button interrupt received\r\n");` line and the `for`
delay loop immediately below it.

**Symptom:** `tick N` lines mostly arrive correctly, but occasionally a
number is skipped or a line comes out later than expected — this gets
worse especially when the button is pressed frequently.

**Root cause:** The UART write and busy-wait delay loop, added to the
ISR under the justification of "useful for seeing that the interrupt
arrived," keep the interrupt on the CPU for far longer than it should
be; during this time, TTC0 interrupts pending behind it are delayed or,
if they arrive back-to-back, missed — this is what causes the tick
counter to skip or lag.

**Fix:** Have the ISR update state only (flag + counter); move the
UART write and any debounce/delay logic to the main loop:

```c
/* src/gpio_led_button.c — before */
static void buttonIsr(void *pvCallBackRef)
{
    XGpioPs *spGpio = (XGpioPs *)pvCallBackRef;
    unsigned int uiDelayCount;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;

        uartSendString("button interrupt received\r\n");
        for (uiDelayCount = 0; uiDelayCount < 200000U; uiDelayCount++)
        {
            /* empty body: a brief settling delay */
        }
    }
}

/* src/gpio_led_button.c — after */
static void buttonIsr(void *pvCallBackRef)
{
    XGpioPs *spGpio = (XGpioPs *)pvCallBackRef;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;
    }
}
```

If debouncing is genuinely needed (if mechanical bounce is a real
problem), do it in the main loop, comparing against the tick counter or
a timestamp — never set up a delay loop inside an ISR.

---

## Bug 3 — DS50 toggle uses `|=`

**Location:** `src/gpio_led_button.c`, the `ledDs50Toggle()` function.

**Symptom:** On the first button press DS50 lights up, but on
subsequent presses, when it should turn off, it stays lit.

**Root cause:** The line meant to invert (toggle) the state uses `|=`
instead of `^=`; bitwise ORing in a 1 pins the state to 1 on every
call, meaning once the LED lights up it can never return to 0.

**Fix:**

```c
/* src/gpio_led_button.c — before */
void ledDs50Toggle(XGpioPs *spGpio)
{
    /* invert the state */
    G_uiDs50State |= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}

/* src/gpio_led_button.c — after */
void ledDs50Toggle(XGpioPs *spGpio)
{
    /* invert the state */
    G_uiDs50State ^= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}
```

The lesson this bug teaches: the comment ("invert the state") states
the intent correctly, but the code does not carry it out — trust the
code, not the comments.

---

## Bug 4 — an 8 KB local array causes stack overflow

**Location:** `src/main.c`, the `printHealthSummary()` function — the
`char cArrHistoryBuffer[8192];` line. Compare against `_STACK_SIZE` in
`src/lscript.ld` (0x4000 = 16 KB in this lab).

**Symptom:** The system runs fine for minutes (sometimes hours), then
crashes randomly or starts printing nonsensical values; there appears
to be no clear trigger.

**Root cause:** Every time `printHealthSummary()` is called (once every
10 ticks), it allocates the 8 KB `cArrHistoryBuffer` array on the
stack; the 16 KB of stack space allotted for this project can be
overrun by this allocation together with the other call frames stacked
on top of it (and the stack usage of any interrupt that happens to fire
at that moment). The overflow corrupts adjacent memory; since which data
gets corrupted depends on the stack depth at the moment of the call, the
crash does not appear immediately but rather randomly, after the system
has been running for a while.

**Fix:** Shrink the buffer to what is actually needed (a few dozen
bytes are enough for a tick/button count message):

```c
/* src/main.c — before */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    char cArrHistoryBuffer[8192];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "summary: tick=%lu button=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}

/* src/main.c — after */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    char cArrHistoryBuffer[128];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "summary: tick=%lu button=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}
```

As a standing discipline: large local arrays should always be
considered suspect in embedded systems. If a genuinely large buffer is
required, consider making it `static` to move it from the stack to
`.bss`, or deliberately growing `_STACK_SIZE` in `lscript.ld` — but
either way, do it on purpose, not by accident.

---

## Summary table

| # | File / function | Root cause (one sentence) |
|---|---|---|
| 1 | `gpio_led_button.h/.c` — `G_ucButtonFlag` | Missing `volatile` means the compiler stops re-reading the flag's memory under `-O2`. |
| 2 | `gpio_led_button.c` — `buttonIsr()` | The UART write and delay loop inside the ISR lengthen it, delaying/missing TTC0 interrupts. |
| 3 | `gpio_led_button.c` — `ledDs50Toggle()` | Using `|=` instead of `^=` pins the LED state to 1 permanently. |
| 4 | `main.c` — `printHealthSummary()` | An 8 KB local array overflows the project's tight stack space and corrupts adjacent memory. |
