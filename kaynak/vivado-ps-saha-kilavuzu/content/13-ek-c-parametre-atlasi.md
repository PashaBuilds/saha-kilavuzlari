# Ek C — Parametre Atlası

Kılavuzun referans çekirdeği: yazılıma parametre olarak çıkan her ayarın tek
tablosu. "Hızlıca şu ayara bakacağım" senaryosunun tek durağı. Değerler
demo projelerin gerçek raporlarından (`assets/reports/`) alınmıştır; kendi
projende sayılar değişir, satır yapısı aynı kalır.

Satır yapısı: **parametre → hangi ekran → ne anlama gelir → yazılım karşılığı
→ bölüm**.

## MPSoC / UltraScale+ (Demo 1)

| Parametre | Ekran | Anlamı | Yazılım karşılığı | Bölüm |
|---|---|---|---|---|
| UART0 pin | [Ekran 10](#ekran-10) | Konsolun fiziksel MIO pini (MIO 18..19) | `XPAR_XUARTPS_0_BASEADDR`, `console=ttyPS0` | [5](#05-ps-ayarlari-1) |
| UART ref clock | [Ekran 12](#ekran-12) | Baud bölücüsünün girişi (Actual 99.99 MHz) | `XPAR_XUARTPS_0_UART_CLK_FREQ_HZ=99990005` | [5](#05-ps-ayarlari-1) |
| PSS_REF_CLK | [Ekran 11](#ekran-11) | Kart kristali, PLL kökü (33.330 MHz) | Tüm türetilmiş frekansların temeli | [5](#05-ps-ayarlari-1) |
| PL fabric clock | [Ekran 13](#ekran-13) | PL IP'lerinin saati (pl_clk0, ~100 MHz) | `XPAR_AXI_TIMER_0_CLOCK_FREQ_HZ` | [5](#05-ps-ayarlari-1) |
| DDR tip/hız | [Ekran 14](#ekran-14) | DDR4-2133P, 64bit, 4GB, ECC off | linker `memory`, `XPAR_PSU_DDR_0_*` | [5](#05-ps-ayarlari-1) |
| HPM0 master | [Ekran 15](#ekran-15) | PS→PL register erişim kapısı (açık) | PL IP `BASEADDR`'ları bu kapıdan | [6](#06-ps-ayarlari-2) |
| PL→PS IRQ0 | [Ekran 16](#ekran-16) | PL interrupt grubu (açık, 1 bit grubu) | `XScuGic_Connect(..., 121..)` | [6](#06-ps-ayarlari-2) |
| GPIO adresi | [Ekran 17](#ekran-17) | 0xA0000000, 64K | `XPAR_AXI_GPIO_LED_BASEADDR` | [7](#07-adres-haritasi) |
| Timer adresi | [Ekran 17](#ekran-17) | 0xA0010000, 64K | `XPAR_AXI_TIMER_0_BASEADDR` | [7](#07-adres-haritasi) |
| Uartlite adresi | [Ekran 17](#ekran-17) | 0xA0020000, 64K | `XPAR_AXI_UARTLITE_DBG_BASEADDR` | [7](#07-adres-haritasi) |
| BRAM adresi | [Ekran 17](#ekran-17) | 0xA0030000, 8K | `XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR` | [7](#07-adres-haritasi) |
| Timer IRQ ID | (concat sırası) | concat In0 → GIC ID 121 | `XPAR_FABRIC_AXI_TIMER_0_INTERRUPT_INTR` | [6](#06-ps-ayarlari-2) |
| Uartlite IRQ ID | (concat sırası) | concat In1 → GIC ID 122 | `XPAR_FABRIC_AXI_UARTLITE_DBG_*` | [6](#06-ps-ayarlari-2) |
| GPIO IRQ ID | (concat sırası) | concat In2 → GIC ID 123 | `XPAR_FABRIC_AXI_GPIO_LED_IP2INTC_*` | [6](#06-ps-ayarlari-2) |

## Versal (Demo 2)

| Parametre | Ekran | Anlamı | Yazılım karşılığı | Bölüm |
|---|---|---|---|---|
| UART0 pin | [Ekran 23](#ekran-23) | Konsol PMC_MIO 42..43 | `XPAR_XUARTPSV_0_*`, device tree | [8](#08-versal) |
| PL clock | [Ekran 24](#ekran-24) | pl0_ref_clk 333.333 MHz | `XPAR_AXI_TIMER_0_CLOCK_FREQ_HZ=333333008` | [8](#08-versal) |
| DDR yeri | [Ekran 26](#ekran-26) | DDR4-1600, NoC/DDRMC arkasında | linker `memory` (iki bölge) | [8](#08-versal) |
| DDR adres bölgeleri | [Ekran 27](#ekran-27) | LOW0 0x0 (2G) + LOW1 0x8_0000_0000 | device tree `memory` iki düğüm | [8](#08-versal) |
| GPIO adresi (doğrudan) | [Ekran 27](#ekran-27) | 0xA4000000, M_AXI_FPD üzerinden | `XPAR_AXI_GPIO_LED_BASEADDR` | [8](#08-versal) |
| Timer adresi (NoC) | [Ekran 27](#ekran-27) | 0x201_0000_0000, NoC arkasında | `uintptr_t` adres (32-bit üstü!) | [8](#08-versal) |
| NoC NMU/NSU | [Ekran 25](#ekran-25) | 6 slave girişi, 1 master çıkışı, 1 MC | Görünmez; "yol var mı" cevabı | [8](#08-versal) |
| CIPS→NoC kapıları | [Ekran 28](#ekran-28) | FPD_CCI_NOC_0..3, LPD, PMC | Yüksek bant trafiğinin yolu | [8](#08-versal) |

:::yazilima-yansimasi
Bu atlasın kullanım biçimi: bir XPAR tanımının nereden geldiğini merak
ettiğinde tabloda ara, "Ekran" sütunundan gerçek Vivado ekranına git, değeri
kendi projende teyit et. Ters yön de geçerli: bir ekranda ayar gördüğünde
"Yazılım karşılığı" sütunu sana kod tarafındaki adı verir. Tablo, iki
dünya arasındaki sözlüktür.
:::

## Kapsam notu

Tablodaki her satır gerçek bir Vivado ekranına ya da rapora dayanır. Versal
CIPS UART0 (Ekran 23) ve PL clock (Ekran 24) ekranları da yakalandı ve
`assets/reports/versal-ps-pmc-config.txt` raporuyla çapraz doğrulandı
(UART0 = PMC_MIO 42..43, pl0_ref_clk = 333.333 MHz).
