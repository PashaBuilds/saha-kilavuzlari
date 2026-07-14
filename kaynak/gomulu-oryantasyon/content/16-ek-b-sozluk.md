# Ek B — Sözlük

Dokümanda geçen teknik terimlerin alfabetik listesi. Her madde, terimin
dokümanda ilk ciddi biçimde işlendiği bölüme işaret eder — tam tanımı
orada, bağlamıyla birlikte bulursun.

**ACK** — I2C'de alıcının "bu baytı aldım" demek için SDA hattını aşağı
çektiği onay biti (acknowledge); karşılığı NACK'tir (Bölüm 8).

**AXI** — PS ile PL arasındaki (ve PL içi IP'ler arasındaki) standart
donanım veri yolu (Advanced eXtensible Interface); valid/ready el sıkışmalı
okuma/yazma kanalları üzerinden çalışır (Bölüm 9).

**bare-metal** — altında işletim sistemi olmayan, uygulamanın donanımı
doğrudan sürdüğü çalışma modeli; bu dokümanın ilk görevlerinin dünyası
(Bölüm 10).

**baud** — UART'ta saniyede taşınan sembol sayısı; iki uç konuşmadan önce
aynı baud değerinde anlaşmış olmalı (Bölüm 8).

**bitstream** — PL'yi (FPGA fabric'ini) belirli bir donanım tasarımına
göre yapılandıran ikili dosya; FSBL tarafından boot sırasında yüklenir
(Bölüm 3).

**boot.bin** — BootROM'un karttan okuduğu, FSBL ve gerekirse bitstream/
uygulamayı bir arada taşıyan önyükleme imaj dosyası (Bölüm 3).

**BootROM** — çipin içine gömülü, resetten sonra ilk çalışan; boot modu
pinlerine bakıp FSBL'yi yükleyen değiştirilemez kod (Bölüm 3).

**bring-up** — yeni bir kartın ya da alt sistemin ilk kez ayağa
kaldırılıp temel işlevlerinin doğrulandığı süreç (Bölüm 1).

**BSP** — Board Support Package; bir donanım platformu için üretilen
sürücü ve başlık dosyaları koleksiyonu; Vitis'te uygulama projesinin
altında durur (Bölüm 11).

**cache** — CPU ile ana bellek arasında hız farkını kapatan küçük, hızlı
bellek katmanı; DMA ile tutarlılık sorunlarının kaynağı olabilir (Bölüm 6).

**context switch** — scheduler'ın bir task'ın çalışmasını durdurup
başka bir task'ı çalıştırmaya geçtiği, kayıt/durum değişimi işlemi
(Bölüm 10).

**datasheet** — bir çipin register'larını, elektriksel özelliklerini ve
davranışını tanımlayan üretici belgesi; gömülü yazılımcının temel okuma
malzemesi (Bölüm 8).

**debounce** — mekanik bir butonun/anahtarın basılma anında ürettiği
sahte, hızlı geçişleri yazılımsal ya da donanımsal olarak süzme tekniği
(Bölüm 6).

**debugger** — programı adım adım çalıştırmana, breakpoint koymana,
register ve bellek durumunu izlemene izin veren araç; Vitis'te JTAG
üzerinden çalışır (Bölüm 11).

**device tree** — Linux çekirdeğine donanımın hangi adreste, hangi
kesmede olduğunu anlatan açıklama ağacı; bare-metal dünyadaki
`xparameters.h`'nin Linux karşılığı sayılabilir (Bölüm 13).

**DMA** — Direct Memory Access; CPU'yu meşgul etmeden bellekler arası
veri taşıyan donanım (Bölüm 6).

**driver** — bir donanım biriminin register'larını saran, üst katmana
temiz bir fonksiyon arayüzü sunan yazılım katmanı (Bölüm 1).

**edge/level tetikleme** — bir kesmenin sinyalin geçişinde (edge — yükselen/
düşen kenar) mi yoksa sinyalin durumunda (level — yüksek/düşük seviyede
kaldığı sürece) mi tetiklendiği ayrımı (Bölüm 7).

