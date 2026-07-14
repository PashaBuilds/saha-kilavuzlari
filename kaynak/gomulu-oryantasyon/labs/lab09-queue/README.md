# lab09-queue — Task 9 solution: Producer/Consumer with a Queue

## What it does

The **producerTask** task measures the board's VCCINT power rail bus
voltage (mV) every 500 ms with `ina226ReadBusVoltageMv()`, and puts it
on the queue as an `SMeasurementPacket` packet, together with a
timestamp, via `xQueueSend`. The **consumerTask** task waits with
`xQueueReceive`, formats the packet, and prints it to UART. Since only
`consumerTask` writes to UART, lines never interleave — this "natural
serialization" is a side benefit of the architecture, and is also
highlighted in the code.

## `ina226.h` / `ina226.c` — the same module as lab06

This module walks the PS I2C0 → PCA9544A mux (U23, `0x75`) → channel 0 →
INA226 (`0x40`, VCCINT rail) path and reads the Bus Voltage register
(`0x02`, LSB 1.25 mV); `ina226Init()` first verifies the Manufacturer ID
register (`0xFE` → expected `0x5449`, ASCII "TI"). The API contract is
fixed in `content/_gorev-zinciri.md`:

```c
int ina226Init(void);
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);
```

This is the **same module** as Task 6's (`lab06-i2c`) solution — even if
Task 6 has not been written yet in your sequence, these files conform
exactly to the contract; once you complete Task 6, the two copies'
behavior will match. The source of the PCA9544A control byte (`0x04` =
enable + channel 0) is confirmed via web search in
`content/_arastirma-ek-E.md`.

## How to build

1. Platform component: OS = `freertos10_xilinx`, processor
   `psu_cortexa53_0`.
2. Application component: empty application + this folder's
   `src/main.c`, `src/ina226.h`, `src/ina226.c`.
3. Build, load via JTAG, open the UART terminal at 115200-8N1.

## Console note

Like the other FreeRTOS labs, this lab also uses `xil_printf` for
console output.

## Expected output

Timestamped mV lines stream steadily in the terminal:

```
[    1500 ms] VCCINT =  852 mV
[    2000 ms] VCCINT =  851 mV
[    2500 ms] VCCINT =  852 mV
```

Even if the producer and consumer run at different speeds (for example,
if the consumer briefly lags while writing to UART), the queue acts as a
buffer; no data is lost — if the queue genuinely fills up, the Producer
reports this explicitly with a
`[Producer] queue full, this measurement was dropped` line rather than
silently dropping data.
