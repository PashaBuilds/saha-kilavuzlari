# Bölüm 1 — Büyük Resim: Katmanlar

Ağ dünyasındaki her kavram — MAC, IP, port, DNS, TLS — tek bir iskelete
asılır: **katman modeli**. Bu iskeleti bir kez doğru kurarsan, gerisi yerine
oturur. Kurmadan ilerlersen her yeni terim havada asılı kalır. O yüzden
kılavuzun ilk işi bu: beş katlı bir zihinsel model inşa edip sonuna kadar
onu kullanmak.

## Neden katman var?

"Tarayıcıdan sunucuya veri gitsin" işi, tek parça çözülemeyecek kadar
karmaşık. Kablodaki voltaj seviyeleri, aynı ağdaki cihazların birbirini
bulması, şehirlerarası yönlendirme, kaybolan paketlerin telafisi, verinin
şifrelenmesi... Bunların hepsini tek bir devasa protokolde çözmeye kalksan,
kablo teknolojisi her değiştiğinde tarayıcıyı yeniden yazman gerekirdi.

Çözüm, mühendisliğin klasik hamlesi: problemi kes, katmanlara ayır, her
katmana tek bir iş ver ve katmanlar arasına net bir arayüz koy. Her katman
yalnızca bir alttakinin sunduğu hizmeti kullanır ve bir üsttekine hizmet
sunar. Alt katman *nasıl* yaptığını üstten gizler: TCP, verinin fiber
üzerinden mi Wi-Fi üzerinden mi gittiğini bilmez; HTTP, kaybolan paketleri
TCP'nin nasıl telafi ettiğini bilmez. Sen de gömülü tarafta aynısını
yaşıyorsun: `socket` API'sini çağıran uygulama kodun, altındaki Ethernet
denetleyicisinin DMA ayarlarından habersizdir — ve bu bir eksiklik değil,
tasarımın kendisidir.

:::analoji Katmanlar: kargo zinciri
Bir arkadaşına hediye yolluyorsun. Sen hediyeyi seçersin (uygulama), kutuya
koyup üstüne "kırılacak eşya, teslimatta imza al" yazarsın (taşıma), kargo
firması kutuya adres etiketi yapıştırır (ağ), şoför o gün hangi kamyona,
hangi rafa koyacağına karar verir (veri bağı), kamyon da asfaltta fiilen
yol alır (fiziksel). Şoför hediyenin ne olduğunu bilmez; sen kamyonun
plakasını bilmezsin. Herkes kendi katmanının işini yapar, zincir çalışır.
:::

## OSI mi, TCP/IP mi?

Literatürde iki model görürsün. **OSI (Open Systems Interconnection)**
yedi katmanlı akademik referans modeldir; 1980'lerde uluslararası bir
standart olarak tasarlandı. **TCP/IP modeli** ise internetin fiilen üzerinde
çalıştığı, pratikten doğmuş modeldir. OSI'nin 5-6-7. katmanları (oturum,
sunum, uygulama) gerçek dünyada neredeyse her zaman tek bir uygulama
protokolünün içinde erir — HTTP hem oturumu hem sunumu hem uygulamayı kendi
içinde halleder.

