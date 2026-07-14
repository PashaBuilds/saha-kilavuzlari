# lab02-uart — GÖREV 2: UART "Merhaba Dünya" ve printf'in Arkası

## Ne yapar

PS UART0 üzerinden iki aşamalı bir gösteri:

1. `xil_printf` ile tek satır — hazır ve hafif printf'in doğrudan çalıştığını
   gösterir (bkz. `%f` desteklemediği uyarısı, `main.c` içindeki yorum).
2. Kendi yazdığın `uart_ps` modülüyle (register seviyesinde, `XUartPs`
   sürücüsü kullanılmadan) çok satırlı bir karşılama ekranı (banner)
   bastırır.

`uart_ps` modülü üç fonksiyondan oluşur (`uart_ps.h`):

```c
void uartInit(void);
void uartSendChar(char cChar);
void uartSendString(const char* cpString);
```

`uartSendChar`, UART0'ın Channel Status Register'ında (`SR`, offset
`0x2C`) TXFULL biti (`0x10`) temizlenene kadar bekler, sonra karakteri FIFO
register'ına (offset `0x30`) yazar. `uartSendString`, `'\n'` gördüğünde
önce `'\r'` gönderir — terminalin satırı gerçekten sola sarması için.

**Dürüst not:** `uartInit()` UART0'ın baud hızını (115200) ya da kare
formatını (8N1) yeniden kurmaz. Kart açılırken FSBL ve standalone BSP zaten
UART0'ı bu ayarla bırakır — `xil_printf`'in ek bir ayar yapmadan çalışması
bunun kanıtıdır. `uartInit()` sadece bu modülün kullanacağı register
tabanını "hazır" ilan eder; gerçek bir sıfırdan init (Control/Mode/Baud Rate
Generator yazmaçları) istersen ekleyeceğin yer orası.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform** (.xsa, standalone) seçilir.
2. Yeni bir **boş (empty) uygulama** projesi açılır ve bu platforma bağlanır.
3. Bu klasördeki `src/uart_ps.h`, `src/uart_ps.c` ve `src/main.c` projenin
   `src/` klasörüne kopyalanır.
4. Proje derlenir (Build) ve JTAG üzerinden karta yüklenip çalıştırılır
   (Run As → Launch on Hardware) — Görev 0/1'de kurduğun akışın aynısı.

## Beklenen çıktı

Terminal 115200-8N1 ayarıyla bağlıyken (Görev 0), kart çalıştırıldığında
şuna benzer bir çıktı akar:

```
xil_printf hazir: UART0 platform tarafindan zaten ayarli.

========================================
  Ekibe hos geldin - ZCU111 / PS UART0
  Bu satirlari senin uart_ps modulun bastı.
  TXFULL biti kontrol edildi, FIFO'ya yazildi.
========================================

```

İlk satır `xil_printf`'ten, banner'ın geri kalanı `uart_ps` modülünden gelir.