**EMIO** — PS'in dahili MIO pin sayısı yetmediğinde, GPIO gibi sinyalleri
PL üzerinden dışarı çıkarma yolu (Extended MIO) (Bölüm 9).

**FIFO** — First In First Out; UART gibi çevre birimlerinde veriyi
sırasıyla biriktirip aynı sırayla boşaltan donanım tamponu (Bölüm 5).

**FPGA** — alan programlanabilir kapı dizisi; PL'nin fiziksel olarak
üzerinde yaşadığı, yeniden yapılandırılabilir donanım fabric'i (Bölüm 2).

**FSBL** — First Stage Bootloader; BootROM tarafından OCM'e yüklenen,
DDR'ı ve PL'yi (varsa bitstream ile) hazırlayıp uygulamayı başlatan ilk
yazılım aşaması (Bölüm 3).

**GIC** — Generic Interrupt Controller; kesme kaynaklarını önceliklendirip
uygun çekirdeğe yönlendiren donanım (Bölüm 7).

**GPIO** — General Purpose Input/Output; yazılımca yönü ve durumu
ayarlanabilen genel amaçlı dijital pin (Bölüm 4).

**heap** — çalışma zamanında dinamik olarak ayrılan bellek bölgesi;
gömülüde temkinli kullanılır (Bölüm 6).

**I2C** — iki telli (SDA/SCL), çoklu cihaz destekleyen, adresleme ve
ACK/NACK mekanizmalı senkron seri protokol (Bölüm 8).

**interrupt** — donanımın CPU'ya "bir olay oldu, hemen ilgilen" demek için
gönderdiği sinyal; polling'in alternatifi (Bölüm 7).

**IP** — Intellectual Property; PL içinde yaşayan, belirli bir işlevi
gören hazır ya da özel tasarım donanım bloğu (AXI GPIO gibi) (Bölüm 9).

**ISR** — Interrupt Service Routine; bir kesme geldiğinde çalışan, kısa
tutulması gereken özel fonksiyon (Bölüm 7).

**JTAG** — kartı programlamak ve debug etmek için kullanılan endüstri
standardı seri erişim arayüzü; ZCU111'de aynı USB kablosu üzerinden gelir
(Bölüm 2).

**linker script** — derlenmiş kodun (`.text`, `.data`, `.bss` gibi ELF
bölümlerinin) bellek haritasında nereye yerleşeceğini tanımlayan betik
(Bölüm 6).

**memory-mapped I/O** — çevre birimi register'larının, CPU'nun bakış
açısından sıradan bellek adresleriymiş gibi okunup yazılabildiği tasarım
ilkesi (Bölüm 4).

**MIO** — Multiplexed I/O; PS'in doğrudan dış dünyaya çıkan, çoklu
işlevden birine atanabilen sabit pin seti (Bölüm 4).

**MOSI/MISO** — SPI'de master'dan slave'e (Master Out Slave In) ve
slave'den master'a (Master In Slave Out) veri taşıyan iki ayrı hat
(Bölüm 8).

**mutex** — aynı anda yalnızca bir task'ın sahip olabileceği, paylaşılan
kaynağı korumak için kullanılan özel semaphore türü (Bölüm 10).

**OCM** — On-Chip Memory; çipin içindeki küçük, hızlı, DDR'a bağımlı
olmayan bellek; FSBL buraya yüklenir (Bölüm 3).

