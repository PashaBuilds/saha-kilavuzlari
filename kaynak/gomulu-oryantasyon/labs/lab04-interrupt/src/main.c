/* ============================================================================
 * main.c — TASK 4 solution: Button Interrupt
 *
 * Converts SW19 (PS MIO22), which Task 3 read via polling, into a GPIO
 * interrupt connected through the GIC. The main loop runs DS50 (PS MIO23)
 * like a heartbeat, simulating a CPU "busy with its own real work"; the
 * button press is noticed without delay and without ever interrupting
 * that work.
 *
 * The setup order is an exact application of the five-step GIC pattern
 * from Chapter 7:
 *   LookupConfig -> CfgInitialize -> Xil_ExceptionRegisterHandler ->
 *   Connect -> Enable.
 *
 * ISR RULE (Chapter 7): keep it short. buttonIsr() ONLY verifies that
 * this pin actually fired, sets the volatile flag, and acknowledges the
 * hardware. No writing to UART, no computation, no delay — all of that
 * is the main loop's job.
 * ============================================================================ */

#include "xparameters.h"
#include "xgpiops.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"

#define KESME_PS_PIN_SW19       22U   /* SW19 button -> PS MIO22 (input) */
#define KESME_PS_PIN_DS50       23U   /* DS50 LED    -> PS MIO23 (output, heartbeat) */
#define KESME_GIC_ID_GPIO       48U   /* GIC interrupt ID: PS GPIO (Chapter 7) */

/* The heartbeat interval simulating the main loop's "busy" real work.
 * It is kept short so that, after pressing the button, DS50 does not
 * appear frozen, while still making it clear that the CPU is inside this
 * wait. */
#define HEARTBEAT_INTERRUPT_INTERVAL_US   150000U   /* 150 ms */

static XGpioPs S_sGpio;
static XScuGic S_sGic;

/* The ONE variable through which the ISR talks to the main loop. volatile
 * is MANDATORY: the compiler must know this variable can be changed by
 * the ISR at an "unexpected moment", otherwise it may cache the read in
 * the main loop and never refresh it (the lesson of Chapter 5 + Chapter
 * 7). */
static volatile unsigned char G_ucButtonFlag = 0U;

/* --- small helper: unsigned int -> decimal text, no ready-made printf needed --- */
static void printNumber(unsigned int uiValue)
{
    char cArrBuffer[11];
    int iIndex = 10;

    cArrBuffer[10] = '\0';

    if (uiValue == 0U)
    {
        uartSendChar('0');
        return;
    }

    while ((uiValue > 0U) && (iIndex > 0))
    {
        iIndex--;
        cArrBuffer[iIndex] = (char)('0' + (uiValue % 10U));
        uiValue /= 10U;
    }

    uartSendString(&cArrBuffer[iIndex]);
}

/* --- ISR: SHORT. Only the flag + ack. --- */
static void buttonIsr(void* pvCallBackRef)
{
    XGpioPs* spGpio = (XGpioPs*)pvCallBackRef;

    if (XGpioPs_IntrGetStatusPin(spGpio, KESME_PS_PIN_SW19) != 0U)
    {
        G_ucButtonFlag = 1U;
        XGpioPs_IntrClearPin(spGpio, KESME_PS_PIN_SW19);
    }
    /* Do NOT add UART writes, computation, or delays here — Chapter 7's
     * "no printf in the ISR" rule applies the moment you are tempted to
     * add anything below this line. */
}

/* --- Sets up the GIC and connects buttonIsr to interrupt ID 48 --- */
static int setupInterruptSystem(void)
{
    int iStatus;
    XScuGic_Config* spGicConfig;

    spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    if (spGicConfig == NULL)
    {
        return XST_FAILURE;
    }

    iStatus = XScuGic_CfgInitialize(&S_sGic, spGicConfig,
                                     spGicConfig->CpuBaseAddress);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    /* Connect the CPU's IRQ exception to the GIC's general handler —
     * this single line is done once per interrupt source. */
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
        (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
    Xil_ExceptionEnable();

    /* Connect buttonIsr to the GPIO's interrupt ID, then enable that source. */
    iStatus = XScuGic_Connect(&S_sGic, KESME_GIC_ID_GPIO,
        (Xil_ExceptionHandler)buttonIsr, (void*)&S_sGpio);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    XScuGic_Enable(&S_sGic, KESME_GIC_ID_GPIO);

    return XST_SUCCESS;
}

int main(void)
{
    XGpioPs_Config* spGpioConfig;
    unsigned int uiPressCount;
    unsigned int uiLedState;

    uartInit();

    /* --- PS GPIO: SW19 input, DS50 output (same pattern as Task 1/3) --- */
    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        uartSendString("ERROR: XGpioPs_LookupConfig failed.\n");
        while (1) { ; }
    }

    if (XGpioPs_CfgInitialize(&S_sGpio, spGpioConfig,
                               spGpioConfig->BaseAddr) != XST_SUCCESS)
    {
        uartSendString("ERROR: XGpioPs_CfgInitialize failed.\n");
        while (1) { ; }
    }

    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_SW19, 0U);
    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, KESME_PS_PIN_DS50, 1U);

    /* --- Interrupt type for SW19: rising edge (Chapter 7) --- */
    XGpioPs_SetIntrTypePin(&S_sGpio, KESME_PS_PIN_SW19,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);

    if (setupInterruptSystem() != XST_SUCCESS)
    {
        uartSendString("ERROR: setupInterruptSystem failed.\n");
        while (1) { ; }
    }

    /* We enable the pin-level interrupt last — enabling the pin before
     * the GIC is ready could generate an interrupt that nobody is yet
     * listening for. */
    XGpioPs_IntrEnablePin(&S_sGpio, KESME_PS_PIN_SW19);

    uartSendString("\n--- TASK 4: Button Interrupt ---\n");
    uartSendString("Main loop 'busy' with DS50: press SW19, you'll see an instant reaction.\n\n");

    uiPressCount = 0U;
    uiLedState = 0U;

    while (1)
    {
        /* The main loop's "real work" is simulated here: the DS50
         * heartbeat. In a real system this could be any work — sensor
         * reading, telemetry computation, display updates; what matters
         * is that the CPU can continue its own work WITHOUT polling the
         * button. */
        usleep(HEARTBEAT_INTERRUPT_INTERVAL_US);
        uiLedState ^= 1U;
        XGpioPs_WritePin(&S_sGpio, KESME_PS_PIN_DS50, uiLedState);

        if (G_ucButtonFlag != 0U)
        {
            /* Clear FIRST, process SECOND: if the ISR fires again right
             * between these lines, the new press is not lost — it is
             * caught on the next round. If we reversed the order
             * (process first, then clear), and the ISR fired again while
             * we were processing, we would unconditionally clear that
             * new press's flag once we were done and LOSE it — this is
             * the answer to Chapter 7's "Self-Check" question. */
            G_ucButtonFlag = 0U;

            uiPressCount++;
            uartSendString("button pressed, count = ");
            printNumber(uiPressCount);
            uartSendString("\n");
        }
    }

    return 0;
}
