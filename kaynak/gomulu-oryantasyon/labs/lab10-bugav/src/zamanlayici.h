/* ============================================================
 * zamanlayici.h — TTC0 kanal 0 ile saniyede bir kesme
 *
 * lab10-bugav (Gorev 10 - Bug Avi). Gorev 5'teki "Timer ile Kalp Atisi"
 * duzeninin ayni deseni: TTC0 kanal 0, 1 Hz araligina kurulu, her
 * kesmede G_uiTickCount'u bir artirir.
 * ============================================================ */
#ifndef ZAMANLAYICI_H
#define ZAMANLAYICI_H

#include "xttcps.h"
#include "xscugic.h"

/* ISR ile ana dongu arasinda paylasilan sayac — burada nitelik dogru. */
extern volatile unsigned int G_uiTickCount;

/**
 * @brief TTC0 kanal 0'i 1 Hz'e kurar, GIC'e baglar.
 *
 * @param spTtc Baslatilacak TTC surucu nesnesi.
 * @param spGic Kesmenin baglanacagi GIC nesnesi.
 * @return XST_SUCCESS basarili ise, aksi halde Xilinx hata kodu.
 */
int timerInit(XTtcPs* spTtc, XScuGic* spGic);

#endif /* ZAMANLAYICI_H */
