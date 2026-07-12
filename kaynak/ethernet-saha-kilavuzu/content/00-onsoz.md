# Önsöz — Bu Kılavuz Kimin İçin

Bir FPGA kartına ping atamadığın bir akşam, elinde `ipconfig` çıktısı,
karşında yanıp sönen bir link LED'i ile kaldıysan bu kılavuz senin için
yazıldı. Ağ yöneticisi olmayacaksın; switch konfigürasyonu ezberlemeyeceksin.
Ama işin gereği Ethernet üzerinden konuşan cihazlarla — FPGA kartları, gömülü
işlemciler, test cihazları, kurumsal LAN'daki ölçüm düzenekleri — her gün
uğraşıyorsun. Socket açıyorsun, paket yakalıyorsun, "neden bağlanamıyorum"
diye saatler harcıyorsun.

Bu kılavuz, "Saha Kılavuzu" serisinin üçüncü üyesi. Serinin ruhu aynı:
tek bir HTML dosyası, internetsiz açılır, baştan sona okunduğunda o konuda
kendi ayakları üstünde durmanı sağlar. Bellek Mimarisi ve RF Örnekleme
kılavuzları donanımın içine bakıyordu; bu kılavuz kartın dışına, kabloya ve
kablodan öteye bakıyor.

## Bittiğinde neler yapabileceksin

1. Tarayıcıya bir URL yazıldığı anda başlayan zinciri — DNS, ARP, TCP, TLS,
   HTTP — adım adım, katman katman anlatabileceksin.
2. Wireshark'ta bir capture (paket kaydı) açıp gördüğün frame'i katmanlarına
   ayırabileceksin: "şu byte'lar Ethernet, şunlar IP, şunlar TCP."
3. Kurumsal LAN'da bir gömülü karta UDP veya TCP ile bağlanan Python kodunu
   kendin yazabileceksin.
4. "Link var ama ping yok" tarzı bir arızayı el yordamıyla değil, sistematik
   bir karar ağacıyla teşhis edebileceksin.

## Nasıl okumalı

Bölümler birbirinin üstüne inşa edilir: hiçbir kavram tanımlanmadan
kullanılmaz. Baştan sona okumak en iyisi; ama acelen varsa şu rotalar işler:

| Derdin | Rota |
|---|---|
| "Ağın büyük resmini bir görsem yeter" | 1 → 4 → 13 |
| "Karta soket açıp veri alacağım" | 1 → 5 → 9 → 15 |
| "Kart ping atmıyor, yardım" | 5 → 6 → 7 → 14 → 16 |
| "Wireshark'ı öğrenmek istiyorum" | 1 → 3 → 9 → 15 |
| "Gömülü Ethernet bring-up yapıyorum" | 2 → 3 → 14 → 16 |

Metin boyunca dört tür kutuyla karşılaşacaksın:

:::saha-notu Bu kutu: saha notu
Gerçek hayatta işe yarayan pratik bilgi. Çoğu zaman bir komut, bir Wireshark
filtresi ya da yılların "keşke bana da söyleseydiler" tecrübesi.
:::

:::tuzak Bu kutu: tuzak
Yaygın hata ve yanlış anlamalar. Bu kutulardaki hataların her biri sahada
gerçekten yapılmış, saatler yakmıştır.
:::

:::analoji Bu kutu: analoji
Soyut kavramı günlük hayattan bir benzetmeye bağlar. Benzetme birebir
örtüşmez ama zihinde tutacak bir kanca verir.
:::

:::derin-dalis Bu kutu: derin dalış
Meraklısına ek derinlik. Katlıdır; açmadan geçersen ana akıştan hiçbir şey
kaçırmazsın. İlk okumada atlamak tamamen meşru.
:::

Teknik terimler İngilizce bırakılır, ilk geçtiği yerde parantez içinde
Türkçesi verilir — sahada ve dokümantasyonda İngilizcesiyle karşılaşacaksın,
Türkçe uydurma karşılıklar seni yavaşlatır. Komutlar hem Windows hem Linux
karşılığıyla yazılır. Kod örnekleri Python 3'tür ve yalnızca standart
kütüphane kullanır: kopyala, yapıştır, çalıştır.

:::ozet
- Hedef kitle: ağcı değil, ağ üzerinden iş yapan gömülü yazılımcı.
- Kılavuz baştan sona pedagojik sırayla inşa edilir; acele rotaları yukarıda.
- Dört kutu türü: saha notu (pratik), tuzak (hata), analoji (benzetme),
  derin dalış (isteğe bağlı derinlik).
- Tüm kod örnekleri Python 3 stdlib; komutlar Windows + Linux.
:::