{{svg:sema-01-osi-tcpip.svg|OSI'nin yedi katmanı ile bu kılavuzun kullanacağı pratik beş katmanlı TCP/IP modeli. Sağ sütun, her katmanda karşılaşacağın örnek protokolleri gösteriyor.}}

Bu kılavuz boyunca sağdaki **beş katmanı** kullanacağız:

1. **Fiziksel** — bitleri kabloda/fiberde/havada taşır. Volt, ışık, radyo.
2. **Veri bağı (link)** — aynı yerel ağdaki iki cihaz arasında frame
   (çerçeve) taşır. Ethernet burada yaşar; adresi **MAC**'tir.
3. **Ağ (network)** — farklı ağlar arasında paket yönlendirir. IP burada
   yaşar; adresi **IP adresidir**.
4. **Taşıma (transport)** — iki uygulama arasında uçtan uca taşıma. TCP ve
   UDP burada yaşar; adresi **port**tur.
5. **Uygulama** — verinin anlamı. HTTP, DNS, MQTT, senin kendi protokolün.

OSI tamamen çöp değil: sahada herkes katmanları OSI numarasıyla anar.
"L2 switch", "L3 yönlendirme", "L4 load balancer", "L7 firewall" dendiğinde
kastedilen OSI numarasıdır. Numaraları bil, yedi katmanı ezberleme.

:::tuzak "Katman" fiziksel bir kutu değildir
Katmanlar kodda ve kavramda vardır; kartta "IP çipi" diye ayrı bir yonga
aramak yanıltır. Tek bir Ethernet denetleyicisi fiziksel + veri bağı işini
yapar; IP/TCP genellikle yazılımdır (işletim sistemi ya da lwIP gibi bir
stack). Aynı şekilde tek bir cihaz birden çok katmanda iş yapabilir:
ev "modemin" aynı kutuda switch (L2), router (L3) ve erişim noktasıdır.
:::

## Enkapsülasyon: her katman bir zarf

Katman modelinin çalışma mekaniği tek kelimeyle özetlenir:
**enkapsülasyon (sarmalama)**. Veri aşağı inerken her katman, kendi işini
yapabilmek için gereken bilgiyi bir **header** (başlık) olarak verinin
önüne ekler ve paketi bir alt katmana devreder. Header, o katmanın
"zarfın üstüne yazdığı" bilgidir: TCP header'ında port numaraları ve sıra
numarası, IP header'ında kaynak/hedef IP adresi, Ethernet header'ında MAC
adresleri vardır.

{{svg:sema-02-enkapsulasyon.svg|Enkapsülasyon zinciri: HTTP verisi TCP header alıp segment olur, IP header alıp paket olur, Ethernet header + FCS alıp frame olur. Kabloya çıkan şey en dıştaki frame'dir.}}

Her seviyedeki paketin kendi adı vardır ve bu adları doğru kullanmak,
Wireshark okurken ve hata ayıklarken düşünceni netleştirir:

| Katman | Paketin adı | Header'ın taşıdığı kritik bilgi |
|---|---|---|
| Uygulama | mesaj (message) | verinin kendisi ve anlamı |
| Taşıma | **segment** (TCP) / **datagram** (UDP) | kaynak/hedef **port** |
| Ağ | **paket** (packet) | kaynak/hedef **IP adresi** |
| Veri bağı | **frame** (çerçeve) | kaynak/hedef **MAC adresi** |
| Fiziksel | bit / sembol | — |

Alıcı tarafta süreç tersine işler: her katman kendi header'ını okur, işini
yapar, header'ı söküp kalanı bir üst katmana verir. Buna
**de-enkapsülasyon** denir. Ethernet sürücüsü MAC'e bakar, IP katmanı IP'ye
bakar, TCP porta bakar ve veri sonunda doğru uygulamanın soketine düşer.

:::saha-notu Wireshark bu şemanın kendisidir
Wireshark'ta herhangi bir paketi tıkladığında ortadaki detay panelinde
gördüğün ağaç, tam olarak enkapsülasyon katmanlarıdır: en üstte
`Ethernet II`, altında `Internet Protocol`, altında `Transmission Control
Protocol`, en altta uygulama verisi. Bölüm 15'te bu paneli satır satır
okuyacağız; şimdiden bir capture açıp ağacı bu şemayla karşılaştırmak
dersi kalıcılaştırır.
:::

## İki adres dünyası

Şemadaki zincirde iki ayrı adres türü göründü; bu ayrım kılavuzun en
kritik fikirlerinden biri, o yüzden ilk bölümden mıhlayalım:

- **MAC adresi** veri bağı katmanına aittir ve yalnızca **aynı yerel ağ
  içinde** anlamlıdır. "Bu frame, bu odadaki hangi cihaza gidecek?"
  sorusunu cevaplar.
- **IP adresi** ağ katmanına aittir ve **uçtan uca** anlamlıdır. "Bu paket,
  dünyadaki hangi makineye gidecek?" sorusunu cevaplar.

Bir paket İstanbul'dan Frankfurt'a giderken IP adresleri baştan sona aynı
kalır; ama frame her router (yönlendirici) atlayışında yeniden sarılır ve
MAC adresleri her adımda değişir. Bu cümle şu an tam oturmadıysa dert
değil — Bölüm 6 ve 7'de örneğiyle, şemasıyla geri geleceğiz.

:::derin-dalis OSI neden kaybetti?
1980'lerde iki kamp vardı: telekom devlerinin ve standart kurumlarının
desteklediği, önce tasarlanıp sonra kodlanan OSI; ve üniversitelerde
çalışan, önce kodlanıp sonra belgelenen TCP/IP. OSI protokolleri (X.400
e-posta, CLNP gibi) kâğıt üstünde daha "eksiksizdi" ama uygulamaları geç,
pahalı ve hantaldı. TCP/IP ise BSD Unix ile bedava dağıldı; çalışan kodu
olan kazandı. Geriye OSI'den pratikte iki şey kaldı: katman numaralama
sözlüğü (L2/L3/L4/L7) ve ders kitaplarındaki yedi katlı şema. Ağ dünyasının
ünlü özdeyişi bu dönemden kalmadır: "kaba fikir birliği ve çalışan kod"
(rough consensus and running code).
:::

:::ozet
- Katmanlar, karmaşayı bölmek içindir: her katman tek iş yapar, altındakinin
  *nasılını* bilmez.
- Bu kılavuz 5 katman kullanır: fiziksel → veri bağı → ağ → taşıma →
  uygulama. Sahada L2/L3/L4/L7 kısaltmaları OSI numaralarıdır.
- Enkapsülasyon: veri inerken her katman öne kendi header'ını ekler;
  mesaj → segment → paket → frame zinciri oluşur.
- MAC adresi yerel ağ içinde, IP adresi uçtan uca geçerlidir; frame her
  router adımında yenilenir, IP paketi yolculuk boyunca aynı kalır.
- Wireshark'ın detay paneli, enkapsülasyon ağacının canlı halidir.
:::
