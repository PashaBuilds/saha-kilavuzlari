# Ek D — Pencere Fonksiyonları Tablosu
::meta onkosul= acar= blok= rota=

Değerler bu kılavuzun DSP çekirdeğiyle (N = 1024, 16× sıfır doldurmalı
DTFT) hesaplanmıştır; literatürdeki tablolarla (harris 1978) ±0.1 dB içinde
örtüşür. Tanımlar {{bolum:19}}'da.

| Pencere | −3 dB ana lob (bin) | En yüksek yan lob (dB) | ENBW (bin) | Coherent gain | CG (dB) | Scalloping kaybı (dB) |
|---|---|---|---|---|---|---|
| Dikdörtgen | 1.00 | −13.3 | 1.000 | 1.000 | 0.00 | 3.92 |
| Hann | 1.50 | −31.5 | 1.500 | 0.500 | −6.02 | 1.42 |
| Hamming | 1.38 | −42.7 | 1.363 | 0.540 | −5.35 | 1.75 |
| Blackman | 1.75 | −58.1 | 1.727 | 0.420 | −7.54 | 1.10 |
| Blackman-Harris (4 terim) | 2.00 | −92.0 | 2.004 | 0.359 | −8.90 | 0.83 |
| Kaiser β = 8 | 1.63 | −58.7 | 1.667 | 0.435 | −7.22 | 1.18 |
| Chebyshev −80 dB | 1.75 | −80.0 | 1.743 | 0.414 | −7.66 | 1.09 |
| Flat-top | 3.75 | −93* | 3.770 | 0.216 | −13.33 | 0.01 |

\* Flat-top penceresinin ana lobu o kadar geniştir ki yan lob ölçümü ilk
dipten sonra başlar; pratik değer üretici tanımına göre −70…−95 dB arasında verilir.

## Nasıl okunur

- **Ana lob genişliği** iki yakın tonu ayırma yeteneğidir: dikdörtgen en dar, flat-top en geniş.
- **En yüksek yan lob** güçlü bir tonun yanında zayıf tonu görebilme sınırıdır.
- **ENBW** pencerenin gürültüyü kaç bin genişliğinde topladığıdır; gürültü tabanı ENBW ile yükselir (Hann: +1.76 dB).
- **Coherent gain** pencerenin tepe genliği ne kadar düşürdüğüdür; spektrumu dBFS'e ölçeklerken bununla telafi edilir.
- **Scalloping kaybı** tonun iki bin arasına düşmesinin en kötü kaybıdır; genlik doğruluğu için flat-top, tespit için Hann/Kaiser.

## Seçim özeti

| İhtiyaç | Öneri |
|---|---|
| Yakın iki tonu ayırmak | Dikdörtgen (koherent örneklemede) ya da Hamming |
| Güçlünün yanında zayıf sinyal | Blackman-Harris, Chebyshev, Kaiser β ≥ 8 |
| Genlik doğruluğu (kalibrasyon) | Flat-top |
| Genel amaçlı tespit / spektrogram | Hann (referans senaryo), %50 overlap |
| Ayarlanabilir tek pencere | Kaiser (β ile yan lob ↔ ana lob takası) |
