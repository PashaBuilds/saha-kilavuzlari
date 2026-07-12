# Bölüm 8 — Clock Kalitesi

{{sec:2}}'de acımasız bir tablo görmüştün: 3 GHz girişte 60 dB SNR
istiyorsan toplam jitter'ın ~50 fs altında kalacak. Elli femtosaniye —
ışığın 15 mikrometre yol aldığı süre. Bu bütçeyle yaşamak, clock'u "kart
üstünde bir osilatör + biraz iz" olmaktan çıkarıp başlı başına bir **alt
sistem** yapar: referans osilatör, jitter temizleyen PLL'ler, dikkatle
yönetilen dağıtım. KISIM IV'te inceleyeceğimiz kartların neredeyse yarısı
clock devresidir; bu bölüm o devrelerin dilini öğretir. Gömülü yazılımcı
olarak clock chip'in yüzlerce register'ını sen yazacaksın — ne yazdığını
bilerek yazman için buradayız.

::: ogren
- Faz gürültüsü grafiğini okumayı
- Integrated jitter hesabını ve entegrasyon bandı seçimini
- Referans → PLL → dağıtım zincirinin mantığını
- Dual-loop (çift döngülü) jitter temizleme mimarisini
- Clock chip anatomisini: girişler, PLL1/PLL2, bölücüler, DCLK/SYSREF çifti
:::

## Faz gürültüsü grafiğini okumak

İdeal osilatör, spektrumda sonsuz ince bir çizgidir; gerçek osilatörün
çizgisi etekleriyle birlikte gelir. **Faz gürültüsü** L(f), bu eteğin
taşıyıcıdan f kadar uzakta, 1 Hz'lik banttaki gücünün taşıyıcıya oranıdır;
birimi dBc/Hz, grafiği log-log eksende çizilir. Tipik bir grafikte üç bölge
görürsün:

- **Taşıyıcıya yakın** (Hz–kHz offsetler): dik iniş (1/f³, 1/f² eğimleri) —
  osilatörün ve PLL'in yavaş kararsızlıkları.
- **Orta bölge** (kHz–MHz): PLL loop dinamiklerinin şekillendirdiği platoya
  benzer bölge; PLL tasarımının parmak izi buradadır.
- **Uzak bölge** (MHz ve ötesi): düz **gürültü tabanı** (beyaz faz
  gürültüsü) — çıkış tamponlarının ve bölücülerin katkısı.

