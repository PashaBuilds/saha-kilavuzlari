/* ============================================================
 * lscript.ld — stack/heap sizing section (lab10-bughunt)
 *
 * NOTE: Vitis generates its own complete lscript.ld for each platform
 * (the memory regions depend on the .xsa); only the STACK/HEAP sizing
 * section is shown here. In a real project you see this file in full in
 * the Vitis Explorer.
 *
 * In this lab the stack size is deliberately kept small — this is the
 * lab's own choice, not Vitis's general default. In a real project,
 * always check the _STACK_SIZE value in your own lscript.ld.
 * ============================================================ */

_STACK_SIZE = DEFINED(_STACK_SIZE) ? _STACK_SIZE : 0x4000;   /* 16 KB */
_HEAP_SIZE  = DEFINED(_HEAP_SIZE)  ? _HEAP_SIZE  : 0x2000;   /*  8 KB */

/* Local variables (including arrays declared inside functions) are not
   allocated here; they are allocated on the stack at run time. That is
   why an overflow goes unnoticed at compile time and only surfaces at
   run time. */
