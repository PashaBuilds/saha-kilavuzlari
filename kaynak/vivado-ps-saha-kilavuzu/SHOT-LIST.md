# SHOT-LIST — Otomatik alınamayan kareler (B2 yedek yol)

GUI yakalama turu (B1) 29 kareden **28'ini** otomatik döngüyle aldı ve her
karesini görsel olarak doğruladı (bkz. `vivado/gui_capture/capture_log.md`).
Geriye tek kare kaldı; kullanıcının elle çekmesi gerekiyor — ama bu karenin
taşıdığı bilgi (güvenli çıkış davranışı) dokümanda zaten anlatılmış durumda.

## Çekilecek kare

### shot-03 — Kaydetmeden çıkış onay diyaloğu
- **Neden otomatik alınamadı:** 2022.2'de `close_project` konsoldan
  çağrıldığında, projede kaydedilmemiş değişiklik yoksa Vivado onay sormadan
  kapatıyor — yani "güvenli çıkış" davranışı zaten kanıtlandı, diyalog hiç
  belirmedi.
- **Nasıl çekilir (isteğe bağlı):**
  1. `vivado -mode tcl -source vivado/gui_capture/stage_us_open.tcl`
  2. Diagram'da bir bloğu (örn. `ps_ultra`) birkaç piksel taşı — böylece
     proje "değişmiş" sayılır.
  3. **File → Close Project** (menüden, konsoldan değil).
  4. Beklenen diyalog: **Save / Don't Save / Cancel** seçenekleri.
  5. `assets/screenshots/shot-03.png` olarak kaydet; **Don't Save** ile çık
     (asla Save — projeyi scriptten yeniden üretilebilir tutuyoruz).

## Not

Kare kaydedildiğinde `assets/screenshots/shot-03.png` düzenine uyduğu anda,
`build/annotate.py` içindeki SPEC sözlüğüne bir rozet koordinatı eklenip
`python build/gorsel_hatti.py && python build/build.py` çalıştırıldığında
doküman kareyi gömer ve bu listeden düşer.

shot-23 ve shot-24 (Versal CIPS UART0 / PL clock) düzeltme turunda otomatik
olarak çekildi ve dokümana açıklama katmanlı biçimde eklendi — artık
SHOT-LIST dışında.
