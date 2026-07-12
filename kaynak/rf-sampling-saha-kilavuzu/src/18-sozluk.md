# Bölüm 18 — Sözlük

Tüm kısaltmalar ve terimler, alfabetik sırayla, tek cümlelik tanımlarla.
Her maddenin sonundaki bölüm bağlantısı, terimin derinlemesine anlatıldığı
yere götürür.

- **AC kuplaj** — TX ile RX'in DC seviyelerini ayrıştıran seri
  kondansatör; sinyalin DC-dengeli olmasını şart koşar. {{sec:4}}
- **ADC** — analog-to-digital converter; analog gerilimi sayıya çeviren
  blok. {{sec:2}}
- **AFE** — analog front end; ADC/DAC çekirdeklerini, DDC/DUC'ları ve
  JESD arayüzünü tek pakette toplayan RF-sampling entegresi. {{sec:0}}
- **aliasing** — örnekleme hızının yetmediği bileşenlerin başka frekansta
  görünmesi (katlanma). {{sec:1}}
- **aperture jitter** — ADC'nin kendi iç örnekleme anı belirsizliği.
  {{sec:2}}
- **balun** — single-ended sinyali diferansiyele çeviren pasif dönüştürücü.
  {{sec:1}}
- **BER** — bit error ratio; hatalı bit oranı, seri linkte tipik hedef
  10⁻¹². {{sec:4}}
- **blok (66-bit)** — JESD204C'nin temel birimi: 2 sync header biti +
  64 bit payload. {{sec:7}}
- **CDR** — clock and data recovery; clock'u veri geçişlerinden geri
  kazanan alıcı bloğu. {{sec:4}}
- **CGS** — code group synchronization; 204B'de K28.5 akışıyla kod grubu
  senkronizasyonu perdesi. {{sec:6}}
- **character replacement** — 204B'de frame/multiframe sonu oktetlerinin
  /F/ ve /A/ ile değiştirilerek hizanın izlenmesi. {{sec:6}}
- **CML** — current-mode logic; yüksek hızlı seri hatların tipik sürücü
  ailesi. {{sec:4}}
- **comma** — 8b/10b'de veri içinde oluşamayan, sözcük hizası veren desen
  (K28.5'in içinde). {{sec:6}}
- **core clock** — AMD JESD204C IP'sinin ana saati; 64B/66B'de lane
  rate/66. {{sec:14}}
- **CRC-12** — 204C'de multiblock başına 12 bitlik hata tespiti (sync
  word içinde taşınır). {{sec:7}}
- **CTLE** — continuous-time linear equalizer; RX'te yüksek frekansı
  yükselten analog eşitleyici. {{sec:4}}
- **DAC** — digital-to-analog converter; sayıyı analog gerilime çeviren
  blok. {{sec:2}}
- **DDC** — digital downconverter; NCO + mixer + decimation ile bant
  seçip hız düşüren dijital blok. {{sec:3}}
- **decimation** — filtreleyip seyrelterek örnek hızını düşürme. {{sec:3}}
- **deterministic latency** — link gecikmesinin açılıştan açılışa sabit
  olması garantisi. {{sec:10}}
- **device clock** — converter'ın örnekleme saatini ve link zamanlamasını
  türeten ana clock. {{sec:9}}
- **DFE** — decision feedback equalizer; karar geri beslemeli RX
  eşitleyicisi. {{sec:4}}
- **DSA** — digital step attenuator; kazancı register'la ayarlanan adımlı
  zayıflatıcı. {{sec:1}}
- **dual-loop** — kirli referansı VCXO'yla temizleyip (PLL1) sonra çarpan
  (PLL2) clock chip mimarisi. {{sec:8}}
- **DUC** — digital upconverter; interpolation + NCO ile bandı yukarı
  taşıyan verici bloğu. {{sec:3}}
- **elastic buffer** — lane'ler arası varış farklarını yutan, takvimle
  boşaltılan RX tamponu. {{sec:6}}
- **EMB** — extended multiblock; E adet multiblock'tan oluşan 204C takvim
  birimi. {{sec:7}}
