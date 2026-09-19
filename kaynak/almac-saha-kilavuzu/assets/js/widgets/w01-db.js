/* W-01 — dB dönüştürücü
   Kontroller: seviye (dBm), yük direnci, ADC tam ölçeği (dBm), oran ve oranın türü (güç/genlik)
   Çıktı: dBm ↔ mW/W ↔ Vrms/Vpp (R Ω) ↔ dBFS; oran ↔ dB (10·log vs 20·log); dB merdiveni üzerinde konum */
WK.kaydet("w01", function (w) {
  var S = w.S;
  var fsRef = S.adc ? S.adc.tam_olcek_dbm : 4;
  var girisRef = S.sinyal ? S.sinyal.seviye_dbm_giris : -60;
  var bwRef = S.ddc ? S.ddc.cikis_bant_mhz * 2e6 : 300e6;
  var nfRef = S.on_uc ? S.on_uc.nf_toplam_db : 6;

  WK.kaydirici(w, { ad: "dbm", etiket: "seviye", min: -180, max: 40, adim: 0.1, deger: girisRef, birim: "dBm", hane: 1 });
  WK.kaydirici(w, { ad: "R", etiket: "yük direnci", min: 25, max: 600, adim: 1, deger: 50, birim: "Ω", tamsayi: true });
  WK.kaydirici(w, { ad: "fs", etiket: "ADC tam ölçek (0 dBFS)", min: -20, max: 20, adim: 0.5, deger: fsRef, birim: "dBm", hane: 1 });
  var kapat = WK.grup(w, "Oran → dB");
  WK.kaydirici(w, { ad: "oran", etiket: "oran", min: 0.001, max: 1e6, deger: 2, log: true, hane: 3 });
  WK.secim(w, { ad: "tur", etiket: "oranın türü", secenekler: [["guc", "güç oranı (10·log)"], ["genlik", "genlik / gerilim oranı (20·log)"]], deger: "guc", metin: true });
  kapat();

  var merdiven = WK.panel(w, 300), oranP = WK.panel(w, 200);

  function siFmt(x, birim) {
    var tab = [[1, ""], [1e-3, "m"], [1e-6, "µ"], [1e-9, "n"], [1e-12, "p"], [1e-15, "f"], [1e-18, "a"], [1e-21, "z"]];
    for (var k = 0; k < tab.length; k++) if (x >= tab[k][0] * 0.9995) return (x / tab[k][0]).toPrecision(3).replace(/\.?0+$/, "") + " " + tab[k][1] + birim;
    return x.toExponential(2) + " " + birim;
  }

  function ciz() {
    var p = w.param;
    var wW = DSP.dbmToW(p.dbm);
    var vrms = DSP.dbmToVrms(p.dbm, p.R);
    var vpp = vrms * 2 * Math.SQRT2;
    var dbfs = p.dbm - p.fs;
    var taban = DSP.gurultuTabaniDbm(bwRef, nfRef);
    // --- merdiven
    WK.temizle(merdiven);
    var g = WK.grafik(merdiven, { W: 640, H: 300, xmin: 0, xmax: 10, ymin: -180, ymax: 40, kenar: { sol: 60, sag: 14, ust: 22, alt: 26 } });
    g.eksenler({ xTik: [], yAdet: 11, yAd: "dBm", baslik: "dB merdiveni (referans senaryo işaretli)" });
    // gürültü altı ve doyum üstü bölgeleri
    var altBant = g.ekle("rect", { x: g.x0, y: g.py(taban), width: g.x1 - g.x0, height: g.y0 - g.py(taban), "class": "w-dolgu-gurultu" });
    g.ekle("rect", { x: g.x0, y: g.y1, width: g.x1 - g.x0, height: g.py(p.fs) - g.y1, "class": "w-dolgu-kirmizi" });
    g.yatay(p.fs, "w-cizgi-altin", "0 dBFS = " + p.fs.toFixed(1) + " dBm (ADC tam ölçek)");
    g.yatay(taban, "w-cizgi-kirmizi", "gürültü tabanı " + taban.toFixed(1) + " dBm (300 MHz, NF " + nfRef + " dB)");
    g.yatay(0, "w-cizgi-gri", "0 dBm = 1 mW");
    g.yatay(-174, "w-cizgi-gri", "kTB −174 dBm/Hz");
    // seviye işareti
    var yy = g.py(p.dbm);
    g.ekle("line", { x1: g.x0, y1: yy, x2: g.x1, y2: yy, "class": "w-cizgi-sinyal" });
    g.nokta(2, p.dbm, 6);
    g.metin(g.px(2) + 10, yy - 6, p.dbm.toFixed(1) + " dBm = " + siFmt(wW, "W") + " = " + siFmt(vrms, "Vrms") + " (" + p.R + " Ω)", "w-mono");
    // dBFS payı oku
    var yfs = g.py(p.fs);
    g.ekle("line", { x1: g.px(8), y1: yfs, x2: g.px(8), y2: yy, "class": dbfs > 0 ? "w-cizgi-kirmizi" : "w-cizgi-yesil" });
    g.metin(g.px(8) + 5, (yfs + yy) / 2 + 4, (dbfs > 0 ? "+" : "") + dbfs.toFixed(1) + " dBFS", "w-not");
    void altBant;
    // --- oran paneli
    WK.temizle(oranP);
    var g2 = WK.grafik(oranP, { W: 640, H: 200, xmin: -3, xmax: 6, ymin: -60, ymax: 120, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    g2.eksenler({ xAdet: 9, yAdet: 6, xAd: "oran (log10)", yAd: "dB", baslik: "10·log10 (güç) ve 20·log10 (genlik)", xFmt: function (v) { return "10^" + v; } });
    var xs = [], y10 = [], y20 = [];
    for (var k = 0; k <= 90; k++) { var e = -3 + k / 10; xs.push(e); y10.push(10 * e); y20.push(20 * e); }
    g2.cizgi(xs, y10, "w-cizgi-sinyal"); g2.cizgi(xs, y20, "w-cizgi-q");
    g2.metin(g2.px(5.2), g2.py(52) - 4, "10·log (güç)", "w-not");
    g2.metin(g2.px(4.2), g2.py(84) - 4, "20·log (genlik)", "w-not");
    var lo = Math.log10(p.oran), dbOran = (p.tur === "guc" ? 10 : 20) * lo;
    g2.nokta(lo, dbOran, 5);
    g2.metin(g2.px(lo) + 8, g2.py(dbOran) + 4, "×" + (p.oran >= 100 ? p.oran.toPrecision(3) : p.oran.toPrecision(3)) + " → " + dbOran.toFixed(2) + " dB", "w-mono");
    // sonuçlar
    var uyariFs = dbfs > 0 ? "!" + dbfs.toFixed(1) + " dBFS — ADC doyar (clipping)" : (dbfs > -1 ? "!" + dbfs.toFixed(1) + " dBFS — tam ölçeğe çok yakın" : dbfs.toFixed(1) + " dBFS");
    WK.sonucYaz(w, {
      "güç": siFmt(wW, "W") + " (" + wW.toExponential(2) + " W)",
      "Vrms": siFmt(vrms, "V"),
      "Vpp": siFmt(vpp, "V"),
      "dBW": (p.dbm - 30).toFixed(1) + " dBW",
      "dBFS": uyariFs,
      "gürültü tabanına göre": (p.dbm - taban >= 0 ? "+" : "") + (p.dbm - taban).toFixed(1) + " dB (SNR, 300 MHz)",
      "oran → dB": "×" + p.oran.toPrecision(3) + " = " + dbOran.toFixed(2) + " dB (" + (p.tur === "guc" ? "10·log" : "20·log") + ")",
      "dB → oran": dbOran.toFixed(2) + " dB = güç ×" + DSP.lin10(dbOran).toPrecision(3) + " = genlik ×" + DSP.lin20(dbOran).toPrecision(3)
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { dbm: girisRef, R: 50, fs: fsRef, oran: 2, tur: "guc" } },
      { ad: "IF çıkışı (+40 dB kazanç)", param: { dbm: girisRef + (S.on_uc ? S.on_uc.kazanc_toplam_db : 40), R: 50, fs: fsRef, oran: 10000, tur: "guc" } },
      { ad: "ADC tam ölçek", param: { dbm: fsRef, R: 50, fs: fsRef, oran: 1, tur: "guc" } },
      { ad: "Gürültü tabanı", param: { dbm: -83.2, R: 50, fs: fsRef, oran: 2, tur: "genlik" } },
      { ad: "1 W verici", param: { dbm: 30, R: 50, fs: fsRef, oran: 1000, tur: "guc" } }
    ]
  };
});
