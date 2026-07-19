# Ek B — Sözlük

Doküman boyunca kullanılan teknik terimlerin alfabetik listesi. Her madde,
terimin derinlemesine ilk işlendiği bölüme işaret eder — bağlamıyla birlikte
tam tanım oradadır.

**ACK** — I2C'de alıcının SDA hattını düşüğe çekerek "byte alındı" dediği
alındı biti; karşıtı NACK (Bölüm 8).

**AXI** — PS ile PL arasında ve PL içindeki IP blokları arasında kullanılan
standart donanım veriyolu (Advanced eXtensible Interface); okuma/yazma
kanalları üzerinden valid/ready el sıkışmasıyla çalışır (Bölüm 9).

**bare-metal** — Altta işletim sistemi olmayan, uygulamanın donanımı
doğrudan sürdüğü çalışma modeli; bu dokümanın ilk görevlerinin ortamı
(Bölüm 10).

**baud** — UART'ta saniyede iletilen sembol sayısı; haberleşmeden önce iki
taraf aynı baud hızında anlaşmalı (Bölüm 8).

**bitstream** — PL'i (FPGA fabric) belirli bir donanım tasarımına göre
yapılandıran ikili dosya; boot sırasında FSBL tarafından yüklenir (Bölüm 3).

**boot.bin** — BootROM'un karttan okuduğu boot imaj dosyası; FSBL'i ve
varsa bitstream ile uygulamayı bir arada paketler (Bölüm 3).

**BootROM** — Çipe gömülü, değiştirilemez kod; reset sonrası ilk o çalışır,
boot mode pinlerine bakar ve FSBL'i yükler (Bölüm 3).

**bring-up** — Yeni bir kartı veya alt sistemi ilk kez besleyip temel
işlevlerini doğrulama süreci (Bölüm 1).

**BSP** — Board Support Package; bir donanım platformu için üretilen
sürücü ve başlık dosyaları topluluğu; Vitis'te uygulama projesinin altında
yatar (Bölüm 11).

**cache** — CPU ile ana bellek arasındaki hız farkını kapatan küçük ve
hızlı bellek katmanı; DMA ile tutarlılık (coherency) sorunlarının kaynağı
olabilir (Bölüm 6).

**context switch** — Scheduler'ın bir task'ı askıya alıp diğerini
çalıştırmaya başlarken yaptığı register/durum takası (Bölüm 10).

**datasheet** — Bir çipin register'larını, elektriksel özelliklerini ve
davranışını tanımlayan üretici dokümanı; gömülü yazılımcının temel okuma
malzemesi (Bölüm 8).

**debounce** — Mekanik buton veya anahtarın basılınca ürettiği sahte, hızlı
geçişleri süzen yazılımsal ya da donanımsal teknik (Bölüm 6).

**debugger** — Programı adım adım yürütmeyi, breakpoint koymayı, register
ve bellek durumunu incelemeyi sağlayan araç; Vitis'te JTAG üzerinden
çalışır (Bölüm 11).

**device tree** — Linux çekirdeğine donanım cihazlarının hangi adres ve
interrupt'larda oturduğunu anlatan tanım ağacı; bare-metal dünyadaki
`xparameters.h`'ın Linux karşılığı sayılabilir (Bölüm 13).

**DMA** — Direct Memory Access; CPU'yu meşgul etmeden bellekler arasında
veri taşıyan donanım (Bölüm 6).

**driver** — Bir donanım biriminin register'larını sarıp üst katmanlara
temiz bir fonksiyon arayüzü sunan yazılım katmanı (Bölüm 1).

**edge/level triggering** — Interrupt'ın sinyal geçişinde (edge —
yükselen/düşen) mi, yoksa sinyal durumunda (level — yüksek/düşük kaldığı
sürece) mi tetiklendiği ayrımı (Bölüm 7).

**EMIO** — Extended MIO; PS'in yerleşik MIO pin sayısı yetmediğinde GPIO
gibi sinyalleri PL üzerinden dışarı çıkarma yolu (Bölüm 9).

