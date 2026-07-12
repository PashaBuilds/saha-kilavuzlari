# Bölüm 2 — ADC/DAC Kavramları

Datasheet'in "AC performans" sayfasını aç: SNR, SFDR, ENOB, NSD, IMD3...
Bu metrik ormanı gözünü korkutmasın; hepsi tek soruya cevap verir: *ADC'nin
ürettiği sayılara ne kadar güvenebilirim?* Gömülü yazılımcı olarak bu
bölümü iki nedenle okuyorsun. Birincisi, {{sec:3}}'te ve {{sec:5}}'te
yapacağımız veri hızı ve link parametre hesapları bu kavramların (özellikle
çözünürlük ve N′) üstüne kurulu. İkincisi, sahada spektrumda bir tepecik
gördüğünde "bu sinyal mi, spur mu, gürültü mü?" sorusunu bu bölümdeki
kavramlarla cevaplayacaksın. Ve bu bölümün sonunda, dokümanın kalbine giden
kapı açılacak: clock jitter'ının SNR'ı nasıl katlettiğini gördüğünde,
{{sec:8}}'deki clock chip'lerin neden bu kadar önemsendiğini anlayacaksın.

::: ogren
- Çözünürlük, LSB ve kuantalama gürültüsü; 6.02N + 1.76 formülü
- SNR / SINAD / ENOB / SFDR / NSD / IMD3 — her birinin ne söylediği
- Jitter–SNR ilişkisi: formül, gerçek GHz/fs sayılarıyla tablo
- Interleaved ADC mimarisi ve interleaving spur'larını tanıma
- DAC tarafı: imajlar, sinc roll-off, mix-mode, rekonstrüksiyon filtresi
:::

## Çözünürlük ve kuantalama gürültüsü

N bitlik bir ADC, tam ölçek (full scale, FS) giriş aralığını 2^N basamağa
böler; bir basamağa **LSB** (least significant bit) denir. Örnekleme anındaki
gerçek gerilim ile en yakın basamak arasındaki fark — kuantalama hatası —
her örnekte ±LSB/2 aralığında rastgele dağılır ve spektrumda beyaz gürültü
gibi görünür. Tam ölçekli bir sinüs için bu gürültünün sinyale oranı meşhur
formülü verir:

```text
SNR_ideal = 6.02·N + 1.76 dB
```

14-bit ideal ADC: 6.02·14 + 1.76 = **86.0 dB**. 12-bit: 74.0 dB. 16-bit:
98.1 dB. Bit başına ~6 dB — bu değiş tokuş tablosunu aklında tut, birazdan
jitter bunu nasıl yediğini göreceğiz.

::: not
GS/s sınıfı RF ADC'lerin datasheet SNR'ı ideal değerin belirgin altındadır
(termal gürültü, jitter, distorsiyon). 14-bit bir RF ADC'de ~86 değil,
koşullara göre 55–65 dBFS civarı SNR görmek normaldir. "Kaç bit yazıyorsa o
kadar bit alırım" beklentisi, RF ADC dünyasına ilk gelenlerin klasik
şaşkınlığıdır — gerçek cevap ENOB'dadır, birazdan geliyor.
:::

## Metrik ormanında yol bulmak

Hepsi genelde dBFS (tam ölçeğe göre dB) cinsinden verilir; sinyal gücünü
tam ölçeğe göre ölçmek, farklı ADC'leri karşılaştırılabilir kılar.

