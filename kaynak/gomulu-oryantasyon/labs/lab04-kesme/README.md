# lab04-kesme — GÖREV 4: Buton Interrupt'ı

## Ne yapar

Görev 3'ün polling ile okuduğu SW19 butonunu (PS MIO22) bir **GIC-400**
kesmesine dönüştürür. Ana döngü artık butonu hiç sormaz; DS50'yi (PS MIO23)
150 ms'de bir çevirerek "kendi asıl işiyle meşgul" bir CPU'yu simüle eder.
SW19'a her basıldığında donanım kendisi bir kesme üretir, `buttonIsr()`
çalışır, ana döngü bir sonraki turunda basış sayısını UART'a basar —
heartbeat hiç durmadan.

`src/uart_ps.h` ve `src/uart_ps.c`, **lab02-uart'tan birebir kopyadır**
(`_gorev-zinciri.md` gereği her lab bağımsız derlenir). Bu lab için ayrı
bir `buton_ps` modülü YOK — GIC/ISR kurulumu `XGpioPs`/`XScuGic`
nesnelerine doğrudan erişim gerektirdiğinden hepsi `main.c` içinde,
tek yerde tutuldu.

## Kurulum sırası (Bölüm 7'nin beşli GIC deseni)

```c
XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
XScuGic_CfgInitialize(&S_sGic, ...);
Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
    (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
Xil_ExceptionEnable();
XScuGic_Connect(&S_sGic, 48, (Xil_ExceptionHandler)buttonIsr, &S_sGpio);
XScuGic_Enable(&S_sGic, 48);
```

SW19 pini **yükselen kenar** (`XGPIOPS_IRQ_TYPE_EDGE_RISING`) tetiklemesine
ayarlanır; pin kesmesi (`XGpioPs_IntrEnablePin`) en son, GIC tamamen
kurulduktan sonra açılır — sıra önemli, aksi halde kimsenin dinlemediği bir
kesme üretme riski var.

## ISR neden bu kadar kısa?

`buttonIsr()` üç satırdır: pinin gerçekten kestiğini doğrula
(`XGpioPs_IntrGetStatusPin`), `volatile` bayrağı set et, donanımı ack'le
(`XGpioPs_IntrClearPin`). UART'a yazma, hesap yapma, gecikme YOK — Bölüm
7'nin "ISR'de printf yok" kuralının kod karşılığı budur. Bayrağı işleyen,
sayacı artıran, UART'a yazan hep ana döngüdür.

Bayrağı ana döngüde temizleme sırasına dikkat et: kod **önce sıfırlar,
sonra işler**. Tersini yapsaydık (önce işle, sonra sıfırla), ISR tam işleme
sırasında tekrar tetiklenirse o yeni basışın bayrağını iş bitince
koşulsuzca sıfırlayıp kaybederdik.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform** (.xsa, standalone) seçilir.
2. Yeni bir **boş (empty) uygulama** projesi açılır ve bu platforma bağlanır.
3. Bu klasördeki `src/` altındaki üç dosya (`uart_ps.h`, `uart_ps.c`,
   `main.c`) projenin `src/` klasörüne kopyalanır.
4. Proje derlenir (Build) ve JTAG üzerinden karta yüklenip çalıştırılır.

## Beklenen çıktı

```
--- GOREV 4: Buton Interrupt'i ---
Ana dongu DS50 ile 'mesgul': SW19'a bas, aninda tepki gorecek.

buton basildi, sayac = 1
buton basildi, sayac = 2
```

DS50, ana döngü boyunca hiç durmadan 150 ms'de bir yanıp söner (heartbeat);
SW19'a her bastığında en fazla bir heartbeat turu içinde (yani gözle
gecikmesiz) yeni bir "buton basildi" satırı görünür. Sayaç sekmeden,
kaçırmadan artar — Görev 3'ün debounce'lu polling sayacından farklı olarak
burada donanımın kendi kenar algılaması (edge detect) bir basışı bir kez
sayar.
