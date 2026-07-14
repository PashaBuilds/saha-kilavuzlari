# lab03-buton — GÖREV 3: Buton Oku (Polling)

## Ne yapar

SW19 butonunu (PS MIO22) sürekli sorgulama (polling) ile okur, durumunu
DS50 LED'ine (PS MIO23) yansıtır ve **sayaç-tabanlı debounce** ile gerçek
basma sayısını UART'a basar.

Karttaki 8 kullanıcı LED'i, 5 buton ve DIP switch **PL pinlerindedir**
(Bölüm 2) — bitstream olmadan PS'ten erişilemezler. Bu yüzden bu görevde
de yalnızca tek PS butonu (SW19) ve tek PS LED'i (DS50) kullanılıyor;
8 LED'lik yürüyen ışık Bölüm 9 / Görev 7'de PL kapısı açılınca geliyor.

`buton_ps` modülü (`buton_ps.h`), `_gorev-zinciri.md` sözleşmesindeki
imzalarla birebir:

```c
int          buttonInit(void);
unsigned int buttonRead(void);
void         ledPsWrite(unsigned int uiState);
```

`src/uart_ps.h` ve `src/uart_ps.c`, **lab02-uart'tan birebir kopyadır**
(GÖREV 2'nin çözümü) — her lab klasörünün bağımsız derlenebilmesi için
`_gorev-zinciri.md` gereği kopya taşınır.

## Debounce nasıl çalışıyor

Mekanik bir buton bastığın/bıraktığın anda pini tek bir temiz kenar gibi
değil, birkaç milisaniye süren bir "sıçrama" (bounce) ile değiştirir —
temas noktaları titreşerek birkaç kez açılıp kapanır. Ham okumayı doğrudan
sayarsan bir basış 2-3 kez sayılabilir.

`main.c`'deki çözüm **sayaç-tabanlı debounce** kullanır: her 5 ms'de bir
SW19 okunur (`DEBOUNCE_ORNEK_ARALIGI_US`); okunan değer mevcut kararlı
durumdan farklıysa bir sayaç (`uiUnstableCount`) artırılır. Bu sayaç
**4 ardışık turda** (`DEBOUNCE_ESIK`, yani 20 ms'lik kararlılık penceresi)
aynı yeni değeri görürse geçiş "gerçek" kabul edilir, LED güncellenir ve
(basılma yönündeyse) sayaç artırılır. Ara sıra dönen tek bir sıçrama
okuması sayacı sıfırlar ve hiçbir şeyi tetiklemez.

20 ms'lik pencere gelişigüzel değil: tipik tacil buton sıçrama süresi
birkaç ms ile birkaç onlarca ms arasındadır; 20 ms hem sıçramayı
yutacak kadar uzun hem de gerçek bir basışı gözle fark edilir gecikmeden
yakalayacak kadar kısa. Kendi butonunda daha uzun/kısa sıçrama
gözlemlersen `DEBOUNCE_ESIK`'i değiştirmen yeterli.

## Nasıl derlenir

Vitis Unified IDE'de:

1. Ekibin sağladığı hazır **platform** (.xsa, standalone) seçilir.
2. Yeni bir **boş (empty) uygulama** projesi açılır ve bu platforma bağlanır.
3. Bu klasördeki `src/` altındaki dört dosya (`buton_ps.h`, `buton_ps.c`,
   `uart_ps.h`, `uart_ps.c`, `main.c`) projenin `src/` klasörüne kopyalanır.
4. Proje derlenir (Build) ve JTAG üzerinden karta yüklenip çalıştırılır.

## Beklenen çıktı

Terminal 115200-8N1 ayarıyla bağlıyken, SW19'a birkaç kez basıp
bıraktığında:

```
--- GOREV 3: Buton Oku (Polling) ---
SW19'a bas: DS50 yanar. Birak: soner. Sayac debounce'lu.

basma #1 - DS50 YANDI
birakma    - DS50 SONDU
basma #2 - DS50 YANDI
birakma    - DS50 SONDU
```

Butona basılı tuttuğun sürece DS50 yanık kalır, bıraktığın anda söner;
10 kez basarsan sayaç tam `basma #10` der — sıçrama yüzünden 11 ya da 12
demez.

## Polarite hakkında bir not

UG1271, SW19/DS50'nin aktif-yüksek mi aktif-düşük mü olduğunu açıkça
yazmıyor (bkz. `content/_arastirma-ek-C.md` §C.1). Bu kod, dokümanın
geri kalanıyla tutarlı olarak **aktif-yüksek** kabul ediyor: SW19
basılıyken 1 okunur, DS50'ye 1 yazılınca yanar. Kartında tersini
gözlemlersen (LED'in basılı DEĞİLKEN yanması gibi) tek değişiklik yeri
`buton_ps.c`'deki `buttonRead()`'in dönüş satırıdır.
