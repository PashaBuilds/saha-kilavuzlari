/* ============================================================
 * gpio_led_button.h — DS50 LED (MIO23) and SW19 button (MIO22)
 *
 * lab10-bughunt (Task 10 - Bug Hunt). Drives DS50 via PS GPIO, watches
 * SW19 via interrupt. The GIC binding is done through XPS_GPIO_INT_ID
 * (48).
 * ============================================================ */
#ifndef GPIO_LED_BUTTON_H
#define GPIO_LED_BUTTON_H

#include "xgpiops.h"
#include "xscugic.h"

#define DS50_PIN_NO   23U   /* PS MIO23 — user LED */
#define SW19_PIN_NO   22U   /* PS MIO22 — user button */

/* State shared between the ISR and the main loop.
   NOTE: the qualifiers for these lines are defined below (in the .c file). */
extern unsigned char G_ucButtonFlag;      /* set in the button ISR */
extern unsigned int  G_uiButtonCount;     /* total press counter */

/**
 * @brief Sets up GPIO and the GIC binding (DS50 output, SW19 interrupt input).
 *
 * @param spGpio The GPIO driver object to initialize.
 * @param spGic The GIC object the interrupt will be connected to.
 * @return XST_SUCCESS on success, otherwise a Xilinx error code.
 */
int  gpioLedButtonInit(XGpioPs* spGpio, XScuGic* spGic);

/**
 * @brief Inverts DS50's state.
 *
 * @param spGpio The GPIO driver object to operate on.
 */
void ledDs50Toggle(XGpioPs* spGpio);

#endif /* GPIO_LED_BUTTON_H */
