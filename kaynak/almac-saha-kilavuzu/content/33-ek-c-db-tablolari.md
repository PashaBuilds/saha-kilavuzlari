# Ek C — dB ve Hızlı Hesap Tabloları
::meta onkosul= acar= blok= rota=

Sahada hesap makinesi açmadan önce bakılacak tablolar. Tümü {{bolum:1}}'deki
tanımlardan türetilmiştir.

## Oran ↔ dB ezber kartı

| Güç oranı | dB (10·log) | Gerilim oranı | dB (20·log) |
|---|---|---|---|
| ×1 | 0 | ×1 | 0 |
| ×1.26 | 1 | ×1.12 | 1 |
| ×2 | 3.01 | ×1.41 (√2) | 3.01 |
| ×4 | 6.02 | ×2 | 6.02 |
| ×10 | 10 | ×3.16 | 10 |
| ×100 | 20 | ×10 | 20 |
| ×1000 | 30 | ×31.6 | 30 |
| ×10⁶ | 60 | ×1000 | 60 |
| ×½ | −3.01 | ×0.707 | −3.01 |
| ×0.1 | −10 | ×0.316 | −10 |

Kural: dB'ler toplanır, oranlar çarpılır. 3 dB + 10 dB = 13 dB ≙ ×2 · ×10 = ×20.
Her 6 dB gerilimi ikiye katlar, gücü dörde; her ADC biti 6.02 dB'dir.

## dBm ↔ mW ↔ Vrms ↔ Vpp (50 Ω)

| dBm | Güç | Vrms | Vpp | Tipik yer |
|---|---|---|---|---|
| +30 | 1 W | 7.07 V | 20 V | küçük verici çıkışı |
| +10 | 10 mW | 707 mV | 2.0 V | ADC tam ölçek (büyük) |
| +4 | 2.5 mW | 354 mV | 1.0 V | **referans ADC tam ölçeği** |
| 0 | 1 mW | 224 mV | 632 mV | sinyal üreteci varsayılanı |
| −10 | 100 µW | 70.7 mV | 200 mV | LO seviyesi (bazı mixer'ler) |
| −30 | 1 µW | 7.07 mV | 20 mV | güçlü alınan sinyal |
| −60 | 1 nW | 224 µV | 632 µV | **referans senaryo giriş darbesi** |
| −68 | 158 pW | 89 µV | 252 µV | **referans hassasiyet (MDS)** |
| −83 | 5 pW | 15.8 µV | 45 µV | **referans gürültü tabanı (300 MHz)** |
| −111 | 8 fW | 0.63 µV | 1.8 µV | gürültü tabanı, 2 MHz, NF 0 |
| −174 | 4 zW | — | — | kTB, 1 Hz, 290 K |

Dönüşüm: $P_{mW} = 10^{dBm/10}$, $V_{rms} = sqrt{P_W · 50}$, $V_{pp} = 2 sqrt{2} · V_{rms}$.

## Bant genişliği → gürültü tabanı (NF = 0 dB)

| B | 10·log(B) | Taban (dBm) | Örnek |
|---|---|---|---|
| 1 Hz | 0 | −174 | tanım |
| 1 kHz | 30 | −144 | ses bandı |
| 1 MHz | 60 | −114 | dar IF |
| 2 MHz | 63 | −111 | 1 µs darbe ana lobu |
| 20 MHz | 73 | −101 | geniş IF |
| 300 MHz | 84.8 | −89.2 | **DDC çıkışı (NF 6 ile −83.2)** |
| 1200 MHz | 90.8 | −83.2 | ADC Nyquist bandı (2400 MSPS) |
| 4 GHz | 96 | −78 | geniş bant EH almacı |

## Zaman ↔ frekans ↔ mesafe

| Büyüklük | Değer | Karşılığı |
|---|---|---|
| 1 µs darbe | ana lob null–null | 2 MHz |
| 1 µs darbe | −3 dB bant genişliği | ≈ 0.89 MHz |
| 1 µs | ışık yolu (tek yön) | 300 m |
| 1 ns | ışık yolu | 30 cm |
| 3.33 ns | 300 MSPS'te 1 örnek | 1 m |
| 1 ms PRI | belirsiz menzil (radar) | 150 km |
| 293 kHz FFT bin | 1024 nokta @ 300 MSPS | 3.41 µs gözlem |

## Bit ↔ dinamik aralık

| Bit | 6.02·N + 1.76 | Kod sayısı | LSB (1 Vpp FS) |
|---|---|---|---|
| 8 | 49.9 dB | 256 | 3.9 mV |
| 10 | 62.0 dB | 1 024 | 0.98 mV |
| 12 | 74.0 dB | 4 096 | 244 µV |
| 14 | **86.0 dB** | 16 384 | 61 µV |
| 16 | 98.1 dB | 65 536 | 15 µV |
| 18 | 110.1 dB | 262 144 | 3.8 µV |

## Pfa ↔ eşik (Rayleigh zarf, σ birimi)

| Pfa | T/σ | 20·log(T/σ) | 300 MSPS'te yanlış alarm/s |
|---|---|---|---|
| 10⁻³ | 3.72 | 11.4 dB | 300 000 |
| 10⁻⁴ | 4.29 | 12.7 dB | 30 000 |
| 10⁻⁶ | **5.26** | 14.4 dB | 300 |
| 10⁻⁸ | 6.07 | 15.7 dB | 3 |
| 10⁻¹⁰ | 6.79 | 16.6 dB | 0.03 |

## CA-CFAR çarpanı α (kare yasa)

| N \ Pfa | 10⁻³ | 10⁻⁴ | 10⁻⁶ | 10⁻⁸ |
|---|---|---|---|---|
| 8 | 11.2 | 16.4 | 36.6 | 72.0 |
| 16 | 8.7 | 12.0 | **21.9** | 36.6 |
| 32 | 7.7 | 10.2 | 17.0 | 25.6 |
| 64 | 7.3 | 9.5 | 15.0 | 21.7 |
| ∞ (ideal) | 6.9 | 9.2 | 13.8 | 18.4 |

Son satır −ln Pfa'dır: N büyüdükçe α ona yaklaşır; aradaki fark **CFAR kaybı**dır.
