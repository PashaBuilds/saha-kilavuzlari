# Bölüm 12 — NAT ve Ev/Kurum Ağının Gerçeği

Bölüm 5'te öğrendin: `192.168.1.20` private bir adres ve internette
yönlendirilmez. Ama o adresli PC şu an internete çıkıyor. Nasıl? Cevap,
modern ağların en yaygın "hilesi": **NAT** (Network Address Translation —
ağ adresi çevirisi). NAT'ı anlamak, "dışarıdan cihazıma neden
erişemiyorum" sorusunun ve kurum ağındaki yarı görünmez duvarların
cevabıdır.

## Neden NAT var?

IPv4'ün ~4,3 milyar adresi dünyaya yetmedi. Çözüm iki parçalıydı: iç
ağlarda herkes aynı private blokları kullansın (Bölüm 5) ve internete
çıkarken tek bir **public** (kamusal) adresin arkasında saklansın. Evindeki
onlarca cihaz, ISS'in sana verdiği *tek* public IP'yi paylaşır. Çeviriyi
router yapar.

## Mekanizma: çevir, tabloya yaz, cevabı geri çevir

{{svg:sema-19-nat.svg|NAT'ın iki yönü: giden pakette router, kaynak IP:port'u kendi dış adresi ve seçtiği bir portla değiştirip eşlemeyi tabloya yazar. Dönen paket tablodaki eşlemeyle içerideki gerçek sahibine çevrilir. Tabloda karşılığı olmayan dış paket çöpe gider.}}

Adım adım:

1. PC (`192.168.1.20:52814`) sunucuya paket yollar.
2. Router paketi dışarı verirken **kaynak** adresi kendi WAN adresiyle,
   kaynak portu da kendi seçtiği bir portla değiştirir
   (`85.102.7.44:40001`) ve eşlemeyi **NAT tablosuna** yazar.
3. Sunucu, cevabı bildiği tek adrese — `85.102.7.44:40001` — gönderir.
4. Router tabloya bakar: "40001, içeride 192.168.1.20:52814'tü" → hedefi
   geri çevirir, paketi PC'ye teslim eder.

Port numarasının da çevrildiğine dikkat et (bu yüzden tam adı PAT/NAPT'tır
— port address translation): iki iç cihaz aynı anda aynı sunucuya
çıktığında router onları dış port numarasıyla ayırt eder. Soket dörtlüsü
(Bölüm 9) burada yeniden sahnede: NAT tablosu, dörtlüler arasında çeviri
yapan bir tablodur.

Kritik asimetri şu: NAT tablosuna kayıt, **yalnızca içeriden dışarıya**
giden trafikle düşer. Dışarıdan gelen davetsiz bir pakete tabloda eşleşme
yoktur → çöp. Bu, NAT'ın yan etkisi olarak kaba bir güvenlik duvarı gibi
davranması demektir — ve "dışarıdan erişememe" sorununun ta kendisidir.

## "Dışarıdan cihazıma neden erişemiyorum?"

Evdeki kartına ofisten bağlanmak istiyorsun: `85.102.7.44:5001`'e paket
attın. Router'ın tablosunda bu portla ilgili kayıt yok (kart dışarıya hiç
konuşmadı) → paket sessizce çöpe. Klasik çözümler:

- **Port forwarding** (port yönlendirme): router'a *kalıcı* bir kural elle
  girilir: "dışarıdan :5001'e gelen her şeyi 192.168.1.130:5001'e ilet."
  NAT tablosunun statik satırıdır. Ev router'ının arayüzünden yapılır;
  interneti açık her port gibi güvenlik sorumluluğu getirir.
- **İçeriden dışarıya kurmak:** cihaz, dışarıdaki bir sunucuya kendisi
  bağlanır ve bağlantıyı açık tutar (IoT cihazlarının bulut mimarisi tam
  budur — kimse buzdolabına port forwarding yapmaz; buzdolabı buluta
  bağlanır, komutlar o kanaldan döner).
- **VPN:** iki ağı sanal olarak aynı ağ yapar; NAT sorunu kökten kalkar.

Kurumsal ağda tablo daha katmanlıdır: NAT'ın yanında **firewall** (güvenlik
duvarı — hangi IP/port çiftlerinin konuşabileceğini kurallarla sınırlar)
ve çoğu yerde **proxy** (HTTP trafiğini senin adına yapan, filtreleyen
aracı sunucu) vardır. "Kart lab ağında çalışıyor, kurum ağında çalışmıyor"
vakalarının önemli bir dilimi ağın değil, bu politika katmanının işidir —
IT'ye sorulacak doğru soru: "şu porta şu subnet'ten erişim açık mı?"

:::saha-notu İki IP'n var: hangisini soruyorsun?
`ipconfig` sana **iç** adresini söyler (192.168.x.x); internetteki
servislerin gördüğü **dış** adresini ise ancak dışarıdan öğrenirsin:
tarayıcıdan "what is my ip" ya da konsoldan `curl ifconfig.me`. Uzaktaki
birine "IP'mi vereyim" derken bu ayrımı karıştırmak klasiktir: iç adresin
onun ağında anlamsızdır. Tersi de teşhis kokusudur: `tracert` çıktının
ilk *iki* hop'u da private blokta ise (192.168.1.1 → 10.0.0.1 gibi) çift
NAT arkasındasın demektir.
:::

:::tuzak NAT tablosu kayıtları ölümlüdür
Tablodaki dinamik kayıtların ömrü vardır: trafik akmayan UDP eşlemesi
tipik olarak 30–120 saniyede, boştaki TCP bağlantısı birkaç saatte düşer.
Kartın buluta UDP telemetri atıyor ve "arada komutlar kayboluyor"sa,
muhtemelen sunucudan karta dönen paketler, süresi dolmuş bir NAT kaydına
çarpıyordur. Standart ilaç: **keepalive** — bağlantıyı düzenli aralıkla
(ör. 25 saniyede bir) minik bir paketle canlı tutmak. TCP'de
`SO_KEEPALIVE` soket seçeneği de aynı derdin kurumsal çözümüdür.
:::

:::analoji Şirket santralinin tek dış numarası
NAT'lı ağ, tek dış telefon numarası olan şirkettir. İçeriden herkes dış
arama yapabilir; santral (router) "dahili 20, dış hat 40001'den konuşuyor"
diye deftere (NAT tablosu) yazar; geri arayanı deftere bakıp doğru
dahiliye bağlar. Ama şirketi dışarıdan arayıp "dahili 130'a bağlayın"
diyemezsin — santral tanımadığı çağrıyı açmaz. Port forwarding,
santrale bırakılmış kalıcı talimattır: "40001'i soran olursa dahili
130'a bağla."
:::

:::ozet
- NAT, private iç adresleri tek public adrese çevirir; eşlemeler NAT
  tablosunda yaşar, port numaraları da çevrilir (PAT).
- Tablo kaydı yalnız içeriden dışarıya trafikle açılır; davetsiz dış paket
  çöpe gider — "dışarıdan erişemiyorum"un sebebi.
- Çözümler: port forwarding (statik kural), içeriden-dışarı bağlantı
  (IoT deseni), VPN.
- Kurum ağında NAT'ın yanına firewall ve proxy eklenir; "lab'da çalışıyor,
  kurumda çalışmıyor" çoğu zaman politika meselesidir.
- NAT kayıtları zaman aşımına uğrar; uzun ömürlü bağlantıları keepalive
  ile canlı tut.
:::