- **ENOB** — effective number of bits; SINAD'dan türetilen gerçek etkin
  çözünürlük. {{sec:2}}
- **EoEMB** — end of extended multiblock; sync word'de EMB sınırını
  işaretleyen 100001 deseni. {{sec:7}}
- **eşitleme (equalization)** — kanal kaybını telafi eden TX/RX teknikleri
  bütünü. {{sec:4}}
- **eye diagram** — bit periyotlarının üst üste bindirilmesiyle oluşan göz
  görüntüsü; açıklığı link marjını gösterir. {{sec:4}}
- **faz gürültüsü** — osilatör spektrumunun taşıyıcı çevresine yayılan
  eteği, dBc/Hz. {{sec:8}}
- **FEC** — forward error correction; 204C'de multiblock başına 26 parite
  bitiyle hata düzeltme seçeneği. {{sec:7}}
- **folding** — spektrumun fs/2 katlarında akordeon gibi katlanması;
  aliasing'in geometrik dili. {{sec:1}}
- **frame** — transport katmanının S örneklik temel zaman dilimi.
  {{sec:5}}
- **gapped periodic** — senkronizasyon sırasında akıp sonra susturulan
  SYSREF tipi. {{sec:9}}
- **GT** — gigabit transceiver; FPGA'daki SerDes bloğu. {{sec:4}}
- **holdover** — referans kaybolduğunda clock chip'in VCXO ile frekansı
  koruma modu. {{sec:8}}
- **IBERT** — GT'lere gömülü BER test/göz tarama altyapısı. {{sec:16}}
- **ILAS** — initial lane alignment sequence; 204B'de 4 multiframe'lik
  hizalama ve kimlik geçidi. {{sec:6}}
- **IMD3** — üçüncü derece intermodülasyon ürünleri (2f1−f2, 2f2−f1).
  {{sec:2}}
- **integrated jitter** — faz gürültüsünün bir bantta entegre edilip
  zamana çevrilmiş hali (RMS). {{sec:8}}
- **interleaving** — birden çok ADC çekirdeğini sırayla çalıştırarak hız
  kazanma; spur ailesi üretir. {{sec:2}}
- **I/Q** — in-phase/quadrature; kompleks örneğin iki bileşeni. {{sec:3}}
- **ISI** — inter-symbol interference; bir bit'in enerjisinin komşu
  bit'lere taşması. {{sec:4}}
- **jitter** — clock kenarının ideal anından rastgele sapması. {{sec:2}}
- **K-karakteri** — 8b/10b'nin veri uzayı dışındaki kontrol kodları
  (K28.0, K28.3, K28.4, K28.5, K28.7). {{sec:4}}
- **K28.5** — comma deseni içeren K-karakteri; CGS'in yapı taşı. {{sec:6}}
- **lane** — tek diferansiyel çift üzerinden akan seri veri hattı.
  {{sec:4}}
- **LCPLL / RPLL** — Versal HSCLK bloğundaki LC-tank ve ring PLL'ler.
  {{sec:14}}
- **LEMC** — local extended multiblock clock; 204C'de EMB sınırlarını
  sayan yerel sayaç. {{sec:7}}
- **link parametreleri** — L, M, F, S, N, N′, K, E, CS, CF, HD: linki
  tarif eden ve iki uçta birebir eşleşmesi zorunlu set. {{sec:5}}
- **LMFC** — local multiframe clock; 204B'de multiframe sınırlarını sayan
  yerel sayaç. {{sec:6}}
- **LNA** — low-noise amplifier; zincirin gürültü figürünü belirleyen ilk
  yükselteç. {{sec:1}}
- **loopback** — zincirin bir dilimini geri döndürerek test etme; near-end
  ve far-end türleri. {{sec:16}}
- **LSB** — least significant bit; ADC'nin bir kuantalama basamağı.
  {{sec:2}}
- **mix-mode** — DAC'nin enerjisini 2. Nyquist bölgesine kaydıran çıkış
  modu. {{sec:2}}
