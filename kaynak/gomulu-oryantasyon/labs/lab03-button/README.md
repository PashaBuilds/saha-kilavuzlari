# lab03-button — Görev 3: Butonu Oku (Polling)

## Ne yapar

SW19 butonunu (PS MIO22) sürekli polling ile okur, durumunu DS50 LED'ine
(PS MIO23) yansıtır ve **sayaç tabanlı debounce** kullanarak gerçek
basma sayısını UART'a basar.

Kartın 8 kullanıcı LED'i, 5 butonu ve DIP switch'i **PL pinlerindedir**
(Bölüm 2) — bitstream olmadan PS'ten erişilemezler. Bu yüzden bu görev
de yalnızca tek PS butonunu (SW19) ve tek PS LED'ini (DS50) kullanır;
8 LED'lik yürüyen ışık deseni, PL kapısı Bölüm 9 / Görev 7'de açılınca gelir.

`button_ps` modülü (`button_ps.h`), `_gorev-zinciri.md` sözleşmesindeki
imzalarla birebir aynıdır:

```c
int          buttonInit(void);
unsigned int buttonRead(void);
void         ledPsWrite(unsigned int uiState);
```

`src/uart_ps.h` ve `src/uart_ps.c`, **lab02-uart'tan birebir kopyadır**
(Görev 2 çözümü) — `_gorev-zinciri.md` sözleşmesi gereği kopya taşınır
ki her lab klasörü bağımsız derlenebilsin.

## Debounce nasıl çalışır

Mekanik bir butona basıldığında ya da bırakıldığında pin tek temiz bir
kenarla değişmez; birkaç milisaniye "seker" — kontak noktaları titreşir,
birkaç kez açılıp kapanır. Ham okumayı doğrudan saymak tek basışı 2-3
kez sayabilirdi.

`main.c`'deki çözüm **sayaç tabanlı debounce** kullanır: SW19 her 5
ms'de bir okunur (`DEBOUNCE_SAMPLE_INTERVAL_US`); okunan değer mevcut
kararlı durumdan farklıysa bir sayaç (`uiUnstableCount`) artırılır.
Ancak bu sayaç aynı yeni değeri **art arda 4 tur** (`DEBOUNCE_ESIK`,
yani 20 ms'lik kararlılık penceresi) gördüğünde geçiş "gerçek" kabul
edilir — LED güncellenir ve geçiş bir basışsa sayaç artırılır. Arada
kaçan tek bir sekme okuması sayacı sıfırlar ve hiçbir şey tetiklemez.

20 ms'lik pencere keyfî değil: tipik bir tactile butonun sekme süresi
birkaç ms ile birkaç on ms arasında değişir; 20 ms hem sekmeyi yutacak
kadar uzun hem de gerçek basışı fark edilir gecikme olmadan kaydedecek
kadar kısadır. Kendi butonunda daha uzun ya da kısa sekme gözlersen
`DEBOUNCE_ESIK`'i ayarlaman yeter.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform**u (.xsa, standalone) seç.
2. Yeni bir **boş uygulama** projesi aç ve bu platforma bağla.
3. Bu klasördeki `src/` altındaki dosyaları (`button_ps.h`,
   `button_ps.c`, `uart_ps.h`, `uart_ps.c`, `main.c`) projenin `src/`
   klasörüne kopyala.
4. Projeyi **build** et, sonra JTAG üzerinden karta yükle ve çalıştır.

## Beklenen çıktı

Terminal 115200-8N1 ile bağlıyken SW19'a birkaç kez basıp bırakınca:

```
--- TASK 3: Read Button (Polling) ---
Press SW19: DS50 turns on. Release: it turns off. Count is debounced.

press #1 - DS50 ON
release   - DS50 OFF
press #2 - DS50 ON
release   - DS50 OFF
```

DS50, buton basılı kaldığı sürece yanık kalır ve bıraktığın anda söner;
10 kez basarsan sayaç tam olarak `press #10` gösterir — sekme yüzünden
asla 11 ya da 12 değil.

## Polarite üzerine not

UG1271, SW19/DS50'nin active-high mı active-low mu olduğunu açıkça
söylemez (bkz. `content/_arastirma-ek-C.md` §C.1). Bu kod, dokümanın
geri kalanıyla tutarlı biçimde **active-high** kabulünü benimser: SW19
basılıyken 1 okunur, DS50'ye 1 yazılınca yanar. Kartında tersini
gözlersen (örn. buton basılı DEĞİLKEN LED yanıyorsa), değiştirilecek
tek yer `button_ps.c`'deki `buttonRead()` fonksiyonunun return
satırıdır.
