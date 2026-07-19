# lab02-uart — GÖREV 2: UART "Hello World" ve printf'in Arkasındaki Şey

## Ne yapar

PS UART0 üzerinden iki aşamalı bir gösterim:

1. `xil_printf` ile tek satır — hazır, hafif printf'in kutudan çıktığı
   gibi çalıştığını gösterir (`main.c` içindeki yorumda `%f` desteğinin
   olmadığına dair nota bak).
2. Kendi `uart_ps` modülünün (register seviyesinde, `XUartPs` sürücüsü
   kullanmadan) bastığı çok satırlı karşılama afişi.

`uart_ps` modülü üç fonksiyondan oluşur (`uart_ps.h`):

```c
void uartInit(void);
void uartSendChar(char cChar);
void uartSendString(const char* cpString);
```

`uartSendChar`, UART0'ın Channel Status Register'ındaki (`SR`, offset
`0x2C`) TXFULL biti (`0x10`) temizlenene kadar bekler, sonra karakteri
FIFO register'ına (offset `0x30`) yazar. `uartSendString`, `'\n'` ile
karşılaştığında önce `'\r'` gönderir — terminal imleci böylece gerçekten
sol kenara döner.

**Not:** `uartInit()`, UART0'ın baud hızını (115200) ya da çerçeve
biçimini (8N1) yeniden yapılandırmaz. Kart açıldığında FSBL ve
standalone BSP, UART0'ı zaten bu şekilde yapılandırılmış bırakır —
`xil_printf`'in hiçbir ek ayar olmadan çalışması bunun kanıtıdır.
`uartInit()` yalnızca bu modülün kullandığı register tabanını "hazır"
ilan eder; sıfırdan gerçek bir init istersen (Control/Mode/Baud Rate
Generator register'ları), ekleyeceğin yer burasıdır.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform**u (.xsa, standalone) seç.
2. Yeni bir **boş uygulama** projesi aç ve bu platforma bağla.
3. Bu klasördeki `src/uart_ps.h`, `src/uart_ps.c` ve `src/main.c`
   dosyalarını projenin `src/` klasörüne kopyala.
4. Projeyi **build** et, sonra JTAG üzerinden karta yükle ve çalıştır
   (Run As → Launch on Hardware) — Görev 0/1'de kurduğun akışın aynısı.

## Beklenen çıktı

Terminal 115200-8N1 ile bağlıyken (Görev 0) kartı çalıştırdığında şuna
benzer bir çıktı alırsın:

```
xil_printf ready: UART0 already configured by the platform.

========================================
  Welcome to the team - ZCU111 / PS UART0
  These lines were printed by your uart_ps module.
  The TXFULL bit was checked, and data was written to the FIFO.
========================================

```

İlk satır `xil_printf`'ten gelir; afişin kalanı `uart_ps` modülünden.