- **multiblock** — 32 bloktan (2112 bit) oluşan 204C birimi. {{sec:7}}
- **multiframe** — K frame'den oluşan 204B takvim birimi. {{sec:6}}
- **NCO** — numerically controlled oscillator; faz akümülatörlü dijital
  osilatör. {{sec:3}}
- **NSD** — noise spectral density; 1 Hz başına gürültü, dBFS/Hz.
  {{sec:2}}
- **Nyquist bölgesi** — frekans ekseninin fs/2'lik dilimleri; n. bölge
  (n−1)fs/2..n·fs/2. {{sec:1}}
- **one-shot** — yazılım tetiğiyle tek/sayılı darbe üretilen SYSREF tipi;
  DC kuplaj ister. {{sec:9}}
- **PLL** — phase-locked loop; loop bandwidth'i içinde referansı, dışında
  VCO'yu geçiren frekans çarpanı/filtresi. {{sec:8}}
- **PRBS** — pseudo-random bit sequence; IBERT'in protokolsüz test deseni.
  {{sec:16}}
- **pre-emphasis** — TX'in geçişli bit'leri güçlendirerek kanal kaybını
  önceden telafi etmesi. {{sec:4}}
- **process gain** — bant daraltmanın (decimation) SNR'a 10·log10(fs/2BW)
  katkısı. {{sec:2}}
- **quad** — 4 GT kanalı + ortak clock kaynaklarından oluşan paket.
  {{sec:4}}
- **RBD** — RX buffer delay; elastic buffer release anının LMFC kenarından
  gecikmesi (1..K frame). {{sec:6}}
- **refclk** — GT PLL'lerini besleyen, kart üstü clock chip'ten gelen
  referans clock. {{sec:14}}
- **rekonstrüksiyon filtresi** — DAC imajlarını bastıran analog çıkış
  filtresi. {{sec:2}}
- **running disparity** — 8b/10b'nin DC dengeyi koruyan 1/0 sayım
  mekanizması. {{sec:4}}
- **scrambler** — veriyi polinomla karıştırarak spektral tepeleri ve desen
  bağımlılığını kıran blok. {{sec:5}}
- **SerDes** — serializer/deserializer; paralel-seri dönüşüm makinesi.
  {{sec:4}}
- **SFDR** — spurious-free dynamic range; sinyal ile en büyük spur arası
  mesafe. {{sec:2}}
- **SINAD** — signal-to-noise-and-distortion; gürültü+distorsiyon dahil
  sinyal oranı. {{sec:2}}
- **sinc roll-off** — DAC'nin örnek tutmasından doğan, fs/2'de −3.92 dB'lik
  spektral zarf. {{sec:2}}
- **SNR** — signal-to-noise ratio; sinyalin toplam gürültüye oranı.
  {{sec:2}}
- **subclass** — 204B'nin deterministic latency seviyeleri: 0 (yok),
  1 (SYSREF), 2 (SYNC~). {{sec:5}}
- **superheterodyne** — sinyali mixer'la ara frekansa indirip orada
  işleyen klasik alıcı mimarisi. {{sec:1}}
- **sync header** — 66-bit bloğun başındaki 2 bit; geçiş yönüyle sync
  word bitini kodlar. {{sec:7}}
- **SYNC~** — 204B'de RX'ten TX'e giden aktif-düşük senkronizasyon/hata
  sinyali. {{sec:6}}
- **SYSREF** — device clock'la örneklenen, LMFC/LEMC fazını sıfırlayan
  hizalama sinyali. {{sec:9}}
- **transport katmanı** — örnekleri oktetlere/frame'lere yerleştiren JESD
  katmanı. {{sec:5}}
- **undersampling** — sinyali 2. ve üstü Nyquist bölgelerinde örnekleyip
  katlanmayı mixer gibi kullanmak. {{sec:1}}
- **VCO** — voltage-controlled oscillator; PLL'in gerilimle ayarlanan
  osilatörü. {{sec:8}}
- **VCXO** — voltage-controlled crystal oscillator; PLL1'in temiz kristal
  referansı. {{sec:8}}
- **zero-IF** — sinyali doğrudan DC etrafına indiren alıcı mimarisi.
  {{sec:1}}
