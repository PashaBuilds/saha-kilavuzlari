/* W-05 — Mixer frekans planı ve image gezgini
   Kontroller: RF, hedef IF, enjeksiyon (low/high-side), IF filtre bandı, preselector bandı, spur mertebesi
   Çıktı: LO, IF, image, evrilme; RF ekseninde preselector/image/half-IF ve IF'e düşüren giriş frekansları;
           IF ekseninde m×n ürünleri ve IF filtresi bandı. Sayılar Bölüm 6 / g-62 ile aynı formüllerden. */

/* Yerel yardımcılar (dsp-core'da yok — rapora yazıldı):
   mixerUrunleri(rf, lo, M): |m·rf − n·lo| ürünleri, temsili seviye (dBc) ile.
   ifeDusenGirisler(lo, ifHz, M): m·f − n·lo = ±IF olan giriş frekansları. */
function W05_mixerUrunleri(rf, lo, M) {
  var out = [];
  for (var m = 0; m <= M; m++) {
    for (var n = 0; n <= M; n++) {
      if (m === 0 && n === 0) continue;
      var f1 = Math.abs(m * rf - n * lo), f2 = m * rf + n * lo;
      // temsili seviye: her ek RF mertebesi −20 dB, her ek LO mertebesi −10 dB; sızıntılar −30 / −40 dBc (kurgusal)
      var sev;
      if (m === 0) sev = -30 - 10 * (n - 1);            // LO sızıntısı ve harmonikleri
      else if (n === 0) sev = -40 - 20 * (m - 1);       // RF sızıntısı ve harmonikleri
      else sev = -20 * (m - 1) - 10 * (n - 1);
      out.push({ m: m, n: n, f: f1, sev: sev, tur: "fark" });
      if (m > 0 && n > 0) out.push({ m: m, n: n, f: f2, sev: sev - 0.0, tur: "toplam" });
    }
  }
  return out;
}
function W05_ifeDusenGirisler(lo, ifHz, M) {
  var out = [];
  for (var m = 1; m <= M; m++) {
    for (var n = 0; n <= M; n++) {
      for (var s = -1; s <= 1; s += 2) {
        var f = (n * lo + s * ifHz) / m;
        if (f > 0) out.push({ m: m, n: n, f: f, isaret: s });
      }
    }
  }
  return out;
}

