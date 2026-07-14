# AGENTS.md — gomulu-oryantasyon

Bu projenin tek başlangıç talimatı **KICKOFF.md**'dir. Her oturumda önce onu oku
ve oradaki kurallara uy. Aşağıdakiler çalışma sırasında sık gereken özetlerdir.

## Hızlı özet

- Ürün: `dist/index.html` — tamamen self-contained (CSS/SVG/JS inline, internet yok).
- İçerik: `content/NN-isim.md` (bölüm başına bir dosya, NN sıra belirler).
  `_` ile başlayan dosyalar (örn. `_arastirma.md`) build'e girmez.
- Çözüm kodları: `labs/labNN-isim/` altında gerçek C dosyaları; HTML'e
  `{{kod:...}}` direktifiyle gömülür.
- Build: `python3 build/build.py` (repo kökünden). Çıktı `dist/index.html`.

## Markdown direktifleri (build.py'nin anladığı özel sözdizimi)

- Kutular: `:::saha-notu` / `:::tuzak` / `:::analoji` / `:::ekip-notu` ...
  `:::` ile kapanır. Başlık istersen: `:::saha-notu Başlık metni`.
- Katlanabilir: `:::derin-dalis Başlık` ... `:::`
- SVG göm: `{{svg:dosya-adi.svg|Şekil N — açıklama}}` (dosya `assets/svg/` altında).
- Lab kodu göm: `{{kod:lab01-led/src/main.c}}` (yol `labs/`e göre).
- Görev kartı: `:::gorev no=1 zorluk=2 baslik="..."` içinde
  `[Hedef]` `[Ön koşul]` `[Adımlar]` `[Başarı kriteri]` `[Kendini sına]`
  `[Takıldıysan]` bölümleri; Takıldıysan içinde `::ipucu Başlık` ...`::/` ve
  `::cozum lab01-led/src/main.c` `::/` blokları.
- İlerleme panosu yeri: `{{ilerleme-panosu}}` (Bölüm 0'da bir kez).

## Değişmez kurallar

1. ZCU111'e özgü her değer `content/_arastirma.md`'den (kaynaklı) gelir;
   orada yoksa web'den teyit et ve önce oraya ekle. Teyitsiz değer yazılmaz.
2. SVG'lerde hard-coded renk yasak — yalnızca `var(--...)` CSS değişkenleri.
   Her SVG'de `<title>` zorunlu.
3. Ton: Türkçe, sıcak ama ciddi; emoji yok; teknik terim İngilizce kalır,
   ilk geçişte parantezle açıklanır.
4. Kod stili (labs/): Hungarian notation, `module_object_action()` adlandırma,
   Allman braces, bol yorum, her lab klasöründe README.md.
5. Her 3 bölümde bir build alıp kontrol et.
