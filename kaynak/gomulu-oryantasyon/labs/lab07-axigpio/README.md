# lab07-axigpio — Task 7 solution: Talk to an IP Block in the PL

## What it does

On the PL (programmable logic) side, we directly access the
`GPIO_LED[7:0]` outputs (the board's 8 user LEDs: DS11–DS18) of an **AXI
GPIO** IP block sitting in a team-provided bitstream, using a `volatile`
pointer, and produce a light that walks left to right across the 8 LEDs.
The comment block at the end of `main.c` shows what doing the same job
with Xilinx's ready-made `XGpio` driver would look like.

## Prerequisite — hardware side

This lab works with a **ready-made .xsa/bitstream**; the hardware side
(Vivado design, IP integration, bitstream generation) is provided by the
team. For these source files to work, the following must hold true in
the design:

- An **AXI GPIO** IP block (v2.0, PG144) exists, with its outputs
  connected to the PL's `GPIO_LED[7:0]` pins (DS11–DS18).
- The IP is configured as a single channel (Enable Dual Channel = 0),
  8 bits wide.
- The IP's instance name in Vivado is assumed in this lab to be
  **`axi_gpio_0`**. If you see a different name in your own project
  (such as `led_gpio` or `axi_gpio_led`), replace the
  `XPAR_AXI_GPIO_0_BASEADDR` macro in `main.c` with the actual name you
  find in your project's `xparameters.h` — this is exactly the subject
  of one of Task 7's "self-check" questions.

## How to build

1. In Vitis Unified IDE, create a **platform component** from the `.xsa`
   file you received from the team (OS: `standalone`, processor:
   `psu_cortexa53_0`).
2. Create an **application component**; select the empty (Empty)
   template, then copy this folder's `src/main.c` into the project's
   `src/` directory.
3. Build the project; `xparameters.h` is auto-generated from the
   platform — you should find a `XPAR_AXI_GPIO_0_BASEADDR` line in it
   (or the equivalent derived from the IP's actual instance name). If
   not, apply the note from Step 2: take the correct macro name from
   your own `xparameters.h`.
4. Load onto the board via JTAG, open the UART terminal at 115200-8N1.

## Expected output

A walking-light pattern across the 8 user LEDs (DS11–DS18), lighting one
at a time from left to right, advancing at 150 ms intervals; at the same
time, lines such as `LED pattern: 0x01`, `0x02`, `0x04` ... stream in
the terminal.
