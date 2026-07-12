# Bölüm 0 — Önsöz: Neden Lokal?

ChatGPT'ye ya da Claude'a bir soru yazdığında, o metin senin makinenden çıkar,
internetin üzerinden bir veri merkezine gider, orada devasa bir modelden geçer
ve cevap sana geri döner. Bu düzen çoğu iş için gayet iyi çalışır. Peki aynı
işi — daha mütevazı bir ölçekte — kendi bilgisayarının yapabildiğini biliyor
muydun? Diskinde duran birkaç gigabaytlık bir dosya, internet bağlantısı
olmadan seninle sohbet edebilir, kod yazabilir, doküman özetleyebilir.

Bu kılavuz, o dosyanın ne olduğunu, hangi donanımda nasıl davrandığını ve onu
nasıl çalıştıracağını baştan sona anlatır. Hedefimiz net: kılavuz bittiğinde
bir model kartındaki "70B, MoE, Q4_K_M, 128K context" gibi ifadeleri sökebilecek,
kendi makinene bakıp "bende şu sınıf model, aşağı yukarı şu hızda döner"
diyebilecek ve ilk modelini indirip çalıştırmış olacaksın.

{{svg:00-lokal-vs-bulut.svg|Aynı iş, iki düzen: bulutta model sağlayıcının veri merkezinde çalışır ve verin oraya gider; lokalde model diskindeki bir dosyadır ve hiçbir şey makinenden çıkmaz.}}

## Lokal çalıştırmanın dört somut gerekçesi

**Gizlilik.** Lokal modelde prompt'un da cevabın da makinenden çıkmaz. Şirket
içi dokümanlar, hasta kayıtları, hukuki metinler, henüz yayımlanmamış kod —
"bu veriyi üçüncü tarafa gönderebilir miyim?" sorusunun hiç sorulmadığı tek
düzen budur. Bulut sağlayıcıların gizlilik taahhütleri vardır; ama taahhüt ile
"veri fiziksel olarak buradan çıkmıyor" aynı şey değildir.

**Maliyet yapısı.** Bulut kullanımı ya abonelik ya token başına ücrettir;
kullanım arttıkça fatura büyür. Lokalde maliyet öne çekilmiştir: donanımı bir
kez alırsın (çoğu zaman zaten elindedir), sonrası elektrik. Günde binlerce
istek atan bir otomasyon, özetleme hattı ya da deney düzeneği için bu fark
belirleyici olabilir.

**Çevrimdışı ve kesintisiz çalışma.** Uçakta, sahada, kötü bağlantılı yerlerde
model yanında. Sağlayıcının kesintisi, hız limiti (rate limit — birim zamanda
izin verilen istek sayısı), model emekliye ayırması seni etkilemez. Bugün
çalışan kurulum, beş yıl sonra da aynen çalışır.

**Deney ve kontrol özgürlüğü.** Modelin sistem promptunu, örnekleme
ayarlarını, hatta modelin kendisini istediğin gibi değiştirirsin. Sağlayıcının
uygun gördüğü davranış katmanlarıyla değil, modelin kendisiyle muhatapsın.
Farklı modelleri yan yana koyup karşılaştırmak, bir modeli belirli bir işe
göre ince ayarlamak (fine-tuning) ancak bu düzende gerçekten elinin altındadır.

Bu dördünün toplamına son yıllarda bir isim verildi: **compute sovereignty
(hesaplama egemenliği)** — verinin, aracın ve üretim sürecinin kontrolünün
kendinde olması. Nasıl kendi fotoğraf arşivini buluta yedeklesen bile bir
kopyasını evde tutmak istersen, "düşünen aracının" bir kopyasını da kendi
makinende tutabilmek giderek daha çok insana anlamlı geliyor.

:::analoji
Bulut LLM restoran gibidir: mutfak profesyoneldir, menü geniştir ama her
yemekte hesap ödersin ve mutfağa giremezsin. Lokal LLM ev mutfağıdır:
donanımını bir kez kurarsın, malzemeyi (modeli) kendin seçersin, kimse ne
pişirdiğine karışmaz — ama bulaşıklar da senindir ve Michelin yıldızı
beklememelisin.
:::

## Dürüst beklenti yönetimi

Bu kılavuz hype satmaz, o yüzden baştan söyleyelim: **lokal model, bedava
Claude değildir.** Evindeki donanımda çalışan bir model, en büyük bulut
modellerinin yeteneğine bugün ulaşmaz. Frontier (en ön saf) modeller yüz
milyarlarca — bazıları trilyon ölçeğinde — parametreyle, veri merkezi dolusu
donanımda çalışır. Senin makinen bunun küçük bir dilimini kaldırır.

