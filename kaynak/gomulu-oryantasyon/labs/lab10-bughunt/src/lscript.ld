/* ============================================================
 * lscript.ld — stack/heap boyutlandirma bolumu (lab10-bughunt)
 *
 * NOT: Vitis her platform icin kendi eksiksiz lscript.ld'sini uretir
 * (bellek bolgeleri .xsa'ya baglidir); burada yalnizca STACK/HEAP
 * boyutlandirma bolumu gosterilir. Gercek projede bu dosyanin tamamini
 * Vitis Explorer'da gorursun.
 *
 * Bu lab'de stack boyutu bilerek kucuk tutulmustur — bu lab'in kendi
 * tercihi, Vitis'in genel varsayilani degil. Gercek projede her zaman
 * kendi lscript.ld'ndeki _STACK_SIZE degerini kontrol et.
 * ============================================================ */

_STACK_SIZE = DEFINED(_STACK_SIZE) ? _STACK_SIZE : 0x4000;   /* 16 KB */
_HEAP_SIZE  = DEFINED(_HEAP_SIZE)  ? _HEAP_SIZE  : 0x2000;   /*  8 KB */

/* Yerel degiskenler (fonksiyon icinde bildirilen diziler dahil) burada
   ayrilmaz; calisma zamaninda stack'te ayrilirlar. Bir tasmanin derleme
   zamaninda fark edilmeyip ancak calisma zamaninda ortaya cikmasinin
   sebebi budur. */
