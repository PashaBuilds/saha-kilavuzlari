// ============================================================================
// SAHA KILAVUZLARI — KAYIT DOSYASI
// ----------------------------------------------------------------------------
// Hub sayfası (index.html) kartları ve "Buradan başla" bandını bu listeden
// üretir. Yeni bir belge eklemek için bu listeye kayıt ekle; tasarıma dokunma.
//
// İki tür vardır:
//   tur: "kilavuz"  (varsayılan) → referans eseri; alttaki kart ızgarasında.
//   tur: "yolculuk"               → rehberli müfredat; üstteki "Buradan başla"
//                                   bandında, kendi sıcak tasarımıyla render edilir.
//
// Ortak alanlar:
//   sira        : Diziliş/numara sırası (kılavuzlar SK-01, SK-02, ...)
//   slug        : kilavuzlar/<slug>/index.html hedef klasör adı
//   kaynak      : Besleyen repo klasör adı (varsayılan "<slug>-saha-kilavuzu").
//                 guncelle.py hangi repodan besleneceğini buradan bilir; son eki
//                 taşımayan repolar (ör. gomulu-oryantasyon) bunu açıkça yazar.
//   baslik      : Başlık
//   aciklama    : 2-3 cümlelik tanıtım (kim için, ne anlatıyor)
//   etiketler   : 4-6 kısa teknik etiket
//   bolum       : İnsan-okur bölüm özeti ("17 bölüm + 2 ek" gibi)
//   bolumSayi   : Sayısal bölüm adedi (hero istatistikleri yalnızca kılavuzları toplar)
//   sema        : Sayısal şema/figür adedi
//   kelime      : Yaklaşık kelime sayısı (sayısal)
//   boyut       : Dosya boyutu — guncelle.py otomatik günceller
//   guncelleme  : ISO tarih — guncelle.py otomatik günceller
//   yol         : Karttan açılacak dosya (file:// uyumu için açık index.html)
//   renk        : Vurgu tonu, 0-360 arası hue açısı
//                 (kullanılanlar: 285 mor/RF, 160 turkuaz/Ethernet,
//                  25 amber/Lokal-LLM, 40 altın/Oryantasyon — boşta: 210, 340)
//   motif       : Kart deseni: "analog" | "digital" | "sinir" | "varsayilan"
//
// Yalnızca "yolculuk" türüne özel alanlar:
//   altBaslik   : Başlığın altındaki serif alt-başlık
//   lab         : Uygulamalı lab sayısı
//   final       : Bitirme görevi etiketi ("Mezuniyet Görevi" gibi)
//   rota        : Yolculuğun durakları (bant altındaki rota rayı bundan çizilir)
//   gozkasi     : Bant üstü küçük etiket (boşsa "Rehberli Yolculuk · Yeni başlayanlar için")
//   labEtiket   : Lab birim metni (boşsa "uygulamalı lab")
//   cta         : Buton metni (boşsa "Yolculuğa başla")
//                 — bu üç alan belgenin diliyle uyumu içindir; belge İngilizceyse
//                   İngilizce yaz. Boş bırakılan alan Türkçe varsayılana düşer.
// ============================================================================

window.KILAVUZLAR = [
  {
    tur: "yolculuk",
    sira: 0,
    slug: "oryantasyon",
    kaynak: "gomulu-oryantasyon",
    baslik: "Introduction to Embedded Systems",
    altBaslik: "A Team Onboarding Journey",
    gozkasi: "Guided Journey · For newcomers",
    aciklama:
      "A hand-holding curriculum for the fresh graduate joining the team on " +
      "day one. A ZCU111 board sits on the desk; reading chapters and hands-on " +
      "labs alternate — from the Zynq PS/PL split to register programming, " +
      "from interrupts to I2C/SPI, from FreeRTOS to Vitis debug. Not a " +
      "reference; a journey that turns \"this board scares me\" into \"I get " +
      "work done with this board\" in two weeks.",
    etiketler: ["Zynq · ZCU111", "Bare-metal C", "Registers & Interrupts", "I2C · SPI · UART", "FreeRTOS", "Vitis Debug"],
    rota: ["Welcome", "LED", "UART", "Interrupt", "Timer", "I2C", "AXI GPIO", "FreeRTOS", "Queue", "Bug Hunt", "Capstone"],
    bolum: "17 chapters",
    bolumSayi: 17,
    lab: 10,
    labEtiket: "hands-on labs",
    sema: 25,
    kelime: 33709,
    final: "Capstone Project",
    cta: "Start the journey",
    boyut: "572 KB",
    guncelleme: "2026-07-14",
    yol: "kilavuzlar/oryantasyon/index.html",
    renk: 40,
  },
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
  {
    sira: 3,
    slug: "lokal-llm",
    baslik: "Lokal LLM Dünyası",
    aciklama:
      "Model kartındaki \"70B, MoE, Q4_K_M, 128K context\" ifadesini söküp " +
      "kendi donanımında hangi modelin kaç token/s koşacağını öngörmek için: " +
      "mimariler, quantization, bellek hesabı, Ollama/LM Studio ve lokal API " +
      "ekosistemi — modeli kendi makinesinde koşturmak isteyen teknik meraklı için.",
    etiketler: ["Quantization", "MoE & Mimariler", "VRAM Hesabı", "Ollama & LM Studio", "Lokal API"],
    bolum: "14 bölüm + sözlük & referans",
    bolumSayi: 16,
    sema: 23,
    kelime: 15910,
    boyut: "255 KB",
    guncelleme: "2026-07-12",
    yol: "kilavuzlar/lokal-llm/index.html",
    renk: 25,
    motif: "sinir",
  },
];
