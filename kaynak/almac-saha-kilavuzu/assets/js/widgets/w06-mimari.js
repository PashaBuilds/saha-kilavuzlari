/* W-06 — Mimari karşılaştırıcı
   Kontroller: mimari A, mimari B, öncelik (senaryoya göre öner)
   Çıktı: yedi özellik çubuğu yan yana (A mavi, B altın), blok listeleri, önceliğe göre sıralı öneri.
   Puanlar (0–5) Bölüm 7'deki mimari kartlarının ::ozellik:: satırlarıyla birebir aynıdır; karmaşıklıkta 5 = en pahalı. */
WK.kaydet("w06", function (w) {
  var OZ = [["bw", "Anlık BW"], ["hass", "Hassasiyet"], ["dr", "Dinamik aralık"], ["esz", "Eşzamanlı sinyal"], ["frek", "Frekans doğruluğu"], ["poi", "POI"], ["karm", "Karmaşıklık / maliyet"]];
  var MIM = [
    { id: 1, ad: "M-1 CVR / TRF", p: { bw: 5, hass: 1, dr: 2, esz: 0, frek: 0, poi: 5, karm: 0 },
      blok: ["anten", "geniş BPF", "(RF amp)", "kristal dedektör", "video filtre", "log video amp", "eşik"] },
    { id: 2, ad: "M-2 Süperheterodin (taramalı)", p: { bw: 1, hass: 5, dr: 4, esz: 1, frek: 4, poi: 1, karm: 2 },
      blok: ["anten", "ayarlı preselector", "LNA", "mixer 1 + LO₁ (tarama)", "IF₁ filtre", "mixer 2 + LO₂", "dar IF₂ filtre", "IF/log amp", "dedektör"] },
    { id: 3, ad: "M-3 Zero-IF / homodyne", p: { bw: 3, hass: 3, dr: 3, esz: 2, frek: 3, poi: 3, karm: 2 },
      blok: ["anten", "BPF", "LNA", "I/Q mixer (LO = RF, 0°/90°)", "baseband LPF ×2", "VGA ×2", "ADC ×2 (düşük fs)"] },
    { id: 4, ad: "M-4 IFM", p: { bw: 5, hass: 2, dr: 3, esz: 0, frek: 4, poi: 5, karm: 2 },
      blok: ["anten", "limiter / amp", "bölücü", "gecikme hattı τ", "faz korelatörü (cos, sin)", "ADC ×2", "atan2 tablosu"] },
    { id: 5, ad: "M-5 Analog kanallaştırılmış", p: { bw: 5, hass: 3, dr: 3, esz: 4, frek: 2, poi: 5, karm: 4 },
      blok: ["anten", "LNA", "güç bölücü 1:N", "N × BPF", "N × dedektör", "N × video amp + eşik", "kodlayıcı"] },
    { id: 6, ad: "M-6 Compressive / akusto-optik", p: { bw: 4, hass: 3, dr: 2, esz: 4, frek: 3, poi: 4, karm: 4 },
      blok: ["anten", "LNA", "mixer + chirp LO", "IF filtre", "dispersif hat (SAW)", "dedektör", "eşik + zaman ölçümü"] },
    { id: 7, ad: "M-7 Sayısal IF (referans)", p: { bw: 3, hass: 4, dr: 4, esz: 3, frek: 5, poi: 3, karm: 3 },
      blok: ["anten", "limiter", "LNA", "preselector", "mixer + LO", "IF filtre + amp", "AAF", "ADC 2.4 GSPS", "NCO ⊗", "FIR/CIC ↓8", "zarf → CFAR → PDW"] },
    { id: 8, ad: "M-8 Direct RF sampling", p: { bw: 4, hass: 3, dr: 3, esz: 4, frek: 5, poi: 4, karm: 3 },
      blok: ["anten", "limiter", "LNA", "Nyquist bandı BPF", "att / AGC", "ADC sürücü", "RF ADC (çok GSPS)", "NCO ⊗", "DDC"] },
    { id: 9, ad: "M-9 Sayısal kanallaştırılmış", p: { bw: 5, hass: 4, dr: 4, esz: 5, frek: 5, poi: 5, karm: 5 },
      blok: ["anten", "LNA", "BPF", "geniş bant ADC", "seri→paralel ↓M", "polyphase FIR bankası", "M-nokta FFT", "M × (zarf + CFAR)"] },
    { id: 10, ad: "M-10 Monobit", p: { bw: 5, hass: 2, dr: 1, esz: 1, frek: 4, poi: 5, karm: 1 },
      blok: ["anten", "limiter / amp", "BPF", "1-bit ADC (karşılaştırıcı)", "monobit FFT (çarpımsız)", "tepe bul"] }
  ];
  var secenekler = MIM.map(function (m) { return [String(m.id), m.ad]; });
  WK.secim(w, { ad: "a", etiket: "mimari A (mavi)", secenekler: secenekler, deger: "7", metin: true });
  WK.secim(w, { ad: "b", etiket: "mimari B (altın)", secenekler: secenekler, deger: "8", metin: true });
  WK.secim(w, { ad: "oncelik", etiket: "senaryoya göre öner — öncelik", secenekler: [
    ["denge", "dengeli (hepsi eşit)"], ["bw", "anlık BW / POI (hiçbir darbeyi kaçırma)"], ["hass", "hassasiyet (en zayıf sinyal)"],
    ["esz", "eşzamanlı sinyal (yoğun ortam)"], ["maliyet", "maliyet / basitlik"]], deger: "denge", metin: true });

  // öncelik ağırlıkları (karm negatif: pahalı olan cezalandırılır)
  var AGIRLIK = {
    denge: { bw: 1, hass: 1, dr: 1, esz: 1, frek: 1, poi: 1, karm: -1 },
    bw: { bw: 3, hass: 0.5, dr: 0.5, esz: 1, frek: 0.5, poi: 2, karm: -1 },
    hass: { bw: 0.5, hass: 3, dr: 2, esz: 0.5, frek: 1, poi: 0.5, karm: -0.5 },
    esz: { bw: 1, hass: 0.5, dr: 1, esz: 3, frek: 1, poi: 1, karm: -0.5 },
    maliyet: { bw: 1, hass: 0.5, dr: 0.5, esz: 0.5, frek: 0.5, poi: 1, karm: -3 }
  };
  function puan(m, onc) {
    var a = AGIRLIK[onc] || AGIRLIK.denge, s = 0;
    for (var k in a) s += a[k] * (k === "karm" ? m.p.karm : m.p[k]);
    return s;
  }
  function bul(id) { for (var i = 0; i < MIM.length; i++) if (String(MIM[i].id) === String(id)) return MIM[i]; return MIM[6]; }

  var pBar = WK.panel(w, 280), pBlok = WK.panel(w, 210);

  function ciz() {
    var A = bul(w.param.a), B = bul(w.param.b), onc = w.param.oncelik;
    // ---- çubuklar
    WK.temizle(pBar);
    var g = WK.grafik(pBar, { W: 640, H: 280, xmin: 0, xmax: 5, ymin: 0, ymax: OZ.length, kenar: { sol: 150, sag: 14, ust: 24, alt: 30 } });
    g.eksenler({ xAdet: 6, yAdet: 1, xAd: "puan (0–5; karmaşıklıkta 5 = en pahalı)", baslik: A.ad + "  ↔  " + B.ad, yFmt: function () { return ""; }, xFmt: function (v) { return String(v); } });
    var satirH = (g.y0 - g.y1) / OZ.length;
    OZ.forEach(function (oz, i) {
      var yTop = g.y1 + i * satirH;
      g.metin(g.x0 - 6, yTop + satirH / 2 + 4, oz[1], "w-etiket", "end");
      var va = A.p[oz[0]], vb = B.p[oz[0]];
      g.ekle("rect", { x: g.x0, y: yTop + satirH * 0.12, width: Math.max(0, g.px(va) - g.x0), height: satirH * 0.34, "class": "w-dolgu-sinyal" });
      g.ekle("rect", { x: g.x0, y: yTop + satirH * 0.54, width: Math.max(0, g.px(vb) - g.x0), height: satirH * 0.34, "class": "w-dolgu-altin" });
      g.metin(g.px(va) + 4, yTop + satirH * 0.12 + satirH * 0.28, String(va), "w-not");
      g.metin(g.px(vb) + 4, yTop + satirH * 0.54 + satirH * 0.28, String(vb), "w-not");
      if (i > 0) g.ekle("line", { x1: g.x0, y1: yTop, x2: g.x1, y2: yTop, "class": "w-izgara" });
    });
    // ---- blok listeleri
    WK.temizle(pBlok);
    var gb = WK.grafik(pBlok, { W: 640, H: 210, xmin: 0, xmax: 1, ymin: 0, ymax: 1, kenar: { sol: 8, sag: 8, ust: 20, alt: 6 } });
    gb.metin(gb.x0, 14, "Blok zinciri — A", "w-baslik");
    gb.metin(gb.x0 + 320, 14, "Blok zinciri — B", "w-baslik");
    function liste(x, bl) {
      var y = 34;
      for (var k = 0; k < bl.length; k++) { gb.metin(x, y, (k + 1) + ". " + bl[k], "w-etiket"); y += 15; }
    }
    liste(gb.x0, A.blok); liste(gb.x0 + 320, B.blok);
    // ---- öneri
    var sirali = MIM.slice().sort(function (m1, m2) { return puan(m2, onc) - puan(m1, onc); });
    var top = sirali.slice(0, 3).map(function (m, i) { return (i + 1) + ") " + m.ad + " [" + puan(m, onc).toFixed(1) + "]"; }).join("  ·  ");
    var pa = puan(A, onc), pb = puan(B, onc);
    var fark = OZ.filter(function (oz) { return A.p[oz[0]] !== B.p[oz[0]]; }).map(function (oz) { return oz[1] + " " + A.p[oz[0]] + "→" + B.p[oz[0]]; });
    WK.sonucYaz(w, {
      "öncelik": onc,
      "A puanı": pa.toFixed(1) + (pa >= pb ? " (+)" : ""),
      "B puanı": pb.toFixed(1) + (pb > pa ? " (+)" : ""),
      "öneri (ilk 3)": top,
      "A ↔ B farklar": fark.length ? fark.join(", ") : "+özdeş puanlar",
      "A blok sayısı": String(A.blok.length),
      "B blok sayısı": String(B.blok.length)
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { a: "7", b: "8", oncelik: "denge" } },
      { ad: "RWR: POI + maliyet", param: { a: "1", b: "4", oncelik: "maliyet" } },
      { ad: "ELINT: hassasiyet", param: { a: "2", b: "9", oncelik: "hass" } },
      { ad: "Yoğun ortam: eşzamanlı", param: { a: "9", b: "10", oncelik: "esz" } }
    ]
  };
});