İyi haber şu: çok işin frontier modele ihtiyacı yok. Özetleme, sınıflandırma,
taslak yazma, basit kod yardımı, doküman içinde soru-cevap, veri temizleme
gibi işlerde bugünün 4–30 milyar parametrelik açık modelleri şaşırtıcı
derecede yeterli — ve bu sınıf her yıl belirgin biçimde iyileşiyor. Kural
kabaca şudur:

- **Lokal model yeterli:** tanımı belli, kapsamı dar, tekrar eden işler;
  gizliliğin pazarlık konusu olmadığı işler; yüksek hacimli otomasyon.
- **Bulut hâlâ daha iyi:** çok adımlı karmaşık akıl yürütme, uzun ve çetrefil
  kod tabanlarında derin çalışma, "en iyi cevap neyse o" gereken durumlar.

İkisi rakip değil, aynı alet çantasının farklı gözleri. Bu kılavuzu bitiren
biri çoğu zaman ikisini birlikte kullanır: hassas ve hacimli işler lokalde,
en zor işler bulutta.

:::tuzak
"Lokal model kurayım, aboneliklerimi iptal edeyim" diye başlamak en yaygın
hayal kırıklığı senaryosudur. Önce lokal modelin kendi işlerinde yeterli olup
olmadığını gör, sonra neyi nereye taşıyacağına karar ver. Donanım almak
gerekiyorsa bu karar hepten sona kalmalı — sıradaki kutuya bak.
:::

:::saha-notu Okuma rotaları
Kılavuz baştan sona okunacak şekilde sıralandı; her bölüm bir öncekinin
üstüne kurulur. Ama acelen varsa üç kestirme rota var:

- **"Makinemde ne döner?" rotası:** Bölüm 2 → 4 → 5 → 11. Model boyutları,
  quantization ve bellek ilişkisini kurup doğrudan büyük tabloya git.
- **"Hemen kurayım" rotası:** Bölüm 8 → 12. Ollama ile ilk modelini indir,
  sonra senaryolara bak. Kavramları sonra doldurursun.
- **"Donanım alacağım" rotası:** Bölüm 5 → 6 → 9 → 11 → 13'ü **satın almadan
  önce** oku. Bu kılavuzdaki en pahalı hatalar donanım hataları; bant
  genişliği kavramını anlamadan ekran kartı ya da Mac seçme.
:::

## Bu kılavuz nasıl yazıldı

Kavramsal bölümler (1–9) zamandan bağımsızdır: token, parametre, quantization,
bellek bant genişliği gibi kavramlar model sürümlerinden bağımsız geçerliliğini
korur. Kılavuzun kalıcı değeri oradadır. Model ve cihaz isimleri geçen bölümler
(10, 11, 13) ise yazım tarihindeki manzarayı yansıtır ve eskimeye mahkûmdur —
bu bölümlerde tarihe ve "manzara hızla değişir" uyarılarına dikkat et.

Metin boyunca beş tür kutuyla karşılaşacaksın: altın **saha notları** hemen
uygulanabilir pratik bilgidir; kırmızı **tuzaklar** yaygın hatalardır; yeşil
**analojiler** kavramı günlük hayata bağlar; mavi **derin dalışlar** meraklısı
için isteğe bağlı derinliktir, atlanabilir; **hesap kutuları** ise bu kılavuzun
imzasıdır — "kaba VRAM hesabı", "token/s tahmini" gibi arka-zarf hesaplarını
adım adım gösterir, çünkü bu dünyada doğru soru "çalışır mı?" değil, "kaç
gigabayt ve kaç token/s?" sorusudur.

:::ozet
- Lokal LLM'in dört gerekçesi: gizlilik, maliyet yapısı, çevrimdışı çalışma,
  deney/kontrol özgürlüğü — toplamı compute sovereignty (hesaplama egemenliği).
- Lokal model bedava Claude değildir; frontier yetenek bekleme. Ama tanımlı,
  tekrar eden, gizlilik-hassas işlerde bugünkü açık modeller fazlasıyla yeterli.
- Bulut ve lokal rakip değil, tamamlayıcıdır: hacimli ve hassas işler lokale,
  en zor işler buluta.
- Bölüm 1–9 kalıcı kavramlar, 10–13 dönemin manzarası; donanım almadan önce
  mutlaka 5, 6 ve 11'i oku.
:::
