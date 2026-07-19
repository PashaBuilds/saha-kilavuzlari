/* ============================================================
 * timer.h — TTC0 kanal 0, saniyede bir interrupt
 *
 * lab10-bughunt (Gorev 10 - Bug Hunt). Gorev 5'in "Timer ile
 * Heartbeat" kurulumuyla ayni kalip: TTC0 kanal 0, 1 Hz araliga
 * yapilandirilir, her interrupt'ta G_uiTickCount artar.
 * ============================================================ */
#ifndef TIMER_H
#define TIMER_H

#include "xttcps.h"
#include "xscugic.h"

/* ISR ile ana dongu arasinda paylasilan sayac — buradaki niteleyici dogrudur. */
extern volatile unsigned int G_uiTickCount;

/**
 * @brief TTC0 kanal 0'i 1 Hz icin yapilandirir, GIC'e baglar.
 *
 * @param spTtc Ilklendirilecek TTC surucu nesnesi.
 * @param spGic Interrupt'in baglanacagi GIC nesnesi.
 * @return Basarida XST_SUCCESS, aksi halde bir Xilinx hata kodu.
 */
int timerInit(XTtcPs* spTtc, XScuGic* spGic);

#endif /* TIMER_H */