**FIFO** — First In First Out; UART gibi çevre birimlerinde kullanılan,
veriyi sırayla biriktirip aynı sırayla veren donanım tamponu (Bölüm 5).

**FPGA** — Field-Programmable Gate Array; PL'in fiziksel olarak üzerinde
oturduğu, yeniden yapılandırılabilir donanım dokusu (Bölüm 2).

**FSBL** — First Stage Bootloader; BootROM'un OCM'e yüklediği ilk yazılım
aşaması; DDR'ı ve (bitstream varsa) PL'i başlatır, sonra uygulamayı
çalıştırır (Bölüm 3).

**GIC** — Generic Interrupt Controller; interrupt kaynaklarını
önceliklendirip uygun çekirdeğe yönlendiren donanım (Bölüm 7).

**GPIO** — General Purpose Input/Output; yönü ve durumu yazılımla
ayarlanabilen genel amaçlı sayısal pin (Bölüm 4).

**heap** — Çalışma zamanında dinamik olarak ayrılan bellek bölgesi; gömülü
sistemlerde temkinli kullanılır (Bölüm 6).

**I2C** — İki telli (SDA/SCL), adresleme ve ACK/NACK mekanizmasıyla çok
cihazı destekleyen senkron seri protokol (Bölüm 8).

**interrupt** — Donanımın CPU'ya "bir olay oldu, hemen ilgilen" demek için
gönderdiği sinyal; polling'in alternatifi (Bölüm 7).

**IP** — Intellectual Property; PL'de oturan, AXI GPIO gibi belirli bir
işi yapan hazır veya özel tasarım donanım bloğu (Bölüm 9).

**ISR** — Interrupt Service Routine; interrupt gerçekleştiğinde çalışan,
kısa tutulması gereken özel fonksiyon (Bölüm 7).

**JTAG** — Kartı programlama ve debug için kullanılan endüstri standardı
seri erişim arayüzü; ZCU111'de aynı USB kablosu üzerinden taşınır
(Bölüm 2).

**linker script** — Derlenen kodun (`.text`, `.data`, `.bss` gibi ELF
bölümlerinin) bellek haritasında nereye yerleşeceğini tanımlayan betik
(Bölüm 6).

**memory-mapped I/O** — Çevre birimi register'larının, CPU'nun gözünden
sıradan bellek adresleri gibi okunup yazılabilmesi tasarım ilkesi
(Bölüm 4).

**MIO** — Multiplexed I/O; PS'in dış dünyaya doğrudan bağlanan, her biri
birkaç işlevden birine atanabilen sabit pin kümesi (Bölüm 4).

**MOSI/MISO** — SPI'da veriyi master'dan slave'e (Master Out Slave In) ve
slave'den master'a (Master In Slave Out) taşıyan iki ayrı hat (Bölüm 8).

**mutex** — Aynı anda yalnızca bir task'ın tutabildiği, paylaşılan kaynağı
korumak için kullanılan özelleşmiş semaphore türü (Bölüm 10).

**OCM** — On-Chip Memory; çipin içindeki, DDR'a bağımlı olmayan küçük ve
hızlı bellek; FSBL buraya yüklenir (Bölüm 3).

