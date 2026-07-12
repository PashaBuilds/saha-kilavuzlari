# Bölüm 17 — Sistem Tasarım Kontrol Listesi

Bu bölüm, on altı bölümün damıtılmış halidir: yeni bir direct RF sampling
sistemi tasarlarken (ya da devraldığın bir tasarımı denetlerken) madde
madde üzerinden geçeceğin **tek sayfalık** liste. Her maddenin yanındaki
bölüm numarası, "neden?" sorusunun cevabına götürür. Liste, kart şeması
donmadan *önce* en değerlidir — buradaki maddelerin yarısı, sonradan
düzeltilmesi kart revizyonu gerektiren kararlardır.

## A — Frekans planı ({{sec:1}}, {{sec:2}})

- [ ] fs ve hedef bant seçildi; bant **tek Nyquist bölgesinde** kalıyor.
- [ ] HD2/HD3 katlanmaları hesaplandı; bant içine düşen yok.
- [ ] Interleaving spur aileleri (k·fs/M, k·fs/M ± f_in) kontrol edildi.
- [ ] Ön seçici filtre, seçilen bölgenin dışını yeterince bastırıyor;
      filtre ve frekans planı **birlikte** donduruldu.
- [ ] DAC tarafında imaj konumları (k·fs ± f) ve rekonstrüksiyon filtresi
      uyumlu; NRZ/mix-mode kararı verildi.
- [ ] Üretici frekans planlama aracının çıktısı proje dosyasına kondu.

## B — Jitter bütçesi ({{sec:2}}, {{sec:8}})

- [ ] Hedef SNR'dan izin verilen toplam jitter türetildi
      (SNR = −20·log10(2π·f_in·t_j) tersinden).
- [ ] ADC aperture jitter'ı (datasheet) + clock jitter'ı kareler toplamıyla
      birleştirildi; marj var.
- [ ] Clock chip'in datasheet jitter'ı **senin entegrasyon bandında**
      okundu (bant farkı tuzağı!).
- [ ] Zincirdeki her halkanın (cleaner → dağıtıcı/sentezleyici → iz)
      katkısı bütçeye işlendi.
- [ ] FPGA fabric clock'u hiçbir yerde converter clock yolunda değil.

## C — SYSREF stratejisi ({{sec:9}}, {{sec:10}})

- [ ] f_SYSREF, **tüm** cihazların LMFC/LEMC frekanslarının tam böleni
      (ve cihazların en düşük dahili bölücü frekansının).
- [ ] Tip seçildi: continuous / gapped / one-shot; one-shot ise hat
      **DC kuplajlı**.
- [ ] SYSREF, device clock ile aynı kaynaktan, bilinen fazla üretiliyor
      (DCLK/SYSREF çifti); izler eş uzunlukta.
- [ ] Her cihaza (tüm AFE'ler + FPGA) bir SYSREF dalı var.
- [ ] Setup/hold penceresi analizi yapıldı; gecikme ayar adımı (25 ps /
      3 ps sınıfı) pencereyi ortalamaya yetiyor.
- [ ] Senkronizasyon sonrası SYSREF'in susturulması planlandı (spur).
- [ ] SYSREF monitörü/windowing okuma ve loglama yazılım planında.

## D — Link parametreleri ({{sec:5}}, {{sec:7}}, {{sec:14}})

- [ ] M, N′, S, L seçildi; F = M·S·N′/(8·L) tam sayı.
- [ ] Lane rate hesaplandı (×10/8 veya ×66/64) ve **hem** AFE'nin **hem**
      GT'nin **hem** IP lisansının sınırları içinde.
- [ ] K/E kurallara uygun (B: ceil(17/F) ≤ K ≤ min(32, 1024/F), F·K %4;
      C: EMB tam sayıda frame).
- [ ] Subclass 1; CRC-12/FEC kararı iki uçta aynı.
- [ ] Parametre seti **tek kaynaktan** üretilip iki uca dağıtılıyor
      (elle iki kez girilmiyor).
- [ ] LMFC/LEMC frekansı hesaplandı ve SYSREF planıyla (C maddesi) tutarlı.

## E — FPGA / kart yerleşimi ({{sec:14}})

- [ ] Lane sayısı quad planına oturuyor; lane-kanal eşlemesi belgelendi.
- [ ] Refclk pinleri doğru quad'da; komşu paylaşım kuralı (±2 quad, aynı
      SLR) sağlanıyor; **>16.375 Gb/s ise refclk lokal**.
- [ ] Refclk frekansı GT Wizard'ın desteklediği ve clock chip'in
      üretebildiği ortak küme içinden seçildi.
- [ ] Core clock kaynağı belirlendi (lane rate/66 hesabıyla) ve SYSREF bu
      domain'e senkron örneklenebiliyor.
- [ ] SYNC~ (B linkleri) polarite/standart doğru; loopback portu
      (CH[x]_LOOPBACK) tasarıma bağlandı ({{sec:16}}).

## F — Reset ve init sırası ({{sec:15}})

- [ ] Beş perdelik sıra yazılımda durum makinesi olarak kodlandı.
- [ ] Her kilit bayrağı için bekleme + zaman aşımı + loglama var.
- [ ] GT reset'i, refclk doğrulanmadan bırakılmıyor.
- [ ] AFE kalibrasyonlarının tamamlanması bekleniyor.
- [ ] SYSREF tetiği, linkler kurulup yakalama modları ayarlandıktan sonra.
- [ ] Her perde sonunda durum register'ları loglanıyor (sağlıklı imza).

## G — Doğrulama ve izleme ({{sec:10}}, {{sec:16}})

- [ ] SYSREF-LMFC/LEMC faz register'ları sıfır okunarak hiza kanıtlanıyor.
- [ ] RBD/buffer release marjı ölçüldü; pencere ortasında.
- [ ] CRC/kod hata sayaçları çalışma boyunca izleniyor (eşik + alarm).
- [ ] Sıcaklık taraması yapıldı: SYSREF penceresi, eye scan, CRC.
- [ ] Çok kanallı sistemde kanal-arası faz, güç çevrimleri boyunca
      tekrarlanabilir (DL kanıtı).
- [ ] IBERT/eye scan erişimi üretim kartında da mümkün (debug kapısı).

Kısa listenin uzun versiyonu bu dokümanın kendisidir. Sıradaki iki bölüm
başvuru içindir: terim sözlüğü ve kaynakça.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

Bu bölüm derlemedir; her madde, yanında verilen bölümün kaynaklarına
dayanır. Toplu liste: {{sec:19}}.

</details>
