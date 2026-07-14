/* ============================================================
 * timer.h — TTC0 channel 0, interrupt once per second
 *
 * lab10-bughunt (Task 10 - Bug Hunt). The same pattern as Task 5's
 * "Heartbeat with a Timer" setup: TTC0 channel 0, configured for a
 * 1 Hz interval, incrementing G_uiTickCount on every interrupt.
 * ============================================================ */
#ifndef TIMER_H
#define TIMER_H

#include "xttcps.h"
#include "xscugic.h"

/* Counter shared between the ISR and the main loop — the qualifier here is correct. */
extern volatile unsigned int G_uiTickCount;

/**
 * @brief Configures TTC0 channel 0 for 1 Hz, connects it to the GIC.
 *
 * @param spTtc The TTC driver object to initialize.
 * @param spGic The GIC object the interrupt will be connected to.
 * @return XST_SUCCESS on success, otherwise a Xilinx error code.
 */
int timerInit(XTtcPs* spTtc, XScuGic* spGic);

#endif /* TIMER_H */
