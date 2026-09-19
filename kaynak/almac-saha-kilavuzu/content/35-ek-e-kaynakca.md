# Ek E — Kaynakça ve İleri Okuma
::meta onkosul= acar= blok= rota=

Bu kılavuz yalnızca açık literatüre dayanır. Aşağıdaki eserler anlatımın
omurgasını oluşturur; her birinin yanında hangi bölümlerin ona yaslandığı
yazılıdır. Künyeler yazarın bildiği baskıya göredir; basım yılı ve yayınevi
yeni baskılarda değişmiş olabilir.

## Almaç ve EH

- **J. B.-Y. Tsui**, *Digital Techniques for Wideband Receivers*, 2. baskı, SciTech/Artech House. — Sayısal almaç mimarileri, kanallaştırma, monobit, frekans ölçümü. Bölüm 7, 17, 20, 25.
- **J. B.-Y. Tsui**, *Microwave Receivers with Electronic Warfare Applications*, SciTech. — CVR, IFM, süperhet, dinamik aralık, EH almaç gereksinimleri. Bölüm 5, 6, 7.
- **R. G. Wiley**, *ELINT: The Interception and Analysis of Radar Signals*, Artech House. — PDW, parametre ölçümü, PRI analizi, deinterleaving. Bölüm 3, 24–27.
- **P. E. Pace**, *Detecting and Classifying Low Probability of Intercept Radar*, 2. baskı, Artech House. — LPI dalga biçimleri, zaman–frekans analizi, almaç hassasiyeti. Bölüm 3, 20.
- **D. Adamy**, *EW 101 / EW 102*, Artech House. — dB aritmetiği, almaç hassasiyeti, POI sezgisi. Bölüm 1, 4.

## Radar sinyal işleme

- **M. A. Richards**, *Fundamentals of Radar Signal Processing*, 2. baskı, McGraw-Hill. — Tespit teorisi, CFAR, Doppler, eşlenik filtre. Bölüm 21–23.
- **M. I. Skolnik**, *Introduction to Radar Systems*, 3. baskı, McGraw-Hill. — Radar denklemi, almaç gürültüsü, tespit. Bölüm 4, 21.
- **M. A. Richards, J. A. Scheer, W. A. Holm (ed.)**, *Principles of Modern Radar: Basic Principles*, SciTech. — Almaç mimarisi, ADC gereksinimleri, CFAR ailesi. Bölüm 7, 9, 23.
- **W. Albersheim**, "A closed-form approximation to Robertson's detection characteristics", *Proc. IEEE*, 1981. — Pd/Pfa/SNR yaklaşımı. Bölüm 21.

## Sayısal sinyal işleme

- **R. G. Lyons**, *Understanding Digital Signal Processing*, 3. baskı, Prentice Hall. — DFT sezgisi, pencereleme, kuantizasyon, CIC, DDC. Bölüm 12, 14–19.
- **f. j. harris**, *Multirate Signal Processing for Communication Systems*, Prentice Hall. — Polyphase, halfband, CIC, kanallaştırma. Bölüm 16, 17.
- **f. j. harris**, "On the Use of Windows for Harmonic Analysis with the Discrete Fourier Transform", *Proc. IEEE*, 1978. — Pencere metrikleri (Ek D bu makaleyle karşılaştırılmıştır). Bölüm 19.
- **E. Hogenauer**, "An Economical Class of Digital Filters for Decimation and Interpolation", *IEEE Trans. ASSP*, 1981. — CIC filtresi. Bölüm 16.
- **A. V. Oppenheim, R. W. Schafer**, *Discrete-Time Signal Processing*, 3. baskı, Pearson. — Temel teori. Bölüm 2, 16, 18.
- **U. Meyer-Baese**, *Digital Signal Processing with Field Programmable Gate Arrays*, Springer. — FPGA'da DDS/NCO, CORDIC, FIR, FFT. Bölüm 12–16, 20.

## Veri dönüştürme

- **W. Kester (ed.)**, *The Data Conversion Handbook*, Analog Devices / Newnes. — ADC mimarileri, SNR/SFDR/ENOB, jitter, dither. Bölüm 9, 10.
- **Analog Devices MT-serisi tutorial'lar**: MT-001 (ENOB), MT-003 (SNR/SINAD), MT-008 (jitter), MT-085/086 (DDS). Bölüm 9, 14.
- **AMD/Xilinx**, *Zynq UltraScale+ RFSoC RF Data Converter* ürün kılavuzu (PG269) ve veri sayfası (DS926). Bölüm 10, 11. — Sayısal değerler bu kılavuzda doğrulanmamıştır; güncel belgeye bakın.
- **Texas Instruments** ve **Analog Devices** RF-sampling ADC uygulama notları (ör. TI SLAA617 *Understanding aliasing in RF sampling*, ADI AN-756 *Sampled Systems and the Effects of Clock Phase Noise and Jitter*). Bölüm 8, 9.
- **JEDEC**, JESD204B (2011) ve JESD204C (2017) standart özetleri. Bölüm 11.

## Bu serideki kardeş kılavuz

- **Doğrudan RF Örnekleme ve Ön Uç Tasarımı — Saha Kılavuzu** ({{rf:|raf sayfasından}}). Örnekleme teoremi, Nyquist bölgeleri, JESD204B/C, SYSREF, deterministik gecikme ve clocking bu kılavuzda yalnızca hatırlatma düzeyindedir; derin anlatım oradadır. Bölüm 8, 9, 11'deki bağlantılar doğrudan ilgili başlıklara gider.

## Bir sonraki adım

PDW üretiminden sonrasını (deinterleaving, emiter tanımlama, kütüphane
eşleme) derinlemesine öğrenmek için Wiley'nin *ELINT*'i ile başla; radar
tarafına geçmek için Richards'ın *Fundamentals*'ı; FPGA gerçeklemesinde
ustalaşmak için harris'in *Multirate*'i ve Meyer-Baese. Ders kitaplarını
okurken bu kılavuzun referans senaryosunu yanında tut: her formülü 2400 MSPS,
14 bit, 1 µs darbe ile bir kez sayıya dökmek, formülü ezberden bilgiye çevirir.
