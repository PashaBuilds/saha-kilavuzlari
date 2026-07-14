# lab01-led — Görev 1: LED Yak (Merhaba Donanım)

## Ne yapar

DS50 LED'ini (PS `MIO23`) 500 ms açık / 500 ms kapalı periyotla yakıp
söndürür. Kartta bitstream yüklemeden PS'ten erişilebilen tek LED bu
olduğu için ilk laboratuvarımızın kahramanı o (bkz. Bölüm 2 ve Bölüm 4 —
8 kullanıcı LED'i PL pinlerindedir, onlara Görev 7'de AXI GPIO ile
döneceğiz).

İki alternatif kaynak dosyası var, **aynı anda derlenmezler**:

- `src/main.c` — **asıl çözüm**. `XGpioPs` sürücüsüyle
  (`LookupConfig` → `CfgInitialize` → `SetDirectionPin` →
  `SetOutputEnablePin` → `WritePin`) yazılmıştır.
- `src/main_registerli.c` — Bölüm 4'teki derin-dalış: aynı işi hiçbir
  sürücü kullanmadan, doğrudan `volatile` pointer ile `DIRM_0`/`OEN_0`/
  `DATA_0` register'larına yazarak yapar. Sürücünün perde arkasını görmek
  için ayrı, boş bir uygulama projesine bu dosyayı koyup dene.

## Vitis'te nasıl derlenir

Bu doküman Vitis'in tüm ayrıntılarına Bölüm 11'de giriyor; burada sadece
bu görevi bitirmene yetecek adımlar var:

1. Ekibin sağladığı hazır **platformu** (donanım tanımı, `.xsa`) seç.
2. Yeni bir **boş (empty) uygulama** projesi aç, bu platforma bağla.
3. `src/main.c`'yi projenin `src/` klasörüne kopyala (ya da
   `main_registerli.c`'yi — ikisini birlikte kopyalama, her ikisi de
   `main()` tanımlıyor, aynı projede derlenmezler).
4. Projeyi **derle** (Build).
5. **JTAG üzerinden karta yükle ve çalıştır** (Run As → Launch on
   Hardware).

## Beklenen davranış

DS50 LED'i saniyede bir düzenli biçimde yanıp söner: 500 ms açık, 500 ms
kapalı. UART terminalini (Görev 0'daki ayarlarla) açarsan bir karşılama
satırı da görürsün — ama görevin başarı kriteri LED'in kendisidir, terminal
çıktısı isteğe bağlı bir doğrulamadır.

## Notlar / doğrulanan değerler

- `DS50_LED_PIN_MIO = 23`, `XGpioPs` API'leri, klasik `LookupConfig`
  deseni: `content/_arastirma.md` §1 ve §5'ten.
- `main_registerli.c`'deki `DIRM_0`/`OEN_0`/`DATA_0` ofsetleri (Bank 0:
  `0x204`/`0x208`/`0x040`) Xilinx/AMD embeddedsw `xgpiops_hw.h`'den bu
  oturumda doğrudan çekilip doğrulandı — ayrıntı ve formüller
  `content/_arastirma-ek-B.md`'de.
- `usleep()` (`sleep.h`, standalone BSP, A53 hedefinde `usleep_A53`'e
  yönlenir) da bu oturumda embeddedsw kaynağından doğrulandı —
  `content/_arastirma-ek-B.md`'ye bakabilirsin. Ekstra bir kütüphane ya da
  BSP ayarı gerekmez.