WK.kaydet("w05", function (w) {
  var S = w.S;
  var rfRef = S.sinyal ? S.sinyal.rf_hz : 9.4e9, ifRef = S.on_uc ? S.on_uc.if_hz : 1.8e9;
  var bwRef = S.ddc ? S.ddc.cikis_bant_mhz * 2e6 : 300e6;
  WK.kaydirici(w, { ad: "rf", etiket: "RF (sinyal)", min: 500e6, max: 18000e6, adim: 10e6, deger: rfRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "if", etiket: "hedef IF", min: 50e6, max: 4000e6, adim: 10e6, deger: ifRef, olcek: 1e6, birim: "MHz" });
  WK.secim(w, { ad: "yan", etiket: "enjeksiyon", secenekler: [["low", "low-side (LO < RF)"], ["high", "high-side (LO > RF)"]], deger: "low", metin: true });
  var kapat = WK.grup(w, "Filtreler ve spur");
  WK.kaydirici(w, { ad: "ifbw", etiket: "IF filtre bandı", min: 20e6, max: 1200e6, adim: 10e6, deger: bwRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "prebw", etiket: "preselector bandı (RF etrafında)", min: 100e6, max: 8000e6, adim: 100e6, deger: 3000e6, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "M", etiket: "en yüksek m, n mertebesi", min: 1, max: 5, adim: 1, deger: 3, birim: "", tamsayi: true });
  kapat();

  var pRF = WK.panel(w, 230), pIF = WK.panel(w, 250);

  function ciz() {
    var p = w.param;
    var rf = p.rf, ifHz = p.if, high = p.yan === "high";
    var lo = high ? rf + ifHz : rf - ifHz;
    if (lo <= 0) lo = 1e6;
    var image = 2 * lo - rf;
    var preA = rf - p.prebw / 2, preB = rf + p.prebw / 2;
    var halfIF = (rf + lo) / 2;
    var M = p.M;
    // ---- RF ekseni
    WK.temizle(pRF);
    var xmax = Math.max(rf, lo, image, preB) * 1.15 / 1e6;
    var g1 = WK.grafik(pRF, { W: 640, H: 230, xmin: 0, xmax: xmax, ymin: 0, ymax: 1.15, kenar: { sol: 40, sag: 14, ust: 22, alt: 34 } });
    g1.eksenler({ xAdet: 8, yAdet: 1, xAd: "RF ekseni (MHz)", baslik: "Girişler: RF, LO, image, preselector ve IF'e düşüren spur girişleri", yFmt: function () { return ""; } });
    g1.bant(preA / 1e6, preB / 1e6, "w-dolgu-altin");
    g1.metin(g1.px(Math.max(preA, 0) / 1e6) + 4, g1.y1 + 12, "preselector", "w-not");
    function bar(f, h, kls, et, dy) {
      var x = g1.px(f / 1e6);
      g1.ekle("line", { x1: x, y1: g1.py(0), x2: x, y2: g1.py(h), "class": kls, "stroke-width": 3 });
      if (et) g1.metin(x + 3, g1.py(h) - 3 + (dy || 0), et, "w-not");
    }
    // spur girişleri
    var girisler = W05_ifeDusenGirisler(lo, ifHz, M);
    var icerde = 0;
    girisler.forEach(function (s) {
      if (s.m === 1 && s.n === 1) return;
      if (s.f / 1e6 > xmax) return;
      var inPre = s.f >= preA && s.f <= preB;
      if (inPre) icerde++;
      bar(s.f, inPre ? 0.55 : 0.3, "w-cizgi-kirmizi", (inPre ? s.m + "×" + s.n : ""), 0);
    });
    bar(lo, 1.0, "w-cizgi-gri", "LO " + WK.fmt(lo / 1e6, 0));
    bar(rf, 0.95, "w-cizgi-sinyal", "RF " + WK.fmt(rf / 1e6, 0));
    var imgIn = image >= preA && image <= preB;
    bar(image, 0.8, "w-cizgi-kirmizi", "image " + WK.fmt(image / 1e6, 0) + (imgIn ? " (bant içinde!)" : ""), 0);
    // ---- IF ekseni
    WK.temizle(pIF);
    var urunler = W05_mixerUrunleri(rf, lo, M);
    var ifmax = Math.max(3 * ifHz, lo * 0.6) / 1e6;
    var g2 = WK.grafik(pIF, { W: 640, H: 250, xmin: 0, xmax: ifmax, ymin: -80, ymax: 5, kenar: { sol: 44, sag: 14, ust: 22, alt: 34 } });
    g2.eksenler({ xAdet: 8, yAdet: 5, xAd: "mixer çıkışı (MHz)", yAd: "temsili dBc", baslik: "Mixer çıkışı: |m·RF ± n·LO| ürünleri ve IF filtresi bandı (seviyeler temsilî)" });
    var fa = (ifHz - p.ifbw / 2) / 1e6, fb = (ifHz + p.ifbw / 2) / 1e6;
    g2.bant(fa, fb, "w-dolgu-altin");
    g2.metin(g2.px(Math.max(fa, 0)) + 4, g2.y1 + 12, "IF filtre", "w-not");
    var filtrede = [];
    urunler.forEach(function (u) {
      if (u.f / 1e6 > ifmax) return;
      var x = g2.px(u.f / 1e6), istenen = (u.m === 1 && u.n === 1 && u.tur === "fark");
      var inF = u.f >= ifHz - p.ifbw / 2 && u.f <= ifHz + p.ifbw / 2;
      if (inF && !istenen) filtrede.push(u);
      var kls = istenen ? "w-cizgi-sinyal" : (inF ? "w-cizgi-kirmizi" : "w-cizgi-gri");
      g2.ekle("line", { x1: x, y1: g2.py(-80), x2: x, y2: g2.py(Math.max(u.sev, -79)), "class": kls, "stroke-width": istenen ? 4 : 2 });
      if (istenen || inF || (u.m <= 1 && u.n <= 1)) {
        var et = istenen ? "IF " + WK.fmt(u.f / 1e6, 0) : (u.m + "×" + u.n + (u.tur === "toplam" ? "+" : ""));
        g2.metin(x + 3, g2.py(Math.max(u.sev, -79)) - 3, et, "w-not");
      }
    });
    // sonuçlar
    var sonuc = {
      "LO": WK.fmtHz(lo) + (high ? " (high-side)" : " (low-side)"),
      "IF = |RF − LO|": WK.fmtHz(Math.abs(rf - lo)),
      "image = 2·LO − RF": (imgIn ? "!" : "+") + WK.fmtHz(image) + (imgIn ? " — preselector İÇİNDE" : " — preselector dışında"),
      "evrilme": high ? "!EVET (LO − RF: spektrum ayna, LFM eğimi ters)" : "+hayır (RF − LO: düz)",
      "half-IF girişi (2×2)": WK.fmtHz(halfIF) + ((halfIF >= preA && halfIF <= preB) ? " — bant içinde, mixer bastırmasına kalır" : " — bant dışında"),
      "IF'e düşüren spur girişi (bant içi)": (icerde > 0 ? "!" : "+") + icerde + " adet (m,n ≤ " + M + ")",
      "IF filtresine düşen ürün": (filtrede.length > 0 ? "!" : "+") + filtrede.length + " adet",
      "image uzaklığı 2·IF": WK.fmtHz(2 * ifHz) + " (preselector yarı bandı " + WK.fmtHz(p.prebw / 2) + ")"
    };
    WK.sonucYaz(w, sonuc);
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { rf: rfRef, if: ifRef, yan: "low", ifbw: bwRef, prebw: 3000e6, M: 3 } },
      { ad: "High-side", param: { rf: rfRef, if: ifRef, yan: "high", ifbw: bwRef, prebw: 3000e6, M: 3 } },
      { ad: "Image içeride (IF düşük)", param: { rf: rfRef, if: 200e6, yan: "low", ifbw: 100e6, prebw: 3000e6, M: 3 } },
      { ad: "Yüksek mertebe (M = 5)", param: { rf: rfRef, if: ifRef, yan: "low", ifbw: bwRef, prebw: 3000e6, M: 5 } }
    ]
  };
});
