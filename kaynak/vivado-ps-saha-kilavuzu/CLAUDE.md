# CLAUDE.md — vivado-ps-saha-kilavuzu

Bu repo, *Vivado'yu Yazılımcı Gibi Okumak — PS Perspektifinden Sayısal Tasarım
Analizi Saha Kılavuzu* dokümanının üretim alanıdır.

**Tek başlangıç talimatı: [KICKOFF.md](KICKOFF.md).** Önce onu oku; proje
kimliği, görsel boru hattı, yazım kuralları, üretim akışı ve kalite çıtası
orada tanımlıdır.

## Bu oturumda geçerli ortam notları

- Makinede Vivado **2022.2** kurulu (KICKOFF 2023.2 der; 2023.2 bulunamadı,
  2022.2 ile ilerlenir ve doküman sürüm notu buna göre düşülür).
- ZCU111/RFSoC device desteği kurulu değil → Demo 1 **ZCU102**
  (`xilinx.com:zcu102:part0:3.4`, xczu9eg) üzerine kurulur. PS IP
  (`zynq_ultra_ps_e`) tüm UltraScale+ ailesinde aynıdır; doküman bunu not eder.
- VPK120 yok → Demo 2 **VCK190** (`xilinx.com:vck190:part0:3.1`, xcvc1902)
  üzerine kurulur (KICKOFF'un öngördüğü yedek).
- Demo 3 (MicroBlaze, Bölüm 9) **AC701** (`xilinx.com:ac701:part0:1.4`,
  xc7a200t) üzerine kurulur: KC705 (xc7k325t) bu makinede lisans dışı;
  Artix-7 WebPACK kapsamında olduğundan implementasyon + bitstream + MMI
  üretimi lisanssız koşar.

## Değişmez kurallar

1. Vivado projelerinde HİÇBİR değişiklik kaydedilmez; projeler her zaman
   `vivado/*/create_bd.tcl` scriptlerinden yeniden üretilir. Üretilen proje
   dosyaları `vivado/work/` altına düşer ve repo çıktısı sayılmaz.
2. `dist/index.html` tamamen self-contained üretilir: CSS/JS/SVG inline,
   screenshot'lar base64. İnternet bağımlılığı yok.
3. Konfig tabloları `assets/reports/` altındaki gerçek Tcl çıktılarından
   derlenir; elle uydurulmaz. Teyit edilemeyen iddia "doğrulanacak" işaretiyle
   bırakılır.
4. Build: `python build/build.py` → `dist/index.html` + eksik görsel raporu.

## Dizin haritası

KICKOFF §2'deki yapı geçerlidir. Ek olarak `vivado/work/` (üretilen projeler,
tekrar üretilebilir, silinebilir) kullanılır.
