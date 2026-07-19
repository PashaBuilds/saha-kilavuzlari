# lab01-led — Görev 1: LED'i Yak (Merhaba Donanım)

## Ne yapar

DS50 LED'ini (PS `MIO23`) 500 ms yanık / 500 ms sönük periyotla yakıp
söndürür. Karta bitstream yüklemeden PS'ten erişilebilen tek LED bu
olduğundan ilk laboratuvarın merkezindedir (bkz. Bölüm 2 ve Bölüm 4 —
8 kullanıcı LED'i PL pinlerindedir; onlara Görev 7'de AXI GPIO ile
döneceğiz).

İki alternatif kaynak dosya vardır ve **aynı anda derlenmezler**:

- `src/main.c` — **birincil çözüm**. `XGpioPs` sürücüsüyle yazılmıştır
  (`LookupConfig` → `CfgInitialize` → `SetDirectionPin` →
  `SetOutputEnablePin` → `WritePin`).
- `src/main_registers.c` — Bölüm 4'teki derin dalış: aynı işi hiçbir
  sürücü kullanmadan, `volatile` pointer üzerinden doğrudan
  `DIRM_0`/`OEN_0`/`DATA_0` register'larına yazarak yapar. Sürücünün
  soyutlamasının arkasında ne döndüğünü görmek için bu dosyayı ayrı,
  boş bir uygulama projesine koy.

## Vitis'te nasıl derlenir

Vitis'in tüm ayrıntısı bu dokümanın Bölüm 11'inde; burada yalnızca bu
görevi tamamlamak için gereken adımlar var:

1. Ekibin sağladığı hazır **platform**u (donanım tanımı, `.xsa`) seç.
2. Yeni bir **boş uygulama** projesi aç ve bu platforma bağla.
3. `src/main.c`'yi projenin `src/` klasörüne kopyala (ya da
   `main_registers.c` — ikisini birlikte kopyalama; ikisi de `main()`
   tanımlar ve aynı projede derlenemezler).
4. Projeyi **build** et.
5. **JTAG üzerinden karta yükle ve çalıştır** (Run As → Launch on
   Hardware).

## Beklenen davranış

DS50 LED'i düzenli bir saniyelik tempoda yanıp söner: 500 ms yanık,
500 ms sönük. UART terminalini açarsan (Görev 0'daki ayarlarla) bir
karşılama satırı da görürsün — ama görevin başarı kriteri LED'in
kendisidir; terminal çıktısı isteğe bağlı bir doğrulamadır.

## Notlar / teyitli değerler

- `DS50_LED_PIN_MIO = 23`, `XGpioPs` API'leri ve klasik `LookupConfig`
  kalıbı: `content/_arastirma.md` §1 ve §5'ten.
- `main_registers.c`'deki `DIRM_0`/`OEN_0`/`DATA_0` offset'leri (Bank 0:
  `0x204`/`0x208`/`0x040`) doğrudan Xilinx/AMD embeddedsw
  `xgpiops_hw.h`'den alındı ve bu oturumda teyit edildi — ayrıntılar ve
  formüller `content/_arastirma-ek-B.md`'de.
- `usleep()` (`sleep.h`, standalone BSP, A53 hedefinde `usleep_A53`'e
  yönlenir) de bu oturumda embeddedsw kaynağından teyit edildi — bkz.
  `content/_arastirma-ek-B.md`. Ek kütüphane ya da BSP ayarı gerekmez.
