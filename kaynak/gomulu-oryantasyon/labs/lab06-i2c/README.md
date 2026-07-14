# lab06-i2c — TASK 6: Talk to a Real Chip over I2C

## What it does

We descend into a real I2C tree via PS I2C0 (MIO14-15):

```
PS I2C0  →  PCA9544A mux (U23, address 0x75), channel 0  →  INA226 (address 0x40, VCCINT)
```

`ina226Init()` configures I2C0 at 100 kHz, writes the channel-0 selection
byte to the mux, then reads the INA226's Manufacturer ID register (0xFE)
and verifies it against **0x5449** ("TI"). If the identity does not match,
`main.c` never proceeds to measurement — a mux/address/wiring problem is
caught with a clear error message BEFORE any measurement is taken.
Once verification passes, the Bus Voltage register (0x02) is read once
per second, converted to millivolts with LSB = 1.25 mV, and printed to
UART.

The `ina226.h/.c` API matches the `_gorev-zinciri.md` contract exactly:

```c
int ina226Init(void);
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);
```

`src/uart_ps.h` and `src/uart_ps.c` are an exact copy from lab02-uart.

## PCA9544A control byte

In the control register of the TI PCA9544A datasheet (SCPS146G, §8.6
Register Map, Table 8-1), bit 2 is "enable" and bits 1:0 are the channel
number:

| B2 | B1 | B0 | Command |
|---|---|---|---|
| 0 | X | X | No channel selected (default after POR) |
| 1 | 0 | 0 | **Channel 0 enabled** |
| 1 | 0 | 1 | Channel 1 enabled |
| 1 | 1 | 0 | Channel 2 enabled |
| 1 | 1 | 1 | Channel 3 enabled |

The byte that selects channel 0: **0x04** (`0b0000_0100`). See the
verification note and source at `content/_arastirma-ek-D.md` §D.4.

## Register pointer pattern

The INA226 is a multi-register device: you first write a single-byte
"pointer" to indicate which register you want, then retrieve that
register's contents with a separate read operation. `ina226RegRead()`
wraps these two steps (`XIicPs_MasterSendPolled` + `XIicPs_MasterRecvPolled`)
and assembles the incoming 2 bytes as big-endian (MSB first).

## No infinite waiting allowed

Chapter 12's defensive-programming lesson comes into play early here:
`i2cSendLimited()` / `i2cRecvLimited()` retry each I2C operation at most
**5 times** (`I2C_DENEME_SINIRI`), with a short wait between attempts
(alongside an `XIicPs_BusIsBusy` check). If all five attempts fail, the
function returns an error — the program never hangs forever, even if the
hardware never responds at all.

## How to build

In Vitis Unified IDE:

1. Select the team-provided ready-made **platform** (.xsa, standalone).
2. Open a new **empty application** project and connect it to this
   platform.
3. Copy the five files under this folder's `src/` (`uart_ps.h`,
   `uart_ps.c`, `ina226.h`, `ina226.c`, `main.c`) into the project's
   `src/` folder.
4. Build the project and load it onto the board via JTAG to run it.

## Expected output

```
--- TASK 6: Talk to a Real Chip over I2C ---
PS I2C0 -> PCA9544A(0x75) channel 0 -> INA226(0x40)

INA226 identity verified (0x5449). Measurement starting.

VCCINT = 851 mV
VCCINT = 849 mV
VCCINT = 850 mV
```

VCCINT is nominally 0.85 V; the value may drift a few mV depending on the
board's instantaneous load, but it should hover around 850 mV. A new
line arrives once per second.
