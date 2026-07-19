# lab07-axigpio — Görev 7: PL'deki Bir IP Bloğuyla Haberleş

## Ne yapar

PL (programmable logic) tarafında, ekibin sağladığı bitstream içinde
duran bir **AXI GPIO** IP bloğunun `GPIO_LED[7:0]` çıkışlarına (kartın
8 kullanıcı LED'i: DS11–DS18) `volatile` pointer ile doğrudan erişir ve
8 LED üzerinde soldan sağa yürüyen bir ışık üretir. `main.c`'nin
sonundaki yorum bloğu, aynı işi Xilinx'in hazır `XGpio` sürücüsüyle
yapmanın neye benzediğini gösterir.

## Ön koşul — donanım tarafı

Bu lab **hazır .xsa/bitstream** ile çalışır; donanım tarafı (Vivado
tasarımı, IP entegrasyonu, bitstream üretimi) ekip tarafından sağlanır.
Bu kaynak dosyaların çalışması için tasarımda şunlar geçerli olmalıdır:

- Çıkışları PL'in `GPIO_LED[7:0]` pinlerine (DS11–DS18) bağlı bir
  **AXI GPIO** IP bloğu (v2.0, PG144) vardır.
- IP tek kanal (Enable Dual Channel = 0), 8 bit genişlikte
  yapılandırılmıştır.
- IP'nin Vivado'daki instance adı bu lab'de **`axi_gpio_0`** kabul
  edilir. Kendi projende farklı bir ad görürsen (`led_gpio` ya da
  `axi_gpio_led` gibi), `main.c`'deki `XPAR_AXI_GPIO_0_BASEADDR`
  makrosunu projenin `xparameters.h`'inde bulduğun gerçek adla değiştir
  — Görev 7'nin "kendini sına" sorularından biri tam olarak bunu sorar.

## Nasıl derlenir

1. Vitis Unified IDE'de, ekipten aldığın `.xsa` dosyasından bir
   **platform component** oluştur (OS: `standalone`, işlemci:
   `psu_cortexa53_0`).
2. Bir **application component** oluştur; boş (Empty) şablonu seç, sonra
   bu klasördeki `src/main.c`'yi projenin `src/` dizinine kopyala.
3. Projeyi build et; `xparameters.h` platformdan otomatik üretilir —
   içinde bir `XPAR_AXI_GPIO_0_BASEADDR` satırı (ya da IP'nin gerçek
   instance adından türeyen eşdeğeri) bulmalısın. Yoksa 2. adımdaki
   notu uygula: doğru makro adını kendi `xparameters.h`'inden al.
4. JTAG üzerinden karta yükle, UART terminalini 115200-8N1 ile aç.

## Beklenen çıktı

8 kullanıcı LED'i (DS11–DS18) üzerinde, soldan sağa teker teker yanan,
150 ms aralıklarla ilerleyen bir yürüyen ışık deseni; aynı anda
terminale `LED pattern: 0x01`, `0x02`, `0x04` ... gibi satırlar akar.