Grafikte tek tük **spur** çizgileri de olur: güç kaynağı anahtarlama
frekansı, referans kaçağı, komşu devre kuplajı. Bunlar rastgele gürültü
değil deterministik kirlilliktir; jitter hesabına ayrıca girerler ve
genelde bir kaynak avıyla (kim 300 kHz'de anahtarlıyor?) çözülürler.

## Integrated jitter: grafikten tek sayıya

ADC'nin umursadığı, bu eğrinin altında kalan **toplam** güçtür. L(f), bir
f₁–f₂ bandında entegre edilir; çıkan toplam faz gürültüsü gücü A (dBc)
RMS jitter'a çevrilir:

```text
t_j(rms) = √(2 · 10^(A/10)) / (2π · f_c)
```

(f_c: taşıyıcı, yani clock frekansı.) Sayısal örnek: 3 GHz device clock,
seçilen bantta entegre faz gürültüsü A = −70 dBc olsun. 10^(−7) → ×2 →
karekök = 4.47×10⁻⁴ radyan; 2π·3×10⁹'a bölünce **≈ 24 fs**. {{sec:2}}'nin
tablosuna göre 3 GHz girişte tek başına ~66.5 dB'lik jitter tavanı demek —
bütçeye sığdık. Aynı eğri A = −60 dBc verseydi jitter 75 fs'e, tavan
~57 dB'ye düşerdi. Grafikteki 10 dB, sistem SNR'ında 10 dB'dir; faz
gürültüsü eğrisi bir "analog detay" değil, doğrudan ürün spesifikasyonudur.

Peki f₁ ve f₂ nereden geliyor? Burası datasheet tuzağıdır:

::: dikkat
"RMS jitter = 45 fs" yazan iki datasheet, farklı entegrasyon bantları
kullanıyorsa **karşılaştırılamaz**. Telekom klasiği 12 kHz–20 MHz'dir; ama
senin ADC'n için doğru bant sistemine bağlıdır: alt sınır, sistemin artık
"takip edebildiği" yavaşlıktaki bozulmalarla belirlenir (çok yavaş faz
gezinmesini CDR'lar, taşıyıcı takibi ve kalibrasyon affeder); üst sınır
ise clock'un kullanıldığı bant genişliğine uzanır — GS/s ADC'de fs/2'ye
kadar, yani onlarca-yüzlerce MHz. Somut örnek: LMK04832 datasheet'i aynı
çıkış için 2500 MHz'te 12 kHz–20 MHz bandında 54 fs, 100 Hz–20 MHz
bandında 64 fs verir — aynı silikon, iki sayı. Datasheet karşılaştırırken
ilk soru hep aynı: *hangi bant?* (İkinci soru: taban hangi frekansa kadar
entegre edilmiş — ADF4382 gibi çipler 100 MHz'e kadar entegre eder, telekom
bandıyla yan yana koyamazsın.)
:::

## Zincir: referans → PLL → dağıtım

Tek bir osilatör hem yakında hem uzakta iyi olamaz. Kristal osilatörler
(XO/TCXO/OCXO) taşıyıcıya yakın bölgede mükemmeldir ama frekansları
düşüktür (on-yüz MHz sınıfı); GHz sınıfı VCO'lar yüksek frekans üretir ama
yakın bölgede gürültülüdür. **PLL** (phase-locked loop — faz kilitli
döngü), iki dünyayı birleştiren filtredir: loop bandwidth'inin *içinde*
referansın karakterini, *dışında* VCO'nun karakterini geçirir. Doğru
kurgulanmış bir PLL, "kristalin yakını + iyi VCO'nun uzağı" diye
özetlenebilecek melez bir eğri üretir.

RF-sampling sisteminin clock zinciri bu fikrin ardışık uygulamasıdır:
kararlı ama düşük frekanslı bir **sistem referansı** (örn. 10 MHz OCXO
veya şasiden gelen referans) → temizleyip çarpan PLL katmanları → GHz
sınıfı device clock'lar → dağıtım (bölücüler, tamponlar, eşlenmiş izler).
Zincirin her halkası kendi gürültüsünü ekler; bütçe, {{sec:17}}'de tablo
olarak karşına çıkacak.

## Dual-loop mimari: jitter cleaning

Sahada sık bir durum: referans temiz *değil*. Şasiden gelen 10 MHz, uzun
kablolardan geçmiş, sayısız karttan dağıtılmış, faz gürültüsü kirlenmiş
olabilir. Tek PLL'le hem bu kiri süzmek (çok dar loop bandwidth ister) hem
GHz'e çarpmak (genişçe bir loop ister) çelişir. Çözüm, işi ikiye bölmek —
**dual-loop** mimari; LMK04832 ve HMC7044'ün ({{sec:11}}–{{sec:12}}) ortak
DNA'sı:

- **PLL1 — temizlik döngüsü**: kirli referansı, kart üstündeki temiz bir
  **VCXO**'ya (voltage-controlled crystal oscillator) çok dar bir loop
  bandwidth ile kilitler (Hz–onlarca Hz sınıfı). Sonuç: referansın *uzun
  vadeli frekans doğruluğu* + VCXO'nun *temiz faz gürültüsü*. Kir, dar
  filtrede kalır.
- **PLL2 — çarpma döngüsü**: VCXO'nun temiz ama düşük frekanslı çıkışını,
  geniş loop bandwidth'li ikinci bir döngüyle GHz sınıfı dahili VCO'ya
  çarpar. Çıkış bölücüleri buradan beslenir.

İki döngü arasındaki iş bölümünü loop bandwidth'ler anlatır: PLL1 dar
(süzgeç), PLL2 geniş (çarpan). **Yazılıma dokunduğu yer**: bu bandwidth'ler
ve bölücü oranları, init'te yazdığın register'lardır; üreticinin
konfigürasyon aracından çıkan değerleri anlamadan kopyalarsan, sahada
"kilitleniyor ama jitter kötü" durumunda elin kolun bağlı kalır. Kilit
sırası da senindir: PLL1 kilidini bekle → PLL2 kilidini bekle → çıkışları
aç ({{sec:15}}).

## Clock chip anatomisi

Bir jitter-cleaner clock chip'in kuşbakışı iskeleti hep aynıdır:

1. **Giriş seçici**: birden çok referans girişi (CLKin benzeri adlarla) ve
   otomatik/manuel seçim, holdover (referans düşerse VCXO'yla idare etme)
   mantığı.
2. **PLL1 + harici VCXO**: temizlik döngüsü.
3. **PLL2 + dahili VCO**: çarpma döngüsü.
4. **Çıkış bölücüleri ve tamponları**: VCO'dan türetilmiş, kanal başına
   bölücü + çıkış standardı seçimi (LVDS/LVPECL/CML sınıfı) olan çok sayıda
   çıkış.
5. **SYSREF üretici**: {{sec:9}}'un yıldızı — device clock'la aynı
   kaynaktan, bilinen fazla türetilen, bölücüsü ve tetikleme modu
   (continuous/gapped/one-shot) register'la seçilen senkronizasyon çıkışı.

Beşinci maddenin mimari sonucu, bu çiplerin çıkışlarını **çift** halinde
örgütlemesidir: her device clock çıkışının yanında, aynı bölücü zincirinden
türeyen bir SYSREF kardeşi (DCLK/SYSREF çifti). {{sec:9}}'daki setup/hold
penceresinin sırrı buydu: çift, aynı kaynaktan doğduğu için aralarındaki
faz *bilinir* ve gecikme register'larıyla ince ayarlanır. {{sec:11}} ve
{{sec:12}}'de bu anatomiyi iki gerçek çipin pin adlarıyla dolduracağız.

::: not
Peki ya device clock ihtiyacın clock chip'in VCO'sundan da yüksekse — ya da
AFE clock'unu birkaç GHz'te, birden çok çipe *çok temiz* dağıtman
gerekiyorsa? O zaman zincire bir halka daha eklenir: yüksek frekans
sentezleyici (ADF4382 sınıfı) veya GHz sınıfı dağıtıcı (LMX1204 sınıfı).
Bu iş bölümünün iki üreticideki farklı çözümleri, {{sec:13}}'teki
karşılaştırmanın en öğretici kısmıdır.
:::

Clock kalitesinin dili bu kadar. Şimdi bu temiz clock'ların üstüne inşa
edilen hizalama mekanizmasına — SYSREF'e — geçiyoruz.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- Analog Devices, MT-008: *Converting Oscillator Phase Noise to Time
  Jitter* ve TI SLYT379 — faz gürültüsü → jitter entegrasyonu.
- TI, LMK04832 datasheet (SNAS688) — dual-loop mimari, PLL1 bandwidth
  sınıfı, 54/64 fs bant örneği.
- ADI, HMC7044 datasheet — dual-loop mimari, DCLK/SYSREF çift kavramı
  ({{sec:11}}–{{sec:12}}'de pin düzeyinde).
- ADI, ADF4382 datasheet — geniş bant entegrasyon (100 Hz–100 MHz) örneği.
- Toplu ve linkli liste: {{sec:19}}.

</details>
