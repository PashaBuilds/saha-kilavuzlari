/* ============================================================
 * lscript.ld — stack/heap boyutlandirma bolumu (lab10-bugav)
 *
 * NOT: Vitis her platform icin kendi tam lscript.ld dosyasini uretir
 * (bellek bolgeleri, .xsa'ya gore degisir); burada yalnizca STACK/HEAP
 * boyutlandirma bolumu var. Gercek projede bu dosyanin tamamini Vitis
 * Explorer'da gorursun.
 *
 * Bu labda stack boyutu bilerek kucuk tutuldu — bu, Vitis'in genel
 * varsayilani degil, bu lab'in kendi tercihidir. Gercek bir projede her
 * zaman kendi lscript.ld'ndeki _STACK_SIZE degerini kontrol et.
 * ============================================================ */

_STACK_SIZE = DEFINED(_STACK_SIZE) ? _STACK_SIZE : 0x4000;   /* 16 KB */
_HEAP_SIZE  = DEFINED(_HEAP_SIZE)  ? _HEAP_SIZE  : 0x2000;   /*  8 KB */

/* Yerel degiskenler (fonksiyon icindeki diziler dahil) burada degil,
   calisma zamaninda stack uzerinde ayrilir; bu yuzden derleme asamasinda
   fark edilmeyen bir taşma, ancak calisirken ortaya cikar. */
