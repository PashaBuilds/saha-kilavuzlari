# Bölüm 3 — Ethernet ve MAC

Artık zarfların en dıştakine, kabloya fiilen çıkan pakete yakından bakma
zamanı. Ethernet, veri bağı katmanının ezici standardıdır: laboratuvardaki
FPGA kartından veri merkezindeki sunucuya kadar aynı frame formatı konuşulur.
Bu bölümde Wireshark'ta göreceğin her frame'in iskeletini byte byte öğrenecek,
MAC adresinin yapısını ve üç gönderim türünü (unicast/broadcast/multicast)
netleştireceksin.

## Frame anatomisi

Ethernet'in taşıma birimi **frame**dir (çerçeve). Bugün fiilen kullanılan
format **Ethernet II** (DIX) formatıdır:

{{svg:sema-04-frame-anatomi.svg|Ethernet II frame'inin kablodaki dizilişi. Preamble ve SFD senkronizasyon içindir, frame'den sayılmaz; Wireshark bu yüzden onları göstermez. EtherType, payload'daki protokolü; FCS ise frame'in sağlamlığını söyler.}}

Alanları sırayla okuyalım:

- **Preamble + SFD (8 byte):** `10101010...` deseniyle alıcının saat
  devresini kilitlemesini sağlar; SFD (start frame delimiter) "desen bitti,
  frame başlıyor" işaretidir. Frame'in parçası sayılmaz — Wireshark'ta
  göremezsin, çünkü Ethernet donanımı onu yazılıma hiç çıkarmaz.
- **Hedef MAC (6 byte):** frame'in bu segmentteki alıcısı. Switch'ler bu
  alana bakarak yönlendirme yapar (Bölüm 4).
- **Kaynak MAC (6 byte):** göndericinin adresi.
- **EtherType (2 byte):** payload'da hangi protokolün taşındığını söyler:
  `0x0800` IPv4, `0x0806` ARP, `0x86DD` IPv6. Alıcı stack, frame'i hangi
  üst katman koduna teslim edeceğine buradan karar verir. (Enkapsülasyon
  zincirindeki "zarfın üstündeki içerik etiketi" tam olarak budur.)
- **Payload (46–1500 byte):** taşınan veri — bizim zincirde IP paketi.
  Alt sınır 46'dır; daha kısa veri sıfırlarla doldurulur (padding).
  Üst sınır 1500, birazdan geleceğimiz MTU'dur.
- **FCS (4 byte):** frame check sequence — tüm frame üzerinden hesaplanan
  CRC-32. Alıcı donanım CRC'yi yeniden hesaplar; tutmuyorsa frame **sessizce
  atılır**. Üst katmanlara "bozuk frame geldi" diye bir haber gitmez; kayıp
  telafisi gerekiyorsa o iş TCP'nindir (Bölüm 9).

