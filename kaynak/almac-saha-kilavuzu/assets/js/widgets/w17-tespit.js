/* W-17 — Tespit laboratuvarı
   Kontroller: SNR, eşik (T/σ) ya da hedef Pfa, karar hızı (fs), Monte Carlo
   Çıktı: H0 Rayleigh / H1 Rician PDF'leri (lineer + log), taralı Pfa/Pd, ROC üzerinde nokta,
          saniyedeki yanlış alarm sayısı, Monte Carlo sayaçları vs teori */
WK.kaydet("w17", function (w) {
  var S = w.S, T = S.tespit || {}, fsRef = (S.ddc && S.ddc.cikis_fs_msps ? S.ddc.cikis_fs_msps : 300) * 1e6;
  var snrRef = T.snr_pd09_db || 13.2, pfaRef = T.pfa || 1e-6;

  WK.kaydirici(w, { ad: "snr", etiket: "SNR (tek örnek)", min: 0, max: 20, adim: 0.1, deger: snrRef, birim: "dB" });
  var kapat = WK.grup(w, "Eşik");
  WK.onay(w, { ad: "pfadan", etiket: "eşiği hedef Pfa'dan kur", deger: true });
  WK.secim(w, { ad: "pfaHedef", etiket: "hedef Pfa", secenekler: [["1e-3", "10⁻³"], ["1e-4", "10⁻⁴"], ["1e-6", "10⁻⁶ (referans)"], ["3.3333e-9", "3.3×10⁻⁹ (1/s @ 300 MSPS)"], ["1e-9", "10⁻⁹"]], deger: "1e-6", metin: true });
  WK.kaydirici(w, { ad: "esik", etiket: "eşik T/σ (elle)", min: 1, max: 8, adim: 0.01, deger: 5.26, birim: "σ", hane: 2 });
  kapat();
  WK.kaydirici(w, { ad: "fs", etiket: "karar hızı (örnek hızı)", min: 1e6, max: 2400e6, adim: 1e6, deger: fsRef, olcek: 1e6, birim: "MSPS" });
  WK.onay(w, { ad: "mc", etiket: "Monte Carlo (200 000 deneme, sabit tohum)", deger: true });

  var pPdf = WK.panel(w, 230), pLog = WK.panel(w, 200), pRoc = WK.panel(w, 230);
  var NPT = 400, MC_N = 200000;

  // Rician / Rayleigh yoğunluk (σ = 1): ln p(r) = ln r − (r² + A²)/2 + ln I0(A·r)
  function lnPdf(r, A) { if (r <= 0) return -Infinity; return Math.log(r) - (r * r + A * A) / 2 + (A > 0 ? DSP._lnI0(A * r) : 0); }

  function ciz() {
    var p = w.param;
    var pfaHedef = +p.pfaHedef;
    var Tsig = p.pfadan ? DSP.rayleighEsik(pfaHedef) : p.esik;
    if (p.pfadan) { p.esik = +Tsig.toFixed(2); w.tazele(); }
    var pfa = DSP.rayleighPfa(Tsig);
    var snrLin = DSP.lin10(p.snr), A = Math.sqrt(2 * snrLin);
    var pd = DSP.marcumQ1(A, Tsig);
    var far = DSP.far(pfa, p.fs);
    var rmax = Math.max(12, A + 5);
    var xs = [], h0 = [], h1 = [], l0 = [], l1 = [], k;
    for (k = 0; k < NPT; k++) {
      var r = rmax * (k + 0.5) / NPT;
      xs.push(r);
      var a0 = lnPdf(r, 0), a1 = lnPdf(r, A);
      h0.push(Math.exp(a0)); h1.push(Math.exp(a1));
      l0.push(a0 / Math.LN10); l1.push(a1 / Math.LN10);
    }
    // --- 1) lineer PDF
    WK.temizle(pPdf);
    var g1 = WK.grafik(pPdf, { W: 640, H: 230, xmin: 0, xmax: rmax, ymin: 0, ymax: 0.7, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    g1.eksenler({ xAd: "zarf r / σ", yAd: "yoğunluk", baslik: "H0 Rayleigh (gri) ve H1 Rician (mavi), SNR = " + p.snr.toFixed(1) + " dB — eşiğin sağı: Pd (mavi), Pfa (kırmızı)", xAdet: 6, yAdet: 4, yFmt: function (v) { return v.toFixed(1); } });
    g1.alan(xs, h0, 0, "w-dolgu-gurultu");
    var xsPd = [], ysPd = [], xsFa = [], ysFa = [];
    for (k = 0; k < NPT; k++) if (xs[k] >= Tsig) { xsPd.push(xs[k]); ysPd.push(h1[k]); xsFa.push(xs[k]); ysFa.push(h0[k]); }
    if (xsPd.length) { g1.alan(xsPd, ysPd, 0, "w-dolgu-sinyal"); g1.alan(xsFa, ysFa, 0, "w-dolgu-kirmizi"); }
    g1.cizgi(xs, h0, "w-cizgi-gri"); g1.cizgi(xs, h1, "w-cizgi-sinyal");
    g1.dikey(Tsig, "w-cizgi-altin", "T = " + Tsig.toFixed(2) + "σ");
    if (A > 0) g1.metin(g1.px(A) + 4, g1.y1 + 26, "A = σ√(2·SNR) = " + A.toFixed(2) + "σ", "w-not");
    // --- 2) log PDF
    WK.temizle(pLog);
    var g2 = WK.grafik(pLog, { W: 640, H: 200, xmin: 0, xmax: rmax, ymin: -10, ymax: 0.5, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    g2.eksenler({ xAd: "zarf r / σ", yAd: "log10 yoğunluk", baslik: "Aynı dağılımlar logaritmik eksende — kuyruk görünür olur", xAdet: 6, yAdet: 5, yFmt: function (v) { return v.toFixed(0); } });
    g2.cizgi(xs, l0, "w-cizgi-gri"); g2.cizgi(xs, l1, "w-cizgi-sinyal");
    g2.dikey(Tsig, "w-cizgi-altin", "Pfa = exp(−T²/2) = " + pfa.toExponential(1));
    g2.yatay(Math.log10(pfa), "w-cizgi-kirmizi", "10^" + Math.log10(pfa).toFixed(1));
    // --- 3) ROC
    WK.temizle(pRoc);
    var g3 = WK.grafik(pRoc, { W: 640, H: 230, xmin: 1e-9, xmax: 1, ymin: 0, ymax: 1, xlog: true, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    g3.eksenler({ xAd: "Pfa (log)", yAd: "Pd", baslik: "ROC — bu SNR'ın eğrisi ve seçilen eşiğin noktası", xTik: [1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1], yAdet: 5, xFmt: function (v) { return v === 1 ? "1" : "1e" + Math.round(Math.log10(v)); }, yFmt: function (v) { return v.toFixed(1); } });
    var rx = [], ry = [], sx = [], sy = [];
    for (k = 0; k <= 36; k++) {
      var tt = 0.5 + 6.3 * k / 36, pf = DSP.rayleighPfa(tt);
      if (pf < 1e-9) break;
      rx.push(pf); ry.push(DSP.marcumQ1(A, tt)); sx.push(pf); sy.push(pf);
    }
    g3.cizgi(sx, sy, "w-cizgi-gri"); g3.metin(g3.px(1e-3) - 60, g3.py(1e-3) - 6, "Pd = Pfa (yazı-tura)", "w-not");
    g3.cizgi(rx, ry, "w-cizgi-sinyal");
    g3.dikey(pfaRef, "w-cizgi-altin", "referans Pfa");
    if (pfa >= 1e-9) { g3.nokta(pfa, pd, 5, "w-nokta"); g3.metin(g3.px(pfa) + 8, g3.py(pd) + 4, "Pfa " + pfa.toExponential(1) + ", Pd " + pd.toFixed(3), "w-not"); }
    // --- Monte Carlo
    var mcTxt = { pfa: "kapalı", pd: "kapalı" };
    if (p.mc) {
      var rnd = DSP.prng(17), nFa = 0, nDet = 0, T2 = Tsig * Tsig;
      for (k = 0; k < MC_N; k++) {
        var gz = DSP.gaussKompleks(rnd, Math.SQRT2);         // bileşen σ = 1
        if (gz[0] * gz[0] + gz[1] * gz[1] > T2) nFa++;
        var i1 = gz[0] + A, q1 = gz[1];                       // sinyal I ekseninde (faz önemsiz)
        if (i1 * i1 + q1 * q1 > T2) nDet++;
      }
      var bekFa = pfa * MC_N;
      mcTxt.pfa = nFa + " yanlış alarm / " + MC_N.toLocaleString("tr-TR") + " (beklenen " + (bekFa < 10 ? bekFa.toFixed(2) : bekFa.toFixed(0)) + ")" + (bekFa >= 50 && Math.abs(nFa - bekFa) > 3 * Math.sqrt(bekFa) ? " !" : "");
      mcTxt.pd = (nDet / MC_N).toFixed(4) + " (teori " + pd.toFixed(4) + ")";
    }
    var snr09 = DSP.albersheim(0.9, pfa, 1);
    var farTxt = far >= 1 ? (far >= 1000 ? Math.round(far).toLocaleString("tr-TR") : far.toFixed(1)) + " /s" : (1 / far >= 86400 ? (1 / far / 86400).toFixed(1) + " günde 1" : (1 / far).toFixed(0) + " s'de 1");
    WK.sonucYaz(w, {
      "eşik T": Tsig.toFixed(3) + " σ  (güçte −ln Pfa = " + (Tsig * Tsig / 2).toFixed(1) + " × P_ort, " + (10 * Math.log10(Tsig * Tsig / 2)).toFixed(1) + " dB)",
      "Pfa (teori)": pfa.toExponential(2),
      "Pd (teori, Marcum Q)": (pd < 0.5 ? "!" : (pd >= 0.9 ? "+" : "")) + pd.toFixed(4),
      "yanlış alarm / s": (far > 10 ? "!" : "+") + farTxt + " @ " + (p.fs / 1e6).toFixed(0) + " MSPS",
      "Pd = 0.9 için SNR (Albersheim)": snr09.toFixed(1) + " dB",
      "Monte Carlo Pfa": mcTxt.pfa,
      "Monte Carlo Pd": mcTxt.pd
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { snr: snrRef, pfadan: true, pfaHedef: "1e-6", esik: 5.26, fs: fsRef, mc: true } },
      { ad: "Pd = 0.5 (11.2 dB)", param: { snr: T.snr_pd05_db || 11.2, pfadan: true, pfaHedef: "1e-6", esik: 5.26, fs: fsRef, mc: true } },
      { ad: "Gevşek eşik (4σ)", param: { snr: snrRef, pfadan: false, pfaHedef: "1e-6", esik: 4, fs: fsRef, mc: true } },
      { ad: "Saniyede 1 yanlış alarm", param: { snr: snrRef, pfadan: true, pfaHedef: "3.3333e-9", esik: 6.25, fs: fsRef, mc: false } },
      { ad: "Pfa 10⁻³ — Monte Carlo", param: { snr: snrRef, pfadan: true, pfaHedef: "1e-3", esik: 3.72, fs: fsRef, mc: true } }
    ]
  };
});
