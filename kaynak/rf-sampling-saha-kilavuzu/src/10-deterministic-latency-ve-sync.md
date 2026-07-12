# Bölüm 10 — Deterministic Latency ve Multi-Device Sync

Faz dizili bir radar düşün: 16 anten, 4 AFE, tek FPGA. Hedefin yönünü,
antenlere gelen dalganın **faz farkından** hesaplıyorsun — picosaniyeler
mertebesinde anlamlı bir bilgi. Şimdi kanallardan birinin verisi FPGA'ya
diğerlerinden bir multiframe geç gelse ve bu gecikme her açılışta değişse?
Yön hesabın çöp olur; daha kötüsü, laboratuvarda yaptığın kalibrasyon
sahadaki ilk yeniden açılışta geçersizleşir. Deterministic latency (DL),
tam bu kâbusa karşı JESD204'ün verdiği sözdür: **linkin gecikmesi sabittir
— açılıştan açılışa, karttan karta, sıcaklıktan sıcaklığa.** Bu bölümde o
sözün nasıl tutulduğunu ve birden çok çipin tek koherent makineye nasıl
dönüştüğünü göreceğiz.

::: ogren
- DL'nin tanımını ve gecikmenin nerelerde biriktiğini
- Buffer release mekanizmasını adım adım (W04)
- RBD'nin nasıl seçildiğini
- Multi-chip senkronizasyon akışını, NCO reset dahil (W05)
- DL'nin faz koherensi *olmadığını* — kalibrasyonun neden hâlâ gerektiğini
:::

## Gecikme nerede birikir?

Bir örneğin ADC'den FPGA kullanıcı lojiğine yolculuğundaki gecikme
bileşenleri: AFE'nin transport/link katmanları (deterministik — sabit sayıda
frame), SerDes ve kablo/iz yolu (fiziksel — sabit ama karttan karta farklı),
ve RX elastic buffer'da bekleme (işte bütün oyun burada). İlk ikisi zaten
sabittir; sorun, lane'lerin varış anlarının *tesadüfi* olmasıydı. 204'ün
hilesi, bu tesadüfü buffer'da yutup **okumayı takvime bağlamak**:

## Buffer release, adım adım

Mekanizmanın tamamı ({{fig:w04}}):

1. **SYSREF herkesi hizalar** ({{sec:9}}): TX ve RX'in LMFC/LEMC sayaçları
   artık aynı fazda atıyor. Bu adım olmadan gerisinin anlamı yok.
2. **TX, iletimi takvime bağlar**: ILAS (B'de) veya ilk EMB (C'de), TX'in
   LMFC/LEMC kenarında yola çıkar — {{fig:w02}}'de görmüştük.
3. **Lane'ler varır, buffer'lanır**: her lane'in verisi RX elastic
   buffer'ına yazılır. Varış anları lane'den lane'e, karttan karta farklı —
   umursamıyoruz.
4. **Release takvimle gelir**: RX, *kendi* LMFC kenarından RBD frame sonra
   tüm buffer'ları **aynı anda** okumaya başlar. Gecikme artık "LMFC kenarı
   + RBD" — yani takvim cinsinden sabit bir sayı. Lane'lerin tesadüfü
   buffer'da eridi.

![Elastic buffer release: erken gelen bekler, geç gelen yetişir; okuma herkes için LMFC + RBD anında başlar. Gecikme = takvim sabiti.](../diagrams/wavedrom/w04.json5)

Sonuç: uçtan uca gecikme, her açılışta aynı **tam sayıda frame**'dir.
Kablo değişse, sıcaklık kaysa, lane'lerin varış sırası değişse bile —
release anına kadar yetiştikleri sürece — gecikme değişmez.

## RBD seçimi: pencerenin ortasını bul

RBD (1..K frame) o "yetiştikleri sürece"nin ayar düğmesidir:

- **Çok küçük**: en geç lane henüz varmadan release anı gelir → boş buffer
  okunur, link çöker veya çöpe döner.
- **Çok büyük**: gereksiz bekleme → sisteme boşuna gecikme eklersin.
- **Sınırda**: en tehlikelisi — nominalde çalışır, sıcaklık/voltaj kayması
  bir lane'i release anının öbür tarafına itince gecikme bir LMFC periyodu
  atlar. "Determinizm" sessizce ölür; sistem çalışmaya devam ettiği için
  fark etmezsin.

Doğru yaklaşım ölçmektir: çoğu FPGA IP'si ve AFE, lane varış anlarını LMFC
kenarına göre raporlar. Tüm kartların, sıcaklık uçlarının en kötü değerini
al; release anını en geç varış ile bir sonraki LMFC kenarı arasındaki
pencerenin **ortasına** koy. Bu ölçüm ve hesap {{sec:17}}'deki kontrol
listesinin maddesidir; TI'ın SBAA543 notu yöntemin güzel bir anlatımıdır.

## Multi-chip senkronizasyon: orkestrayı kurmak

