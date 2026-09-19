# Ek B — Formül Kartı
::meta onkosul= acar= blok= rota=

Kılavuzdaki bütün formül kartları, numara sırasıyla. Numaraya tıklayınca
kartın kendisine (sembol tablosu ve referans senaryodaki sayısal örnekle)
gidersin. Formüller derleme sırasında bölümlerden toplanır; metin ile bu
liste birbirinden kopamaz.

{{formul-dizini}}

## En sık kullanılan on formül (ezber kartı)

| Ne | Formül | Referans senaryoda |
|---|---|---|
| Termal gürültü tabanı | $N_0 = −174 + 10·log_{10}(B) + NF$ dBm | B = 300 MHz, NF = 6 → {{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm |
| Hassasiyet (MDS) | $MDS = N_0 + SNR_{min}$ | +15 dB → {{s:turetilmis_beklenen.hassasiyet_dbm}} dBm |
| Friis kaskadı | $F = F_1 + frac{F_2 − 1}{G_1} + frac{F_3 − 1}{G_1 G_2} + …$ | LNA 20 dB / 2 dB + mixer 10 dB → {{s:turetilmis_beklenen.friis_ornek_db}} dB |
| İdeal kuantizasyon SNR'ı | $SNR = 6.02·N + 1.76$ dB | N = 14 → {{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB |
| Jitter SNR'ı | $SNR_j = −20·log_{10}(2π f_{in} σ_j)$ | 1 GHz, 100 fs → {{s:turetilmis_beklenen.jitter_snr_1ghz_100fs_db}} dB |
| İşlem kazancı | $PG = 10·log_{10}(f_s / 2B)$ | 2400 MSPS → 300 MHz → {{s:turetilmis_beklenen.islem_kazanci_1200_300_db}} dB |
| NCO ayar sözcüğü | $FTW = f_{out}/f_s · 2^N$ | 600/2400 · 2^32 = {{s:ddc.ftw_hex}} |
| FFT bin genişliği | $Δf = f_s / N$ | 300 MSPS / 1024 = {{s:turetilmis_beklenen.fft_bin_khz}} kHz |
| Rayleigh zarf eşiği | $T = σ sqrt{−2 ln P_{fa}}$ | Pfa = 10⁻⁶ → {{s:turetilmis_beklenen.rayleigh_esik_sigma}} σ |
| CA-CFAR çarpanı | $α = N (P_{fa}^{−1/N} − 1)$ | N = 16, Pfa = 10⁻⁶ → {{s:turetilmis_beklenen.ca_cfar_alfa}} |
