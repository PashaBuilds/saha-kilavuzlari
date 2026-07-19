# lab04-interrupt — Görev 4: Buton Interrupt'ı

## Ne yapar

Görev 3'ün polling ile okuduğu SW19 butonunu (PS MIO22) bir **GIC-400**
interrupt'ına (kesme) çevirir. Ana döngü butonu artık hiç sorgulamaz;
"kendi gerçek işiyle meşgul" bir CPU'yu taklit etmek için DS50'yi
(PS MIO23) her 150 ms'de bir toggle'lar. SW19'a her basıldığında
interrupt'ı donanımın kendisi üretir, `buttonIsr()` koşar ve ana döngü
bir sonraki turunda basma sayısını UART'a basar — heartbeat hiç durmaz.

`src/uart_ps.h` ve `src/uart_ps.c`, **lab02-uart'tan birebir kopyadır**
(`_gorev-zinciri.md` gereği her lab bağımsız derlenir). Bu lab'de ayrı
bir `button_ps` modülü YOKTUR — GIC/ISR kurulumu `XGpioPs`/`XScuGic`
nesnelerine doğrudan erişim gerektirdiğinden her şey tek yerde,
`main.c` içinde tutulur.

## Kurulum sırası (Bölüm 7'nin beş adımlı GIC kalıbı)

```c
XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
XScuGic_CfgInitialize(&S_sGic, ...);
Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
    (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
Xil_ExceptionEnable();
XScuGic_Connect(&S_sGic, 48, (Xil_ExceptionHandler)buttonIsr, &S_sGpio);
XScuGic_Enable(&S_sGic, 48);
```

SW19 pini **yükselen kenarda** tetiklenecek şekilde yapılandırılır
(`XGPIOPS_IRQ_TYPE_EDGE_RISING`); pin seviyesindeki interrupt
(`XGpioPs_IntrEnablePin`) en son, GIC tamamen kurulduktan sonra
etkinleştirilir — burada sıra önemlidir, aksi halde henüz kimsenin
dinlemediği bir interrupt üretme riski doğar.

## ISR neden bu kadar kısa?

`buttonIsr()` üç satırdır: pinin gerçekten tetiklendiğini doğrula
(`XGpioPs_IntrGetStatusPin`), `volatile` bayrağı kur ve donanıma alındı
bilgisi ver (`XGpioPs_IntrClearPin`). UART'a yazma YOK, hesap yok,
gecikme yok — bu, Bölüm 7'nin "ISR'de printf yok" kuralının kod
düzeyindeki karşılığıdır. Bayrağı işleyen, sayacı artıran ve UART'a
yazan her zaman ana döngüdür.

Ana döngüde bayrağın temizlenme sırasına dikkat et: kod **önce
temizler, sonra işler**. Tersini yapsaydık (önce işle, sonra temizle)
ve işleme sırasında ISR yeniden tetiklenseydi, iş bitince o yeni
basışın bayrağını koşulsuz temizler ve basışı kaybederdik.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform**u (.xsa, standalone) seç.
2. Yeni bir **boş uygulama** projesi aç ve bu platforma bağla.
3. Bu klasördeki `src/` altındaki üç dosyayı (`uart_ps.h`, `uart_ps.c`,
   `main.c`) projenin `src/` klasörüne kopyala.
4. Projeyi **build** et, sonra JTAG üzerinden karta yükle ve çalıştır.

## Beklenen çıktı

```
--- TASK 4: Button Interrupt ---
Main loop 'busy' with DS50: press SW19, you'll see an instant reaction.

button pressed, count = 1
button pressed, count = 2
```

DS50, ana döngü boyunca her 150 ms'de bir kesintisiz yanıp söner
(heartbeat); SW19'a her bastığında en geç bir heartbeat turu içinde
(yani algılanabilir gecikme olmadan) yeni bir "button pressed" satırı
belirir. Sayaç atlamadan, basış kaçırmadan artar — Görev 3'ün debounce
edilmiş polling sayacından farklı olarak, burada donanımın kendi kenar
algılaması her basışı tam bir kez sayar.