Tek link deterministik oldu; şimdi 4 AFE'li sistemi hizalayalım. Hedef:
tüm çiplerin örnekleme anları, sayaçları ve dijital yolları **tek bir
sistem** gibi davransın. Akış ({{fig:w05}}):

1. **Ortak zemin**: tüm AFE'lerin device clock'ları ve FPGA'nın GT
   refclk'i aynı clock chip zincirinden, bilinen faz ilişkisiyle üretilir
   ({{sec:11}}–{{sec:12}}'nin clock tree'leri). SYSREF de aynı kaynaktan
   herkese dağıtılır.
2. **Takvim hizası**: yazılım, tüm cihazları SYSREF yakalamaya hazırlar ve
   SYSREF'i tetikler (tipik olarak one-shot/gapped, {{sec:9}}). Doğrulama
   somuttur: cihazların "SYSREF ile LMFC/LEMC arasındaki faz" register'ları
   **sıfır** okuyana kadar hizalanmış sayılmazsın — ADI'nin çoklu-MxFE
   akışı bu kontrolü açıkça adım yapar. Artık tüm LMFC/LEMC'ler aynı fazda.
3. **Linkler kurulur**: her AFE-FPGA linki kendi CGS/ILAS'ını veya SH/EMB
   merdivenini tırmanır; buffer release'ler aynı takvime bağlandığı için
   tüm linklerin gecikmesi aynıdır.
4. **NCO'lar senkron sıfırlanır**: {{sec:3}}'te bırakılan ipucu — DDC/DUC
   NCO'larının fazı, akümülatörün başlama anına bağlıydı. Modern AFE'ler
   NCO reset'ini hizalanmış takvime bağlama modu sunar: "bir sonraki
   yakalanan SYSREF kenarında" veya ADI MxFE'nin master-slave akışındaki
   gibi "bir sonraki LEMC kenarında" sıfırla. Yazılım modu kurar, tetik
   gelir, tüm çiplerdeki tüm NCO'lar aynı âna hizalı faz-sıfırdan başlar.
   Artık dijital LO'lar da koherenttir.
5. **Doğrulama**: yazılım, SYSREF monitörlerini ({{sec:9}}), link
   durumlarını ve — nihai kanıt olarak — kanallar arası test sinyali faz
   ölçümünü kontrol eder.

![İki AFE + FPGA: SYSREF öncesi LEMC fazları rastgele; yakalanan kenardan sonra tüm takvimler kilit adımda.](../diagrams/wavedrom/w05.json5)

Sıra önemlidir ve tamamı **senin init kodundur**: clock'lar kararlı olmadan
SYSREF tetiklemek, NCO reset modunu kurmadan SYSREF'i susturmak, linkler
kurulmadan kalibrasyona başlamak — hepsi "bazen çalışan" sistemler üretir.
{{sec:15}}'te bu akışı adım adım bir init state machine'e döküyoruz.

## Deterministic latency ≠ faz koherensi

Son ve kritik dürüstlük. DL + senkron NCO'lar sana şunu verir: tüm
kanalların örnekleri **aynı örnek indeksinde, aynı dijital fazla** FPGA'ya
ulaşır. Ama antenden ADC'ye kadarki **analog** dünya hâlâ orada: kablo boyu
farkları, filtre grup gecikmeleri, LNA'ların birim farkları, balun
toleransları, çip içi analog yolların üretim dağılımı... Bunlar kanallar
arasına, JESD'in hiç göremeyeceği faz/genlik farkları ekler.

Yani: **DL, koherensin ön şartıdır; kendisi değildir.** Kanal eşleme
(faz/genlik) kalibrasyonu yine yapılır — test tonu enjekte edilir, kanallar
arası fark ölçülür, düzeltme katsayıları DSP'ye yazılır. DL'nin asıl
armağanı şudur: bu kalibrasyon değerleri **yarın da geçerlidir**, çünkü
dijital gecikmeler artık açılıştan açılışa değişmiyor. DL olmadan
kalibrasyon, her açılışta baştan yapılması gereken bir ritüele döner; DL
ile fabrikada bir kez yapılan bir işleme.

KISIM III bitti: clock kalitesini ({{sec:8}}), hizalama emrini ({{sec:9}})
ve determinizmin kuruluşunu gördün. Artık soyut dünyadan çıkıyoruz: bu
kavramların gerçek kartlarda — TI ve ADI zincirlerinde — ete kemiğe
bürünüşü.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- TI, SBAA543: *Determining Optimal Receive Buffer Delay in JESD204B* —
  RBD ölçüm ve seçim yöntemi.
- ADI, JESD204B subclass / deterministic latency makale serisi — DL
  tanımı ve mekanizması.
- ADI, Quad-MxFE multi-chip senkronizasyon kılavuzu (wiki.analog.com) —
  one-shot sync + NCO master-slave akışı, SYSREF-LEMC faz doğrulaması.
- ADI, *Power-Up Phase Determinism Using Multichip Synchronization
  Features...* teknik makalesi — DL ile faz koherensi ayrımı.
- Toplu ve linkli liste: {{sec:19}}.

</details>