:::saha-notu Frame boyutunu Wireshark'la doğrula
Wireshark'ta bir frame seç; alttaki durum çubuğu `Frame 42: 74 bytes on
wire` der. 74 = 14 (Ethernet header) + 20 (IP) + 20 (TCP) + 20 (veri).
Preamble/SFD ve çoğu kartta FCS bu sayıya dahil değildir — kart FCS'i
doğrulayıp söker, yazılıma vermez. "Hesabım 4 byte eksik çıkıyor" şaşkınlığı
hep buradan gelir.
:::

## MAC adresi: donanımın kimliği

**MAC (Media Access Control) adresi**, 48 bit = 6 byte'lık, ağ arabirimine
üretimde verilen kimliktir; `D8:3A:DD:4F:A2:1C` gibi hex çiftlerle yazılır.

{{svg:sema-05-mac-adres.svg|MAC adresinin iç yapısı: ilk üç byte IEEE'nin üreticiye tahsis ettiği OUI, son üç byte üreticinin karta verdiği benzersiz numara. İlk byte'ın son iki biti U/L ve I/G bayraklarıdır; 48 bitin tamamı 1 olursa broadcast adresi çıkar.}}

- İlk 3 byte **OUI**'dir (Organizationally Unique Identifier — üretici
  kodu): IEEE tarafından üreticilere satılır. Wireshark bu yüzden kaynak
  MAC'in yanına `RaspberryP` ya da `Xilinx` yazabilir — tablodan OUI'yi
  çözmüştür. Sahada karşı tarafın "ne olduğunu" kestirmek için birebirdir.
- Son 3 byte üreticinin o karta verdiği numaradır.
- İlk byte'taki **I/G biti** adresin unicast mi multicast mi olduğunu,
  **U/L biti** adresin üretici tarafından mı yoksa yazılımla yerel olarak mı
  atandığını söyler. Gömülü kartlarda MAC'i genellikle sen yazılımla
  atarsın — ciddi ürünlerde EEPROM'dan okunan satın alınmış bir adres,
  hızlı prototipte U/L biti 1 yapılmış uydurma bir adres.

:::tuzak Aynı ağda iki kez aynı MAC
Prototip kartların hepsine aynı örnek MAC'i (`00:0A:35:00:01:02` gibi bir
SDK varsayılanını) yazıp hepsini aynı switch'e takmak, tuhaflığı garanti
eder: switch'in MAC tablosu (Bölüm 4) iki port arasında gidip gelir,
trafik bir o karta bir bu karta akar. Aynı segmentte MAC benzersiz olmak
zorundadır. Çok kartlı lab kurulumunda MAC'in son byte'ını kart numarasıyla
değiştirmeyi alışkanlık yap.
:::

## Unicast, broadcast, multicast

Hedef MAC alanının değerine göre üç gönderim türü vardır:

- **Unicast** (tek alıcıya): hedef, belirli bir kartın MAC'i. Trafiğin
  ezici çoğunluğu budur.
- **Broadcast** (tüm ağa yayın): hedef `FF:FF:FF:FF:FF:FF`. Segmentteki
  *her* cihaz frame'i alır ve işlemek zorunda kalır. ARP (Bölüm 7) ve
  DHCP (Bölüm 8) broadcast'e dayanır. Broadcast'in ulaştığı alana
  **broadcast domain** denir — Bölüm 4'te sınırlarını çizeceğiz.
- **Multicast** (gruba yayın): hedef, I/G biti 1 olan bir grup adresi
  (`01:00:5E:...` gibi). Yalnızca o gruba abone kartlar işler; ötekiler
  donanımda filtreler. Test cihazlarının keşif protokolleri (mDNS, LLDP)
  ve endüstriyel protokoller multicast'i bolca kullanır.

## MTU ve jumbo frame

**MTU (Maximum Transmission Unit)**, bir frame'in taşıyabileceği en büyük
payload'dır; standart Ethernet'te **1500 byte**. Üst katmanlar bu sınıra
uymak zorundadır: 8000 byte'lık bir veri, IP/TCP tarafından 1500'lük
dilimlere bölünerek gönderilir.

Bazı ağlar **jumbo frame** destekler (tipik 9000 byte MTU): frame başına
header maliyeti düşer, yüksek bant genişlikli veri akışında (ör. FPGA'dan
10GbE ile örnek verisi akıtırken) CPU yükü ciddi azalır. Ama jumbo,
*yol üstündeki her cihaz* destekliyorsa çalışır: kartın, switch'in ve
alıcının MTU'su uyuşmalı. Uyuşmazsa frame'ler sessizce düşer ya da IP
parçalanmasına (fragmentation) düşersin — Bölüm 5'in derin dalışında var.
Kural: jumbo'yu ancak uçtan uca kontrol ettiğin kapalı bir lab ağında aç.

:::analoji EtherType: koli etiketi
Frame bir koliyse MAC adresleri gönderici/alıcı etiketi, EtherType ise
kolinin üstündeki "içindekiler: cam eşya" yazısıdır. Depo görevlisi (ağ
stack'i) koliyi açmadan hangi rafa — IPv4 işleyicisine mi, ARP koduna mı —
göndereceğini bu etiketten bilir.
:::

:::derin-dalis VLAN: aynı kabloda ayrı ağlar (802.1Q)
Kurumsal switch'lerde tek fiziksel altyapıyı mantıksal ağlara bölmek için
**VLAN** (Virtual LAN) kullanılır. Mekanizması frame'e bakınca anlaşılır:
802.1Q standardı, kaynak MAC ile EtherType arasına 4 byte'lık bir **tag**
sokar. Tag'in içinde 12 bitlik **VLAN ID** (1–4094) vardır; switch, frame'i
yalnızca aynı VLAN'a üye portlara iletir. Böylece aynı switch'te "üretim
ağı VLAN 10" ile "test ağı VLAN 20" birbirini hiç görmeden yaşar — ayrı
broadcast domain'lerdir.

Gömülü yazılımcıyı ilgilendiren yüzü: kartını taktığın port **access port**
ise switch tag'i senin yerine ekler/söker, kartın VLAN'dan habersizdir —
tipik durum budur. Port **trunk** (çok VLAN taşıyan hat) olarak ayarlıysa
frame'ler tag'li gelir; kartın stack'i 802.1Q beklemiyorsa EtherType
`0x8100` görüp paketi anlamsız bulur. "Aynı switch'e taktım ama sunucuyu
göremiyorum" arızalarının bir bölümü, iki portun farklı VLAN'larda
olmasıdır — kablo değil, yapılandırma sorunu. IT'ye sorulacak doğru soru:
"Bu port hangi VLAN'da, access mi trunk mü?"
:::

:::ozet
- Ethernet II frame: hedef MAC (6) + kaynak MAC (6) + EtherType (2) +
  payload (46–1500) + FCS (4); preamble/SFD frame'den sayılmaz.
- EtherType payload'ın protokolünü söyler: 0x0800 IPv4, 0x0806 ARP.
- FCS tutmayan frame sessizce atılır; kaybı telafi etmek üst katmanın işi.
- MAC = OUI (üretici) + cihaz numarası; aynı segmentte benzersiz olmalı.
- Üç gönderim türü: unicast (tek), broadcast (herkes, FF:FF:...),
  multicast (grup).
- MTU 1500'dür; jumbo frame ancak uçtan uca herkes destekliyorsa açılır.
:::
