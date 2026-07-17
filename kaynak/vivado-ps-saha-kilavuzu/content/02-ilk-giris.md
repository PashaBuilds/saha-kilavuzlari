# Bölüm 2 — Vivado'ya İlk Giriş (Yazılımcı Rotası)

## Neden umursamalısın

Vivado'yu ilk açışında iki tepkiden biri gelir: ya panele bakıp kapatırsın
ya da yanlış bir yere tıklayıp donanımcının projesini bozmaktan korkarsın.
İkisi de çözülür: arayüzün yazılımcıyı ilgilendiren kısmı üç panelden
ibarettir ve "bozma" korkusunun panzehiri birkaç basit görgü kuralıdır.

## Projeyi açmak: .xpr ve proje dizini

Bir Vivado projesi tek dosya değildir; `.xpr` uzantılı bir giriş dosyası ve
etrafındaki dizin ailesidir (`proje.srcs/`, `proje.gen/`, `proje.runs/` ...).
Donanımcıdan proje aldığında `.xpr` dosyasını açarsın:

[[adim: File → Open Project → demo_ultrascale.xpr]]

ya da dosyaya çift tıklarsın. Repo'daki demo için:

```powershell
vivado vivado\work\demo_ultrascale\demo_ultrascale.xpr
```

Vivado ilk açıldığında seni **Start Page** karşılar: soldan proje aç/oluştur,
sağda son projeler. Buradaki tek ilgin "Open Project".

[[ekran: 29 | Vivado Start Page — açılış
rozet 1: Quick Start → Open Project — donanımcının .xpr'ını buradan açarsın; gerisi (Create/Example) senin işin değil.
]]

