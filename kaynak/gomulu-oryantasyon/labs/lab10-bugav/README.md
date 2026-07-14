# lab10-bugav — Bug Avı (Görev 10)

Bu klasördeki proje senden önceki stajyerden kaldı. Ekipten ayrılmadan
önce son işi buymuş: TTC0 tabanlı bir sayaç, SW19 butonu ve UART durum
satırları — kulağa tanıdık geliyor, çünkü Görev 4 ve Görev 5'in aynı
parçalarından kurulu. Kod **derleniyor** ve karta **yükleniyor**. Ama
projeyi çalıştırdığında dört yerinde bir şeylerin ters gittiğini
göreceksin.

Senden istenen: dedektif gibi davranmak. Belirtiye bakıp körlemesine kod
değiştirme; önce hangi silahın (printf, LED, debugger, lojik analizör —
Bölüm 11) hangi belirtiye uygun olduğuna karar ver, sonra izi sür.

> **Önce kendin bul.** Bu README sana **spesifikasyonu** ve **gözlenen
> belirtileri** veriyor, çözümü değil. Çözüme Bölüm 11'deki Görev 10
> kartının ipucu merdiveninden ya da bu klasördeki `COZUM.md`'den
> ulaşabilirsin — ama önce kendi başına en az yarım saat uğraşmadan oraya
> atlama. Asıl öğrenme, hatayı sen bulduğunda gerçekleşiyor.

## Proje yapısı

```
lab10-bugav/
├── README.md            (bu dosya)
├── COZUM.md              (4 hatanın tam çözümü — ipucu merdiveninin dibi)
└── src/
    ├── main.c            ana döngü, GIC kurulumu, sistem sağlık özeti
    ├── uart_ps.h/.c       PS UART0 için minimal sürücü (register seviyesi)
    ├── gpio_led_buton.h/.c  DS50 LED'i + SW19 butonu, kesme tabanlı
    ├── zamanlayici.h/.c   TTC0 kanal 0, saniyede bir kesme
    └── lscript.ld         stack/heap boyutlandırma bölümü (bkz. not aşağıda)
```

## Nasıl derlenir

Vitis'te yeni bir **application component** aç (platform: standalone,
işlemci: `psu_cortexa53_0`, boş şablon — Hello World'ü seçme, kendi
kaynaklarını kullanacaksın). `src/` altındaki tüm dosyaları projenin
kaynak klasörüne kopyala, derle. `lscript.ld`'yi projenin kendi linker
script'inin ilgili STACK/HEAP bölümüyle karşılaştır — Vitis senin için
platformdan tam bir `lscript.ld` üretir, buradaki dosya yalnızca bu
laboratuvarla ilgili kısmı gösteren bir özet.

## Spesifikasyon (beklenen davranış)

- **TTC0 kanal 0** ile saniyede bir UART'a `tick N` satırı basılır (N
  artan bir sayaç).
- **SW19** basıldığında UART'a `buton: M` satırı basılır (M toplam basış
  sayısı) ve **DS50** LED'i durum değiştirir (toggle).
- Sayaçlar (`tick` ve `buton`) her zaman doğru ve eksiksiz artar.
- Sistem saatlerce kesintisiz ve kararlı çalışır.

## Gözlenen belirtiler

Stajyerin bıraktığı notlarda şunlar yazıyor (senin doğrulaman gereken
şikayetler):

1. **"Optimizasyonlu derlemede buton hiç tepki vermiyor."** Debug
   derlemesinde (`-O0`) buton çalışıyor gibi görünüyor, ama release
   derlemesinde (`-O2`) SW19'a basıldığında hiçbir şey olmuyor.
2. **"Tick bazen sekiyor ya da geç geliyor."** `tick N` satırları çoğu
   zaman düzgün geliyor, ama arada bir sayı atlanıyor ya da satır beklenen
   zamandan gecikmeli çıkıyor — özellikle butona sık basıldığında.
3. **"DS50 bir kez yanıyor, bir daha hiç sönmüyor."** İlk buton basışında
   LED yanıyor, ama sonraki basışlarda sönmesi gerekirken yanık kalıyor.
4. **"Sistem birkaç dakika sonra rastgele çöküyor."** Bazen beş dakika,
   bazen yirmi dakika — kesin bir tetikleyici yok gibi görünüyor, ama
   sistem er ya da geç kilitleniyor ya da saçma değerler basmaya başlıyor.

## Görev

Bu dört belirdinin arkasındaki dört farklı kök nedeni bul, düzelt, her biri
için tek cümlelik bir kök neden yaz. Tam görev tanımı, başarı kriteri ve
kendini sınama soruları Bölüm 11'deki **Görev 10 — Bug Avı** kartında.
