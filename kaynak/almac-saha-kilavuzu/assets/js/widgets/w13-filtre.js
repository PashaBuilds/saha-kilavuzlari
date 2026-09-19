/* W-13 — Filtre ve decimation laboratuvarı
   Kontroller: tip (FIR / halfband / CIC + kompanzasyon), fs, tap sayısı, kesim, katsayı biti, decimation M, CIC kademe N
   Çıktı: frekans yanıtı (katlanacak alias bölgeleri taralı), darbe yanıtı (rise time, σ_TOA); grup gecikmesi, çarpıcı,
          bit büyümesi, alias bastırma, passband ripple
   Hesap: DSP.firTasarla, DSP.halfband, DSP.katsayiKuantize, DSP.firYanit, DSP.cicYanit, DSP.cicBitBuyumesi, DSP.firUygula,
          DSP.decimate, DSP.darbeZarfi, DSP.toaHatasi
   Yerel yardımcı (çekirdeğe aday): lsFirTasarla — en küçük kareler, simetrik FIR (CIC kompanzasyonu için ters-sinc). */
WK.kaydet("w13", function (w) {
  var S = w.S, fsRef = (S.ddc && S.ddc.kademeler ? S.ddc.kademeler[0].fs_cikis_msps : 600) * 1e6;
  var pwRef = S.sinyal ? S.sinyal.pw_s : 1e-6, riseRef = S.sinyal ? S.sinyal.rise_time_ns * 1e-9 : 50e-9;
  var snrRef = S.tespit ? S.tespit.tespit_snr_db : 15;
  var kompTap = S.ddc ? S.ddc.kompanzasyon_fir_tap : 31;

  /* ---- yerel yardımcı: LS ile simetrik FIR (istenen genlik D(f) ağırlıklı) ---- */
  function lsFirTasarla(tap, fs, hedef) {
    // hedef: [{f0, f1, D(f) fonksiyonu, agirlik}] ; H(f) = a0 + 2 Σ a_k cos(2π f k / fs)
    var m = (tap - 1) >> 1, n = m + 1, A = [], b = [], i, j, r;
    for (i = 0; i < n; i++) { A.push(new Float64Array(n)); b.push(0); }
    for (r = 0; r < hedef.length; r++) {
      var h = hedef[r], adet = 120;
      for (i = 0; i <= adet; i++) {
        var f = h.f0 + (h.f1 - h.f0) * i / adet, d = h.D(f), wgt = h.agirlik;
        var row = [1]; for (j = 1; j < n; j++) row.push(2 * Math.cos(2 * Math.PI * f * j / fs));
        for (var p = 0; p < n; p++) { b[p] += wgt * row[p] * d; for (j = 0; j < n; j++) A[p][j] += wgt * row[p] * row[j]; }
      }
    }
    for (i = 0; i < n; i++) {                       // Gauss eliminasyonu (pivotlu)
      var piv = i; for (r = i + 1; r < n; r++) if (Math.abs(A[r][i]) > Math.abs(A[piv][i])) piv = r;
      var t = A[i]; A[i] = A[piv]; A[piv] = t; var tb = b[i]; b[i] = b[piv]; b[piv] = tb;
      for (r = i + 1; r < n; r++) { var fct = A[r][i] / A[i][i]; if (!fct) continue; for (j = i; j < n; j++) A[r][j] -= fct * A[i][j]; b[r] -= fct * b[i]; }
    }
    var a = new Float64Array(n);
    for (i = n - 1; i >= 0; i--) { var s = b[i]; for (j = i + 1; j < n; j++) s -= A[i][j] * a[j]; a[i] = s / A[i][i]; }
    var out = new Float64Array(tap); out[m] = a[0];
    for (j = 1; j < n; j++) { out[m + j] = a[j]; out[m - j] = a[j]; }
    return out;
  }
  function cicLin(R, Nk, f, fs) { var x = f / fs; if (x === 0) return 1; var g = Math.abs(Math.sin(Math.PI * R * x) / Math.sin(Math.PI * x)) / R; return Math.pow(g, Nk); }

  WK.secim(w, { ad: "tip", etiket: "filtre tipi", secenekler: [["fir", "FIR (pencereli sinc, Kaiser)"], ["hb", "halfband (fc = fs/4)"], ["cic", "CIC + kompanzasyon FIR"]], deger: "hb", metin: true });
  WK.kaydirici(w, { ad: "fs", etiket: "giriş fs", min: 100e6, max: 2400e6, adim: 50e6, deger: fsRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "tap", etiket: "tap sayısı (tek)", min: 7, max: 255, adim: 2, deger: 23, birim: "tap", tamsayi: true });
  WK.kaydirici(w, { ad: "fc", etiket: "kesim (FIR: −6 dB; CIC: geçirme kenarı)", min: 1e6, max: 600e6, adim: 1e6, deger: 150e6, olcek: 1e6, birim: "MHz" });
  var kapat = WK.grup(w, "Sabit nokta ve decimation");
  WK.kaydirici(w, { ad: "bit", etiket: "katsayı biti", min: 4, max: 24, adim: 1, deger: 16, birim: "bit", tamsayi: true });
  WK.secim(w, { ad: "M", etiket: "decimation M (CIC: R)", secenekler: [[1, "yok"], [2, "↓2"], [4, "↓4"], [8, "↓8"]], deger: 2 });
  WK.kaydirici(w, { ad: "Nk", etiket: "CIC kademe N", min: 1, max: 5, adim: 1, deger: 4, birim: "", tamsayi: true });
  WK.onay(w, { ad: "komp", etiket: "CIC kompanzasyon FIR'ı (" + kompTap + " tap)", deger: true });
  kapat();

  var pYanit = WK.panel(w, 260), pDarbe = WK.panel(w, 200);
  var NF = 600;

  function ciz() {
    var p = w.param, fs = p.fs, M = +p.M, tap = Math.max(7, (Math.round(p.tap) | 1)), bit = Math.round(p.bit), Nk = Math.round(p.Nk);
    var k, h = null, hq = null, hk = null, yanit = new Float64Array(NF), fsFilt = fs, fsOut = fs / M;
    var carpici = 0, bitBuyume = 0, grupOrnek = 0, katsayiToplam = 1, fcEtkin = p.fc, ad = "";
    if (p.tip === "fir") {
      h = DSP.firTasarla(p.fc, fs, tap, "kaiser", 8); hq = DSP.katsayiKuantize(h, bit);
      yanit = DSP.firYanit(hq, NF); carpici = Math.ceil(tap / 2); grupOrnek = (tap - 1) / 2; ad = tap + " tap Kaiser FIR";
    } else if (p.tip === "hb") {
      h = DSP.halfband(tap, "kaiser"); hq = DSP.katsayiKuantize(h, bit);
      yanit = DSP.firYanit(hq, NF); var nz = 0; for (k = 0; k < tap; k++) if (hq[k] !== 0) nz++;
      carpici = Math.ceil(nz / 2); grupOrnek = (tap - 1) / 2; fcEtkin = fs / 4; ad = tap + " tap halfband (" + nz + " sıfır olmayan)";
    } else {
      var R = Math.max(2, M);
      var cic = DSP.cicYanit(R, Nk, NF);
      if (p.komp) {
        var fk = fs / R;   // kompanzasyon FIR çıkış hızında
        var fp = Math.min(p.fc, fk * 0.3), fst = Math.max(fp * 1.4, fk * 0.35);
        hk = lsFirTasarla(kompTap, fk, [
          { f0: 0, f1: fp, D: function (f) { return 1 / cicLin(R, Nk, f, fs); }, agirlik: 10 },
          { f0: fst, f1: fk / 2, D: function () { return 0; }, agirlik: 1 }]);
        hk = DSP.katsayiKuantize(hk, bit);
        katsayiToplam = 0; for (k = 0; k < hk.length; k++) katsayiToplam += hk[k];
      }
      for (k = 0; k < NF; k++) {
        var f = k / (2 * NF) * fs, v = cic[k];
        if (hk) { var fw = ((f % (fs / R)) + fs / R) % (fs / R); if (fw > fs / (2 * R)) fw = fs / R - fw; v += komp1(hk, fw, fs / R); }
        yanit[k] = v;
      }
      carpici = hk ? Math.ceil(kompTap / 2) : 0; bitBuyume = DSP.cicBitBuyumesi(R, Nk); grupOrnek = Nk * (R - 1) / 2 + (hk ? (kompTap - 1) / 2 * R : 0);
      ad = "CIC R = " + R + ", N = " + Nk + (hk ? " + " + kompTap + " tap komp." : "");
      // eşdeğer FIR (darbe yanıtı için): (ones(R))^N / R^N, sonra komp
      var e = new Float64Array([1]);
      for (var s = 0; s < Nk; s++) { var o = new Float64Array(e.length + R - 1); for (var i = 0; i < e.length; i++) for (var j = 0; j < R; j++) o[i + j] += e[i]; e = o; }
      var gn = Math.pow(R, Nk); for (k = 0; k < e.length; k++) e[k] /= gn; hq = e;
    }
    if (h) { var sa = 0; katsayiToplam = 0; for (k = 0; k < hq.length; k++) { sa += Math.abs(hq[k]); katsayiToplam += hq[k]; } bitBuyume = Math.ceil(Math.log2(Math.max(1, sa))); }
    // metrikler: alias bastırma = katlanacak bölgelerde en büyük yanıt; passband ripple 0..0.8 fc
    var fArr = [], aliasMax = -300, rip = 0, edgeDb = 0, stopMax = -300;
    var koru = 0.8 * Math.min(fcEtkin, fsOut / 2);                       // korunan (temiz) bant: 0.8·fc
    var Akaiser = (p.tip === "hb" ? 6 : 8) / 0.1102 + 8.7;                // Kaiser β ↔ A (dB)
    var dfGecis = (Akaiser - 8) / (2.285 * Math.max(1, (p.tip === "cic" ? kompTap : tap) - 1)) * (p.tip === "cic" ? fs / Math.max(2, M) : fs) / (2 * Math.PI);
    var fStop = p.tip === "cic" ? fsOut - fcEtkin : fcEtkin + dfGecis / 2;   // stopband başlangıcı
    for (k = 0; k < NF; k++) {
      var fh = k / (2 * NF) * fs; fArr.push(fh);
      if (M > 1) { var fw2 = fh % fsOut; if (fw2 > fsOut / 2) fw2 = fsOut - fw2; if (fh > fsOut / 2 && fw2 <= koru) aliasMax = Math.max(aliasMax, yanit[k]); }
      if (fh <= koru) rip = Math.max(rip, Math.abs(yanit[k]));
      if (fh >= fStop) stopMax = Math.max(stopMax, yanit[k]);
    }
    var kEdge = Math.min(NF - 1, Math.round(fcEtkin / fs * 2 * NF)); edgeDb = yanit[kEdge];
    // ---- yanıt çizimi
    WK.temizle(pYanit);
    var g = WK.grafik(pYanit, { W: 640, H: 260, xmin: 0, xmax: fs / 2e6, ymin: -120, ymax: 5, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    g.eksenler({ xAdet: 6, yAdet: 6, xAd: "frekans (MHz)", yAd: "dB", baslik: "Frekans yanıtı — " + ad + " @ " + (fs / 1e6) + " MSPS", xFmt: function (v) { return v.toFixed(0); } });
    if (M > 1) {
      for (var q = 1; q * fsOut - koru < fs / 2; q++) g.bant((q * fsOut - koru) / 1e6, (q * fsOut + koru) / 1e6, "w-dolgu-kirmizi");
      g.dikey(fsOut / 2e6, "w-cizgi-gri", "yeni Nyquist " + (fsOut / 2e6).toFixed(0));
      g.bant(0, koru / 1e6, "w-dolgu-sinyal");
      g.metin(g.px(koru / 2e6), g.y0 - 6, "korunan ±" + (koru / 1e6).toFixed(0), "w-not", "middle");
    }
    var ys = []; for (k = 0; k < NF; k++) ys.push(yanit[k]);
    var fx = fArr.map(function (v) { return v / 1e6; });
    g.cizgi(fx, ys, "w-cizgi-sinyal");
    if (p.tip === "cic") { var yc = []; var cic0 = DSP.cicYanit(Math.max(2, M), Nk, NF); for (k = 0; k < NF; k++) yc.push(cic0[k]); g.cizgi(fx, yc, "w-cizgi-gri"); }
    g.nokta(fcEtkin / 1e6, edgeDb, 4, "w-nokta"); g.metin(g.px(fcEtkin / 1e6) - 6, g.py(edgeDb) + 14, (fcEtkin / 1e6).toFixed(0) + " MHz: " + edgeDb.toFixed(1) + " dB", "w-not", "end");   // noktanın sol altı: Nyquist etiketiyle çakışmaz
    if (M > 1 && aliasMax > -300) g.yatay(aliasMax, "w-cizgi-kirmizi", "alias bastırma " + aliasMax.toFixed(0) + " dB");
    // ---- darbe yanıtı
    var nS = Math.min(8192, Math.max(512, Math.round(fs * 2.6e-6)));
    var zarf = DSP.darbeZarfi(nS, fs, pwRef, 0, riseRef, 0.4e-6);
    var yz = DSP.firUygula(zarf, hq);
    var gd = Math.round((hq.length - 1) / 2);
    var t10 = -1, t90 = -1, pk = 0; for (k = 0; k < nS; k++) pk = Math.max(pk, yz[k]);
    for (k = 0; k < nS; k++) { if (t10 < 0 && yz[k] >= 0.1 * pk) t10 = k; if (t90 < 0 && yz[k] >= 0.9 * pk) { t90 = k; break; } }
    var tr = Math.max(1, t90 - t10) / fs, trGiris = riseRef * 0.59;  // kosinüs kenar %10–90 = 0.59·rise
    var toa = DSP.toaHatasi(tr, snrRef);
    WK.temizle(pDarbe);
    var gp = WK.grafik(pDarbe, { W: 640, H: 200, xmin: 0, xmax: nS / fs * 1e6, ymin: -0.1, ymax: 1.25, kenar: { sol: 48, sag: 14, ust: 22, alt: 30 } });
    gp.eksenler({ xAdet: 6, yAdet: 4, xAd: "zaman (µs)", yAd: "zarf", baslik: "Darbe yanıtı: " + (pwRef * 1e6) + " µs darbe (giriş kesikli, çıkış mavi)", xFmt: function (v) { return v.toFixed(1); }, yFmt: function (v) { return v.toFixed(1); } });
    var tx = [], tz = [], ty = [], adim = Math.max(1, Math.floor(nS / 1500));
    for (k = 0; k < nS; k += adim) { tx.push(k / fs * 1e6); tz.push(zarf[k]); ty.push(yz[k]); }
    gp.cizgi(tx, tz, "w-cizgi-gri"); gp.cizgi(tx, ty, "w-cizgi-sinyal");
    gp.dikey(t10 / fs * 1e6, "w-cizgi-altin"); gp.dikey(t90 / fs * 1e6, "w-cizgi-altin");
    gp.metin(gp.px(t90 / fs * 1e6) + 5, gp.y1 + 12, "%10–%90: " + (tr * 1e9).toFixed(0) + " ns", "w-not");
    gp.metin(gp.x1 - 4, gp.y1 + 12, "grup gecikmesi " + (gd / fs * 1e9).toFixed(1) + " ns", "w-not", "end");
    var bwT = p.tip === "cic" ? p.fc : (p.tip === "hb" ? fs / 4 : p.fc);
    WK.sonucYaz(w, {
      "grup gecikmesi": grupOrnek.toFixed(1) + " giriş örneği = " + (grupOrnek / fs * 1e9).toFixed(1) + " ns",
      "çarpıcı (simetri ile)": carpici + (p.tip === "cic" ? " (CIC'in kendisi 0)" : ""),
      "bit büyümesi": "+" + bitBuyume + " bit" + (p.tip === "cic" ? " (N·log₂R, wrap zorunlu)" : " (⌈log₂ ∑|h|⌉)"),
      "katsayı toplamı (DC kazancı)": katsayiToplam.toFixed(4),
      "geçirme bandı ripple (0–0.8·fc)": (rip > 1 ? "!" : "+") + "±" + rip.toFixed(2) + " dB",
      "stopband": (stopMax > -60 ? "!" : "+") + stopMax.toFixed(1) + " dB (f > " + (fStop / 1e6).toFixed(0) + " MHz)",
      "alias bastırma (korunan banda katlanan)": M > 1 ? ((aliasMax > -40 ? "!" : "+") + aliasMax.toFixed(1) + " dB (korunan ±" + (koru / 1e6).toFixed(0) + " MHz)") : "decimation yok",
      "yeni fs / Nyquist": (fsOut / 1e6).toFixed(0) + " MSPS / ±" + (fsOut / 2e6).toFixed(0) + " MHz",
      "rise time (%10–90)": (tr * 1e9).toFixed(1) + " ns (giriş " + (trGiris * 1e9).toFixed(0) + " ns; 0.35/B ≈ " + (0.35 / bwT * 1e9).toFixed(1) + " ns)",
      "σ_TOA = t_r/√(2·SNR)": (toa * 1e9).toFixed(1) + " ns (SNR " + snrRef + " dB)"
    });
  }
  // kompanzasyon FIR'ının tek frekanstaki yanıtı (dB) — çıkış hızında
  function komp1(hk, f, fsk) { var re = 0, im = 0, wf = 2 * Math.PI * f / fsk; for (var k = 0; k < hk.length; k++) { re += hk[k] * Math.cos(wf * k); im -= hk[k] * Math.sin(wf * k); } return DSP.db20(Math.sqrt(re * re + im * im)); }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { tip: "hb", fs: fsRef, tap: 23, fc: 150e6, bit: 16, M: 2, Nk: 4, komp: true } },
      { ad: "CIC + kompanzasyon", param: { tip: "cic", fs: 2400e6, tap: 23, fc: 150e6, bit: 18, M: 4, Nk: 4, komp: true } },
      { ad: "CIC droop (komp. kapalı)", param: { tip: "cic", fs: 2400e6, tap: 23, fc: 150e6, bit: 18, M: 4, Nk: 4, komp: false } },
      { ad: "63 tap FIR, 16 bit", param: { tip: "fir", fs: fsRef, tap: 63, fc: 150e6, bit: 16, M: 2, Nk: 4, komp: true } },
      { ad: "63 tap FIR, 12 bit", param: { tip: "fir", fs: fsRef, tap: 63, fc: 150e6, bit: 12, M: 2, Nk: 4, komp: true } },
      { ad: "Dar bant: 1 MHz", param: { tip: "fir", fs: 300e6, tap: 255, fc: 1e6, bit: 16, M: 1, Nk: 4, komp: true } }
    ]
  };
});