| Metrik | Açılımı | Ne söyler | Sana ne söyler |
|---|---|---|---|
| SNR | signal-to-noise ratio | Sinyal / toplam gürültü (spur'lar hariç) | Gürültü tabanının yüksekliği; hassasiyet |
| SINAD (SNDR) | signal-to-noise-and-distortion | Sinyal / (gürültü + distorsiyon) | "Her şey dahil" gerçek kalite |
| ENOB | effective number of bits | (SINAD − 1.76)/6.02 | Kaç bitlik *gerçek* çözünürlük aldığın |
| SFDR | spurious-free dynamic range | Sinyal ile en büyük spur arası mesafe | Zayıf sinyali spur'dan ayırt edebilme |
| NSD | noise spectral density | 1 Hz başına gürültü, dBFS/Hz | Geniş bant sistemde gürültüyü bant genişliğinden bağımsız karşılaştırma |
| IMD3 | third-order intermodulation | İki ton girince 2f1−f2, 2f2−f1'de doğan ürünler | Dolu bantta kanalların birbirini kirletmesi |

Birkaçı üzerinde duralım:

**ENOB** gerçeğin özetidir: SINAD'ı 58 dB olan bir ADC'nin ENOB'u
(58 − 1.76)/6.02 = **9.3 bit**'tir — üstünde "14-bit" yazsa bile. Kalan ~5
bit, gürültü ve distorsiyona gitti. Bu kötü bir şey değil; RF frekansında
9 etkin bit ciddi bir başarıdır. Ama {{sec:5}}'te N′ (iletilen bit sayısı)
seçerken, taşıdığın bitlerin kaçının "gerçek" olduğunu bilmek perspektif
kazandırır.

**NSD**, GS/s dünyasının en kullanışlı metriğidir çünkü SNR, ölçüldüğü bant
genişliğine bağlıdır; NSD değildir. İlişki:

```text
NSD ≈ −( SNR + 10·log10(fs/2) )   [dBFS/Hz]
```

Örnek: fs = 3 GS/s, SNR = 58 dBFS → NSD = −(58 + 10·log10(1.5×10⁹)) =
−(58 + 91.8) = **−149.8 dBFS/Hz**. Bunun ikiz kardeşi **process gain**:
ilgilendiğin bant Nyquist bandından darsa, gürültünün çoğu bandının dışında
kalır ve dijital filtreleme (decimation, {{sec:3}}) onu atar:

```text
kazanç = 10·log10( (fs/2) / BW )
```

3 GS/s ADC'den 100 MHz'lik bant çekersen: 10·log10(1500/100) ≈ **11.8 dB**
bedava SNR. Oversampling + DDC kombinasyonunun sessiz kahramanlığı budur;
{{sec:3}}'te decimation'ı görünce hatırla.

**SFDR ve IMD3** debug metrikleridir: spektrumda beliren tek bir tepenin
"ADC'nin harmoniği mi, interleaving spur'u mu ({{fig:d10}} mantığıyla nereye
katlanmış), yoksa gerçekten havada olan bir sinyal mi" olduğuna karar
verirken bu kavramlarla düşünürsün.

## Jitter: SNR'ın sessiz katili