**open-drain** — bir hattın yalnızca aşağı çekilebildiği (0'a), yukarı
çekmek için harici bir pull-up dirence ihtiyaç duyduğu çıkış türü; I2C'nin
temel fiziksel katmanı (Bölüm 8).

**parity** — UART çerçevesinde basit hata sezimi için eklenen, veri
bitlerinin tek/çift sayıda 1 içerdiğini doğrulayan ek bit (Bölüm 8).

**PL** — Programmable Logic; Zynq'in FPGA fabric tarafı, donanımcının
kendi IP'lerini yerleştirdiği bölge (Bölüm 2).

**polling** — CPU'nun bir durumu (örn. buton, FIFO doluluğu) sürekli
döngüyle sorgulaması; interrupt'ın basit ama CPU'yu meşgul eden alternatifi
(Bölüm 6).

**priority inversion** — düşük öncelikli bir task'ın tuttuğu kaynağı
bekleyen yüksek öncelikli bir task'ın, ortadaki orta öncelikli task'lar
yüzünden fiilen daha düşük öncelikliymiş gibi davranması sorunu (Bölüm 10).

**PS** — Processing System; Zynq'in sabit çekirdekleri (A53/R5) ve sabit
çevre birimlerinin (UART, I2C, GPIO...) bulunduğu taraf (Bölüm 2).

**pull-up** — bir hattı varsayılan olarak yüksek (1) seviyede tutan
direnç; open-drain hatlarda (I2C gibi) zorunludur (Bölüm 8).

**queue** — FreeRTOS'ta task'lar (ya da ISR ile task) arasında veri
taşımak için kullanılan, FIFO mantığıyla çalışan senkronize mesaj kutusu
(Bölüm 10).

**register / register map** — bir çevre biriminin davranışını
kontrol eden ya da durumunu bildiren, belirli bir adreste yaşayan bellek
hücresi (register); bir çevre birimine ait tüm register'ların offset,
alan ve erişim tipi (R/W/RO/W1C) bilgisiyle listesi (register map)
(Bölüm 4).

**RTOS** — Real-Time Operating System; zamanlama garantileri veren,
task/scheduler tabanlı işletim sistemi; bu dokümanda FreeRTOS örneği
işlenir (Bölüm 10).

**scheduler** — RTOS'un hangi task'ın ne zaman çalışacağına karar veren
çekirdek bileşeni (Bölüm 10).

**semaphore** — task'lar (ya da ISR ile task) arasında olay bildirimi ya
da kaynak sayımı için kullanılan senkronizasyon nesnesi (Bölüm 10).

**SoC** — System-on-Chip; işlemci, bellek denetleyicisi ve çevre
birimlerinin tek bir çip üzerinde birleştiği tasarım yaklaşımı; Zynq
UltraScale+ bunun bir örneğidir (Bölüm 2).

**SPI** — dört telli (SCLK/MOSI/MISO/CS), senkron, yüksek hızlı, master-
slave seri protokol (Bölüm 8).

**stack** — fonksiyon çağrılarının yerel değişkenlerini ve dönüş
adreslerini tuttuğu, LIFO mantığıyla büyüyüp küçülen bellek bölgesi
(Bölüm 6).

**task** — RTOS'ta bağımsız zamanlanabilen, kendi stack'ine sahip
çalışma birimi (Bölüm 10).

**tick** — RTOS scheduler'ının zaman birimini ölçtüğü periyodik kesme
darbesi (Bölüm 10).

**TRM** — Technical Reference Manual; bir çipin bellek haritası, register
seti ve mimarisini ayrıntılı anlatan birincil kaynak belge (Bölüm 3).

**UART** — Universal Asynchronous Receiver/Transmitter; iki telli,
asenkron, baud anlaşmalı seri iletişim protokolü (Bölüm 8).

**volatile** — derleyiciye "bu değişkeni optimize etme, her erişimde
gerçekten oku/yaz" diyen C niteleyicisi; register erişiminde zorunludur
(Bölüm 5).

**W1C** — Write-1-to-Clear; bir register alanına 1 yazmanın o biti
temizlediği (0 yaptığı), 0 yazmanın hiçbir etkisi olmadığı erişim türü
(Bölüm 4).

**watchdog** — yazılım düzenli "besleme" göndermezse sistemi otomatik
resetleyen bekçi zamanlayıcı (Bölüm 13).

**XSA** — Xilinx Support Archive; Vivado'dan dışa aktarılan, PS/PL
donanım tanımını (bitstream'li ya da bitstream'siz) taşıyan dosya; Vitis
platform projesinin girdisidir (Bölüm 11).

**xparameters.h** — bir Vitis platformu için otomatik üretilen, tüm
çevre birimi taban adreslerini ve cihaz kimliklerini sabit olarak
tanımlayan başlık dosyası (Bölüm 4).
