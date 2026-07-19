# lab10-bughunt — Görev 10: Hata Avı

Bu proje senden önceki stajyerden kaldı. Ekipten ayrılmadan önceki son
işiydi: TTC0 tabanlı bir sayaç, SW19 butonu ve UART durum satırları —
tanıdık geliyor, çünkü Görev 4 ve Görev 5 ile aynı parçalardan kurulu.
Kod **derleniyor** ve karta **yükleniyor**. Ama projeyi çalıştırınca
dört yerde bir şeylerin ters gittiğini göreceksin.

Senden istenen: dedektif gibi davran. Belirtiye bakıp körlemesine kod
değiştirme; önce hangi silahın (printf, LED, debugger, logic analyzer —
Bölüm 11) hangi belirtiye uyduğuna karar ver, sonra izi sür.

> **Önce kendin bul.** Bu README sana çözümü değil, **spesifikasyonu**
> ve **gözlenen belirtileri** verir. Çözüme Bölüm 11'deki Görev 10
> kartının ipucu merdiveninden ya da bu klasördeki `SOLUTION.md`'den
> ulaşabilirsin — ama en az yarım saat kendi başına didinmeden oraya
> atlama. Gerçek öğrenme, hatayı kendin bulduğunda gerçekleşir.

## Proje yapısı

```
lab10-bughunt/
├── README.md            (bu dosya)
├── SOLUTION.md              (4 hatanın tam çözümü — ipucu merdiveninin dibi)
└── src/
    ├── main.c            ana döngü, GIC kurulumu, sistem sağlık özeti
    ├── uart_ps.h/.c       PS UART0 için minimal sürücü (register seviyesi)
    ├── gpio_led_button.h/.c  DS50 LED + SW19 buton, interrupt tabanlı
    ├── timer.h/.c   TTC0 kanal 0, saniyede bir interrupt
    └── lscript.ld         stack/heap boyutlandırma bölümü (aşağıdaki nota bak)
```

## Nasıl derlenir

Vitis'te yeni bir **application component** aç (platform: standalone,
işlemci: `psu_cortexa53_0`, boş şablon — Hello World seçme, kendi
kaynaklarını kullanacaksın). `src/` altındaki tüm dosyaları projenin
kaynak klasörüne kopyala ve build et. Vitis, platformdan senin için
eksiksiz bir `lscript.ld` üretir; buradaki dosya o script'in yalnızca
bu lab'i ilgilendiren kısmını gösteren bir özettir.

## Spesifikasyon (beklenen davranış)

- **TTC0 kanal 0**, saniyede bir UART'a `tick N` satırı basar (N artan
  bir sayaç).
- **SW19**'a basınca UART'a `button: M` satırı basılır (M toplam basış
  sayısı) ve **DS50** LED'inin durumu toggle'lanır.
- Sayaçlar (`tick` ve `button`) her zaman doğru ve eksiksiz artar.
- Sistem saatlerce kesintisiz, kararlı çalışır.

## Gözlenen belirtiler

Stajyerin notları şöyle (kendin doğrulaman gereken şikâyetler):

1. **"Optimize build'de buton hiç tepki vermiyor."** Debug build'de
   (`-O0`) buton çalışır görünüyor, ama release build'de (`-O2`)
   SW19'a basınca hiçbir şey olmuyor.
2. **"Tick'ler bazen atlıyor ya da geç geliyor."** `tick N` satırları
   çoğunlukla düzgün geliyor, ama ara sıra bir numara atlanıyor ya da
   bir satır beklenenden geç çıkıyor — özellikle butona sık basılınca
   kötüleşiyor.
3. **"DS50 bir kez yanıyor, bir daha hiç sönmüyor."** İlk buton
   basışında LED yanıyor, ama sonraki basışlarda sönmesi gerekirken
   yanık kalıyor.
4. **"Sistem birkaç dakika sonra rastgele çöküyor."** Bazen beş dakika,
   bazen yirmi — sabit bir tetikleyici yok gibi görünüyor, ama er ya da
   geç sistem kilitleniyor ya da anlamsız değerler basmaya başlıyor.

## Görev

Bu dört belirtinin arkasındaki dört farklı kök nedeni bul, düzelt ve
her biri için tek cümlelik bir kök neden yaz. Görevin tam tanımı,
başarı kriterleri ve kendini sına soruları Bölüm 11'deki
**Görev 10 — Bug Hunt** kartındadır.
