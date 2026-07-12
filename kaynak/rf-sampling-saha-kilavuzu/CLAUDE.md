# CLAUDE.md — çalışma kuralları

Tek talimat kaynağı **KICKOFF.md**'dir; bu dosya oradaki §4–§5'in özetidir.
Çelişki durumunda KICKOFF.md kazanır.

## Yazım (KICKOFF §4)

1. **Pedagojik sıra:** her kavram, ona ihtiyaç duyan kavramdan ÖNCE anlatılır;
   ileri referans gerekiyorsa `{{sec:N}}` ile "§N'de derinleştireceğiz" denir.
2. **Somutlaştırma:** her soyut kavram sayısal bir örnekle bağlanır
   (gerçek GHz/fs/Gbps değerleriyle uçtan uca hesaplar).
3. **"Neden" önce gelir:** her bölüm motivasyon paragrafıyla açılır.
4. **Gömülü yazılımcı perspektifi:** her donanım kavramının yazılıma dokunduğu
   yer işaretlenir (init sırası, status register, hata görünümü).
5. Ton: teknik, net, samimi ama laubali değil; klişe ve abartı yok,
   trade-off'lar dürüst. Türkçe gövde; teknik terim İngilizce kalır, ilk
   geçtiği yerde parantezle açıklanır.

## Doğruluk ve NDA (KICKOFF §5 — KRİTİK)

1. **Uydurma yasak.** Emin olunmayan sayı/register/pin adı → `[DOĞRULA: ...]`
   etiketi; web'den teyit edilemeyen değer dokümana giremez.
2. **NDA boşlukları** `::: pasa` bloğu ile açık bırakılır (hangi güvenli
   dokümana bakılacağı yazılır). Public ve NDA bilgi asla karışmaz.
3. Standart/doküman numaraları (JESD204C, AMD AM/PG/UG) ilk kullanımdan önce
   web'den teyit edilir; tahmini numara yazılmaz.
4. Her bölümün sonunda o bölümün kaynakları listelenir (toplu hali §19).

## Yazarken kullanılacak sözdizimi

- Şekil: `![Altyazı](../diagrams/svg/d01.svg)` → otomatik "Şekil N.M" numarası
- Şekil referansı: `{{fig:d01}}`, bölüm referansı: `{{sec:9}}`
- Callout: `::: not` / `::: dikkat` / `::: saha` / `::: pasa` / `::: ogren`
- Her bölüm `# Bölüm N — Başlık` ile başlar; h2'ler otomatik "N.M" numarası alır.
- SVG şemalarda sınıflar: `blk`, `blk-clk`, `blk-sysref`, `lbl`, `lbl-s`, `pin`,
  `pin-clk`, `pin-sysref`, `w-clk`, `w-sysref`, `w-data`, `w-ctrl`, `w-ince`;
  ok uçları şablondaki ortak marker'lar: `url(#arw-clk)`, `url(#arw-sysref)`,
  `url(#arw-data)`, `url(#arw-ctrl)`, `url(#arw-ince)`.

## Build

- `npm run build` → `dist/index.html` (tek, self-contained dosya)
- Her faz sonunda: build hatasız + git commit (geri dönüş noktası).