Şimdi dokümanın en önemli formüllerinden birine geliyoruz. ADC, sinyali
clock'un söylediği anda örnekler. Clock kenarı t_j kadar titrerse (jitter),
örnek *yanlış anda* alınır; sinyal o anda dV/dt hızıyla değişiyorsa, zaman
hatası **gerilim hatasına** dönüşür: ΔV ≈ (dV/dt)·t_j. Sinüs ne kadar
hızlıysa (frekans ne kadar yüksekse) dV/dt o kadar büyük — dolayısıyla aynı
jitter, yüksek giriş frekansında daha büyük hata üretir. Sonuç (yalnızca
jitter'dan gelen SNR tavanı):

```text
SNR_jitter = −20·log10( 2π · f_in · t_j )
```

Buradaki f_in **giriş sinyalinin frekansıdır, fs değil** — undersampling
yaparken 3 GHz'lik sinyalin jitter cezası 3 GHz üzerinden kesilir. Sayılarla
görelim (dB, yalnız jitter tavanı):

| t_j (rms) | f_in = 0.5 GHz | 1 GHz | 3 GHz | 6 GHz |
|---|---|---|---|---|
| 200 fs | 64.0 | 58.0 | 48.5 | 42.4 |
| 100 fs | 70.1 | 64.0 | 54.5 | 48.5 |
| 50 fs | 76.1 | 70.1 | 60.5 | 54.5 |
| 25 fs | 82.1 | 76.1 | 66.5 | 60.5 |

Tabloyu sindir: 3 GHz'te 200 fs jitter ile ADC'n kaç bitlik olursa olsun
**48.5 dB'den (≈7.8 ENOB)** iyisini göremezsin. 14-bit ADC parasını verdiysen
ve 60+ dB istiyorsan, 3 GHz girişte toplam jitter'ın ~50 fs altında olmak
zorunda. Frekans iki katına çıkınca tavan 6 dB düşer (~1 bit); jitter iki
katına çıkınca yine 6 dB. Kural basit, sonuçları acımasız.

İki kaynak birleşir: ADC'nin kendi iç **aperture jitter'ı** (datasheet'te
sabit, senin elinde değil) ve dışarıdan verdiğin **clock'un jitter'ı**
(tamamen senin — daha doğrusu clock chip'inin — elinde). Kareler toplamının
karekökü geçerlidir: t_toplam = √(t_aperture² + t_clock²). Dış clock 
jitter'ını aperture'ın altına indirmek, clock tasarımının hedefidir.

::: dikkat
Bu tablo, {{sec:8}}'in varlık sebebidir. "Clock'u FPGA'dan üretsem olmaz
mı?" sorusunun cevabı bu tablodadır: FPGA fabric clock'ları picosaniye
sınıfı jitter taşır — 3 GHz girişte ~30 dB SNR demektir. Device clock'un
neden özel bir jitter-temizleyici PLL zincirinden ({{sec:8}}) geldiğini,
faz gürültüsü grafiğinin nasıl "integrated jitter"a dönüştüğünü orada
göreceğiz.
:::

## Interleaved ADC: hız hilesi ve bedeli

Tek bir ADC çekirdeğini GS/s hızına itmenin fiziksel sınırları var. Çözüm,
M çekirdeği **sırayla** çalıştırmak (time-interleaving): her çekirdek fs/M
hızında örnekler, çıkışlar birleştirilir ve dışarıya fs hızında tek ADC gibi
görünür. Modern RF ADC'lerin hemen hepsi içeride interleaved'dir.

Bedeli: M çekirdek hiçbir zaman birebir aynı değildir. Üç uyumsuzluk türü,
spektrumda üç imza bırakır:

- **Offset uyumsuzluğu**: her çekirdeğin sıfır noktası farklıysa, çıkışta
  fs/M periyotlu bir desen oluşur → **k·fs/M** frekanslarında, giriş
  sinyalinden *bağımsız* sabit tonlar.
- **Kazanç uyumsuzluğu**: çekirdekler sinyali farklı büyütürse → sinyalin
  **k·fs/M ± f_in** konumlarında imajları doğar.
- **Zamanlama (skew) uyumsuzluğu**: çekirdeklerin örnekleme anları ideal
  ızgaradan kayıksa → yine **k·fs/M ± f_in** imajları (frekansla büyüyen
  şiddette).

Sayısal örnek: fs = 3 GS/s, içeride 4-yollu interleave (fs/M = 750 MHz),
f_in = 200 MHz. Offset tonlarını 750 ve 1500 MHz'te; kazanç/zamanlama
imajlarını 750 ± 200 (550 ve 950 MHz) ile 1500 ± 200 (1300 MHz; 1700,
katlanıp 1300'e iner) civarında ararsın. Spektrumda 550 MHz'te açıklanamayan
bir tepe gördüğünde artık ilk şüphen var.

**Yazılıma dokunduğu yer:** modern AFE'ler bu uyumsuzlukları çip içi
kalibrasyonla bastırır — ve o kalibrasyonu init sırasında çalıştıran,
tamamlanmasını bekleyen, bazen sıcaklık değişince tekrarlanmasını yöneten
şey senin kodundur ({{sec:15}}). "Kart soğukken spektrum temizdi, ısınınca
750 MHz ailesi yükseldi" şikâyeti duyarsan, kalibrasyon politikasına bak.

## DAC tarafı: aynanın öbür yüzü

Verici yolunda DAC, sayıları gerilime çevirir. İdeal DAC her örnekte sonsuz
ince bir darbe üretirdi; gerçek DAC, örneği bir sonraki örneğe kadar **tutar**
(zero-order hold, NRZ modu). Bu tutmanın iki spektral sonucu vardır:

**1) İmajlar.** Örneklenmiş sinyalin spektrumu, {{fig:d10}}'da gördüğün gibi
fs'in katları etrafında zaten periyodiktir; DAC çıkışında istediğin f
sinyalinin yanında **k·fs ± f** frekanslarında imajlar belirir. fs = 3 GS/s
ile 400 MHz üretirken 2.6 GHz ve 3.4 GHz'te de (zayıflamış) kopyalar
üretirsin. Bunları bastırmak **rekonstrüksiyon filtresinin** işidir — DAC
sonrası analog filtre; alıcıdaki anti-alias filtresinin ikizi.

**2) Sinc roll-off.** Tutma işlemi, spektrumu şu zarfla çarpar:

```text
|H(f)| = | sin(π·f/fs) / (π·f/fs) |
```

Bu zarf DC'de 0 dB, **fs/2'de −3.92 dB**'dir ve fs'te sıfıra iner. İki
pratik sonucu var: bant içinde kenara doğru kazanç düşer (çoğu AFE bunu
dijital "inverse sinc" filtresiyle düzeltir — init'te açman gereken bir blok
olabilir) ve 1. Nyquist bölgesi dışına çıkan imajlar doğal olarak zayıflar.

**Mix-mode**: peki DAC ile *doğrudan* 2. bölgede (fs/2..fs) sinyal üretmek
istersen? NRZ zarfı orada çok zayıftır. Mix-mode'da DAC, her örnek
periyodunun ikinci yarısında çıkışın işaretini ters çevirir; bu, zarfın
enerjisini 1. bölgeden 2. bölgeye kaydırır. RF DAC'lerin "C-band'e kadar
doğrudan sentez" iddialarının arkasındaki mekanizma budur. Yazılım tarafında
mix-mode bir **register seçimidir** ve frekans planının parçasıdır: yanlış
modda bant kenarında birkaç dB kayıp ya da beklenmedik güçte imaj görürsün.

::: saha
Verici spektrumunda "temiz tek ton bekliyordum, iki ton görüyorum"
vakalarının klasik sebebi imajdır: 2.9 GHz üretmeye çalışırken fs = 3 GS/s
ile 100 MHz'te (3.0 − 2.9) bir kardeş doğar; rekonstrüksiyon filtren onu
geçiriyorsa spektrum analizöründe ikisini birden görürsün. Çözüm yazılımda
değil frekans planındadır — ama ilk fark eden genelde yazılımcı olur.
:::

Artık örneklerin kalitesini ölçebiliyorsun. Sıradaki problem nicelik:
3 GS/s'de 16 bit üreten dört kanal, saniyede ~24 gigabayt demektir. Bu seli
kim taşıyacak? Önce çip içinde eritmeyi (DDC), sonra kalanını FPGA'ya
akıtmayı ({{sec:3}} sonu, JESD'in doğuşu) konuşalım.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- Analog Devices, MT-001: *Taking the Mystery out of the Infamous Formula
  "SNR = 6.02N + 1.76dB"* — kuantalama gürültüsü.
- Analog Devices, MT-003: *Understand SINAD, ENOB, SNR, THD, THD + N, and
  SFDR* — metrik tanımları.
- Analog Devices, MT-008: *Converting Oscillator Phase Noise to Time
  Jitter* ve ilgili notlar — jitter–SNR formülü.
- TI ve ADI time-interleaved ADC uygulama notları — interleaving spur
  mekanizmaları.
- TI/ADI RF DAC dokümantasyonu — sinc roll-off, mix-mode, imajlar.
- Toplu ve linkli liste: {{sec:19}}.

</details>