:::tuzak
`.srcs` içindeki dosyaları dosya yöneticisinden açıp düzenleme hevesine
kapılma. Vivado proje durumunu kendi meta verisinde tutar; dışarıdan
değiştirilen dosyalar projeyi tutarsız bırakabilir. Okumak istediğin her
şeyin Vivado içinde (ya da Ek A'daki Tcl komutlarıyla) temiz bir yolu var.
:::

## Arayüz turu: üç panel yeter

[[ekran: 01 | Vivado ana penceresi — proje açık
rozet 1: Flow Navigator — donanımcının komuta paneli; senin için sadece iki satırı önemli: IP Integrator → Open Block Design ve PROGRAM AND DEBUG.
rozet 2: Sources — projenin dosya ağacı; blok dizaynı ve wrapper'ı burada bulursun.
rozet 3: Diagram penceresi — blok dizaynın kendisi; kılavuzun kalbi burada atar.
not: Pencere yerleşimi sürüklenerek değişebilir; kaybolursan Window menüsünden panelleri geri açabilirsin. Layout → Default Layout her şeyi fabrika düzenine döndürür.
]]

Solda **Flow Navigator**: donanımcının tasarım akışı (sentezden bitstream'e).
Ortada **Diagram** penceresi: blok dizayn. Üstte **Sources**: dosya ağacı.
Yazılımcı rotası şu tek adımdan geçer:

[[adim: Flow Navigator → IP INTEGRATOR → Open Block Design]]

Sources panelinde `sistem_wrapper` gibi bir en-üst modül ve altında `sistem.bd`
görürsün — donanımcı blok dizaynı bir HDL sarmalayıcı (wrapper) içine koyar;
sentez o sarmalayıcıdan başlar. Senin okuyacağın şey `.bd` dosyasıdır.

[[ekran: 02 | Sources — hiyerarşi görünümü
rozet 1: sistem_wrapper — projenin en üst HDL modülü; elle yazılmaz, Vivado üretir.
rozet 2: sistem.bd — blok dizayn; çift tıklayınca Diagram penceresinde açılır.
]]

## "Yanlışlıkla neyi bozabilirim?" — read-only görgü kuralları

Gerçek şu: salt bakarak bir şey bozamazsın. Tıklamak, seçmek, zoom yapmak,
sekmeleri gezmek projenin diskteki hâlini değiştirmez. Riskli eylemler
bellidir ve hepsinin ortak özelliği bir şeyi *değiştirmiş* olmandır:
blok taşımak, parametre penceresinde OK'e basmak, çizgi çekmek.

Üç görgü kuralı seni her durumda korur:

1. **Parametre pencerelerinden Cancel ile çık.** Re-customize ekranlarını
   okumak serbest; kapatırken OK değil Cancel. OK, hiçbir şey değiştirmemiş
   olsan bile IP'yi yeniden üretim kuyruğuna sokabilir.
2. **Kaydetmeden kapat.** Yanlışlıkla bir bloğu kımıldattıysan panik yok:
   File → Close Project de, çıkan diyalogda **Don't Save** seç. Proje
   diskte dokunulmamış kalır.
3. **Git'teki projeye dokunma.** Donanımcının repo'sundaki çalışma kopyasında
   inceleme yapma; kendine ayrı bir kopya al ya da (en temizi) projeyi
   scriptten kendin üret. `git status`'ta beliren `.jou`/`.log` dosyaları
   bile "kim elledi" sorusu doğurur.

[[ekran: 03 | Kaydetmeden çıkış — onay diyaloğu
rozet 1: Don't Save (ya da sürüme göre No) — senin cevabın hep bu; proje diskte değişmeden kalır.
not: Bu diyaloğu görmek kötüye işaret değildir; tam tersine, seçim şansının hâlâ elinde olduğunu gösterir. Vivado sormadan hiçbir şeyi diske yazmaz.
]]

:::saha-notu
Vivado her oturumda çalıştığın dizine `vivado.jou` (journal — yaptığın her
işlemin Tcl karşılığı) ve `vivado.log` düşürür. Journal iki işe yarar:
yanlışlıkla ne yaptığını geriye doğru okuyabilirsin ve GUI'de yaptığın bir
işlemin Tcl karşılığını öğrenip scriptleştirebilirsin. Ek A'daki komutların
çoğu journal'dan öğrenilme tekniğiyle bulunabilir.
:::

## Alt akış: sentez, implementasyon, bitstream — bir paragraf yeter

Flow Navigator'ın alt yarısı donanımcının üretim bandıdır. **Sentez**
(synthesis) RTL kodunu kapı seviyesi devreye çevirir; **implementasyon**
(implementation) o devreyi çipin fiziksel kaynaklarına yerleştirir ve
yolları çizer; **bitstream üretimi** sonucu çipe yüklenecek ikili dosyaya
paketler. Saatler sürebilir, senin analizin için hiçbiri gerekmez — blok
dizayn, adres haritası ve PS ayarları sentezsiz okunur. Bu düğmelere basmak
senin işin değil; ama donanımcı "implementasyon timing'i kapatmıyor"
dediğinde bunun bandın neresinde olduğunu artık biliyorsun.

[[sema: sema-02-vivado-kusbakisi | Şema 2 — Vivado kuşbakışı: üst şerit yazılımcının analiz rotası (saniyeler), alt şerit donanımcının üretim bandı (saatler). İkisi .xsa noktasında buluşur.]]

:::yazilima-yansimasi
Bitstream'in yazılım tarafındaki izdüşümü boot akışında görünür: PL,
bitstream yüklenene kadar boş bir dokudur. FSBL/U-Boot ya da senin
uygulaman bitstream'i yüklemeden PL'deki hiçbir IP (EMIO'ya yönlenmiş
çevre birimleri dahil) yaşamaz. "Kart açıldı, PS konsolu var ama PL IP'lerim
timeout atıyor" tablosunun ilk kontrol maddesi budur: bitstream yüklendi mi?
:::

:::deneme id=deneme-2-1
**Hedef:** Read-only görgüyü kas hafızasına yaz.

Demo projeyi aç, blok dizaynı görüntüle, `ps_ultra` bloğunu fareyle 2 cm
sağa taşı (evet, bilerek boz). Sonra projeyi kapat.

[[adim: File → Close Project]]

Soru: çıkan diyalogda hangi seçenekler var ve hangisini seçtin? Kapattıktan
sonra projeyi tekrar aç — blok eski yerinde mi?

::cozum::
Diyalog Save / Don't Save / Cancel sunar. Don't Save seçtiysen blok eski
yerindedir: taşıma diske hiç yazılmadı. Bir kez bu döngüyü bilerek yaşamak,
"bozarım" korkusunu kalıcı olarak söker — en kötü senaryonun çıkışı tek
tıktır.
:::

:::ozet
- Proje = .xpr + dizin ailesi; açılacak dosya .xpr'dir.
- Yazılımcı rotası: Open Block Design. Gerisi donanımcının bandı.
- Bakmak bozmaz. Cancel ile çık, Don't Save ile kapat, git'teki kopyaya
  dokunma.
- Sentez/implementasyon/bitstream'i tanı ama koşturma; analiz sentezsiz
  yapılır.
:::
