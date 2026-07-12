// ============================================================================
// SAHA KILAVUZLARI — KAYIT DOSYASI
// ----------------------------------------------------------------------------
// Hub sayfası (index.html) kartları bu listeden üretir. Yeni bir kılavuz
// eklemek için bu listeye bir kayıt ekle; tasarıma dokunmana gerek yok.
//
// Alanlar:
//   sira        : Kartların diziliş/numara sırası (SK-01, SK-02, ...)
//   slug        : kilavuzlar/<slug>/index.html klasör adı
//   baslik      : Kart başlığı
//   aciklama    : 2-3 cümlelik tanıtım (kim için, ne anlatıyor)
//   etiketler   : 4-6 kısa teknik etiket
//   bolum       : İnsan-okur bölüm özeti ("17 bölüm + 2 ek" gibi)
//   bolumSayi   : Sayısal bölüm adedi (hero istatistikleri toplar)
//   sema        : Sayısal şema/figür adedi (hero istatistikleri toplar)
//   kelime      : Yaklaşık kelime sayısı (sayısal, hero toplar)
//   boyut       : Dosya boyutu — guncelle.py otomatik günceller
//   guncelleme  : ISO tarih — guncelle.py otomatik günceller
//   yol         : Karttan açılacak dosya (file:// uyumu için açık index.html)
//   renk        : Kart vurgu tonu, 0-360 arası hue açısı
//                 (kullanılanlar: 285 mor/RF, 160 turkuaz/Ethernet —
//                  yeni kılavuzda boş bir açı seç: 25 amber, 210 mavi, 340 gül)
//   motif       : Kart arka plan deseni: "analog" | "digital" | "varsayilan"
// ============================================================================

window.KILAVUZLAR = [
  {
    sira: 1,
    slug: "rf-sampling",
    baslik: "Doğrudan RF Örnekleme ve Ön Uç Tasarımı",
    aciklama:
      "GHz hızında örnekleme yapan RF ön uçların uçtan uca anatomisi: " +
      "ADC/DAC kavramlarından SERDES'e, JESD204B/C'den clock kalitesi ve " +
      "SYSREF'e. TI ve ADI zincirleri, Versal GT + JESD IP, bring-up ve " +
      "debug akışıyla — register yazan mühendisin gözünden.",
    etiketler: ["JESD204B/C", "SERDES", "SYSREF & Clocking", "TI · ADI Zincirleri", "Versal GT"],
    bolum: "18 bölüm + sözlük & kaynakça",
    bolumSayi: 20,
    sema: 18,
    kelime: 22937,
    boyut: "2,1 MB",
    guncelleme: "2026-07-10",
    yol: "kilavuzlar/rf-sampling/index.html",
    renk: 285,
    motif: "analog",
  },
  {
    sira: 2,
    slug: "ethernet",
    baslik: "Ethernet ve Ağ İletişimi",
    aciklama:
      "Bir paketin karttan çıkıp sunucuya varana kadarki yolculuğu katman " +
      "katman: PHY ve MAC'ten ARP, IP, TCP/UDP, DNS ve TLS'e. Wireshark'ta " +
      "frame söken, \"link var ama ping yok\" arızasını sistematik teşhis " +
      "eden gömülü yazılımcı için.",
    etiketler: ["TCP/IP", "ARP & DHCP", "DNS & TLS", "Wireshark", "Gömülü Ethernet"],
    bolum: "17 bölüm + 2 ek",
    bolumSayi: 19,
    sema: 23,
    kelime: 17646,
    boyut: "302 KB",
    guncelleme: "2026-07-12",
    yol: "kilavuzlar/ethernet/index.html",
    renk: 160,
    motif: "digital",
  },
];