**open-drain** — Hattın yalnızca düşüğe (0'a) çekilebildiği, yükseğe
çekmek için harici pull-up direnci gereken çıkış türü; I2C'nin temel
fiziksel katmanı (Bölüm 8).

**parity** — UART frame'ine temel hata tespiti için eklenen ek bit; veri
bitlerindeki 1'lerin tek mi çift mi olduğunu sınar (Bölüm 8).

**PL** — Programmable Logic; Zynq'in FPGA fabric tarafı; donanımcıların
kendi IP bloklarını yerleştirdiği alan (Bölüm 2).

**polling** — CPU'nun bir koşulu (örn. buton durumu veya FIFO doluluğu)
döngüyle sürekli sorgulaması; interrupt'a göre basit ama CPU'yu meşgul
eden alternatif (Bölüm 6).

**priority inversion** — Düşük öncelikli task'ın tuttuğu kaynağı bekleyen
yüksek öncelikli task'ın, araya giren orta öncelikli task'lar yüzünden
fiilen geciktiği, düşük öncelikliymiş gibi davrandığı sorun (Bölüm 10).

**PS** — Processing System; Zynq'in sabit çekirdekleri (A53/R5) ve sabit
çevre birimlerini (UART, I2C, GPIO vb.) barındıran tarafı (Bölüm 2).

**pull-up** — Hattı varsayılan olarak yüksek (1) seviyede tutan direnç;
I2C gibi open-drain hatlarda zorunlu (Bölüm 8).

**queue** — FreeRTOS'ta task'lar (veya ISR ile task) arasında veri
aktarmak için kullanılan, FIFO mantığıyla çalışan senkronize mesaj kutusu
(Bölüm 10).

**register / register map** — Bir çevre biriminin davranışını kontrol eden
veya durumunu bildiren, belirli adresteki bellek hücresi (register); bir
çevre biriminin tüm register'larının offset, alan ve erişim türüyle
(R/W/RO/W1C) birlikte tam listesi (register map) (Bölüm 4).

**RTOS** — Real-Time Operating System; zamanlama garantisi veren,
task/scheduler tabanlı işletim sistemi; bu doküman örnek olarak FreeRTOS
kullanır (Bölüm 10).

**scheduler** — Hangi task'ın ne zaman çalışacağına karar veren çekirdek
RTOS bileşeni (Bölüm 10).

**semaphore** — Task'lar (veya ISR ile task) arasında olay bildirimi ya da
kaynak sayımı için kullanılan senkronizasyon nesnesi (Bölüm 10).

**SoC** — System-on-Chip; işlemci, bellek denetleyicisi ve çevre
birimlerinin tek çipte birleştirildiği tasarım yaklaşımı; Zynq UltraScale+
bunun bir örneği (Bölüm 2).

**SPI** — Dört telli (SCLK/MOSI/MISO/CS), senkron, yüksek hızlı,
master-slave seri protokol (Bölüm 8).

**stack** — Fonksiyon çağrılarının yerel değişkenlerini ve dönüş
adreslerini tutan, LIFO mantığıyla büyüyüp küçülen bellek bölgesi
(Bölüm 6).

**task** — RTOS'ta kendi stack'ine sahip, bağımsız olarak zamanlanabilen
çalıştırma birimi (Bölüm 10).

**tick** — RTOS scheduler'ının zaman birimini ölçtüğü periyodik interrupt
darbesi (Bölüm 10).

**TRM** — Technical Reference Manual; bir çipin bellek haritasını,
register kümesini ve mimarisini ayrıntısıyla anlatan birincil kaynak
doküman (Bölüm 3).

**UART** — Universal Asynchronous Receiver/Transmitter; baud hızında
anlaşma gerektiren, iki telli, asenkron seri haberleşme protokolü
(Bölüm 8).

**volatile** — Derleyiciye "bu değişkeni optimize etme; her erişimde
gerçekten oku/yaz" diyen C niteleyicisi; register erişiminde zorunlu
(Bölüm 5).

**W1C** — Write-1-to-Clear; register alanına 1 yazmanın o biti
temizlediği (0 yaptığı), 0 yazmanın ise etkisiz olduğu erişim türü
(Bölüm 4).

**watchdog** — Yazılım periyodik "besleme" sinyali göndermezse sistemi
otomatik resetleyen bekçi zamanlayıcı (Bölüm 13).

**XSA** — Xilinx Support Archive; Vivado'dan dışa aktarılan, PS/PL donanım
tanımını (bitstream'li veya bitstream'siz) taşıyan dosya; Vitis platform
projesinin girdisidir (Bölüm 11).

**xparameters.h** — Vitis platformu için otomatik üretilen, tüm çevre
birimi taban adreslerini ve cihaz ID'lerini sabit olarak tanımlayan başlık
dosyası (Bölüm 4).
