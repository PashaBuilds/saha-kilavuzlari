/* W-03 — Darbe katarı ↔ spektrum
   Kontroller: PW, PRI, yükselme süresi, MOP (yok / LFM / Barker-13 / Barker-7), chirp BW
   Çıktı: tek darbe (zarf + taşıyıcı), darbe katarı, spektrum (tek darbenin zarfı + PRF aralıklı çizgiler)
   Hesap: DSP.darbeKompleks + DSP.spektrumDbfs (zarf); çizgiler zarftan k·PRF noktalarında okunur. */
WK.kaydet("w03", function (w) {
  var S = w.S;
  var pwRef = S.sinyal ? S.sinyal.pw_s : 1e-6, priRef = S.sinyal ? S.sinyal.pri_s : 1e-3;
  var riseRef = S.sinyal && S.sinyal.rise_time_ns ? S.sinyal.rise_time_ns * 1e-9 : 50e-9;
  var bwRef = S.sinyal && S.sinyal.varyant_b ? S.sinyal.varyant_b.chirp_bw_hz : 10e6;

  WK.kaydirici(w, { ad: "pw", etiket: "darbe genişliği PW", min: 0.1e-6, max: 20e-6, deger: pwRef, log: true, olcek: 1e-6, birim: "µs", hane: 2 });
  WK.kaydirici(w, { ad: "pri", etiket: "darbe tekrar aralığı PRI", min: 2e-6, max: 5e-3, deger: priRef, log: true, olcek: 1e-6, birim: "µs", hane: 1 });
  WK.kaydirici(w, { ad: "rise", etiket: "yükselme süresi (10–90)", min: 0, max: 300e-9, adim: 5e-9, deger: riseRef, olcek: 1e-9, birim: "ns", hane: 0 });
  var kapat = WK.grup(w, "Darbe içi modülasyon (MOP)");
  WK.secim(w, { ad: "mop", etiket: "MOP", secenekler: [["yok", "yok (sabit frekans)"], ["lfm", "LFM chirp"], ["barker13", "Barker-13 faz kodu"], ["barker7", "Barker-7 faz kodu"]], deger: "yok", metin: true });
  WK.kaydirici(w, { ad: "bw", etiket: "chirp bant genişliği B", min: 1e6, max: 50e6, adim: 1e6, deger: bwRef, olcek: 1e6, birim: "MHz", hane: 0 });
  kapat();

  var tek = WK.panel(w, 200), katar = WK.panel(w, 130), spek = WK.panel(w, 260);
  var N = 4096;

  function ciz() {
    var p = w.param;
    var pw = Math.max(p.pw, 0.05e-6), pri = Math.max(p.pri, pw * 1.2), rise = Math.min(p.rise, pw / 2.5);
    var prf = 1 / pri, duty = pw / pri;
    var cipler = p.mop === "barker13" ? 13 : p.mop === "barker7" ? 7 : 1;
    // görüntü aralığı (MHz) ve benzetim fs'i
    var temelBw = 1 / pw;                                    // ilk sıfır
    var xmaxHz = Math.max(6 * temelBw, p.mop === "lfm" ? p.bw / 2 + 3 * temelBw : 0, cipler > 1 ? 1.5 * cipler * temelBw : 0);
    var fsSim = 2.4 * xmaxHz;
    var kesitZaman = N / fsSim;                               // zaman penceresi
    var d = DSP.darbeKompleks({ n: N, fs: fsSim, pw: pw, pri: 0, f0: 0, mop: p.mop, chirpBw: p.bw, rise: rise, gecikme: kesitZaman * 0.1 });
    var sp = DSP.spektrumDbfs(d.i, d.q, "rect");
    var tepe = DSP.maks(sp), k;
    for (k = 0; k < N; k++) sp[k] -= tepe;
    // --- tek darbe
    WK.temizle(tek);
    var t0 = kesitZaman * 0.1;
    var gt = WK.grafik(tek, { W: 640, H: 200, xmin: -0.2 * pw * 1e6, xmax: 1.2 * pw * 1e6, ymin: -1.3, ymax: 1.3, kenar: { sol: 44, sag: 14, ust: 22, alt: 30 } });
    gt.eksenler({ xAdet: 7, yAdet: 4, xAd: "zaman (µs)", yAd: "genlik", baslik: "Tek darbe — zarf (altın), gerçek kısım temsilî taşıyıcı ile (mavi)", yFmt: function (v) { return v.toFixed(1); } });
    var xs = [], zarf = [], reel = [], nn = 700, fGor = 6 / pw;
    for (k = 0; k < nn; k++) {
      var t = -0.2 * pw + 1.4 * pw * k / (nn - 1);
      var idx = Math.round((t + t0) * fsSim);
      var z = idx >= 0 && idx < N ? d.zarf[idx] : 0;
      var faz = idx >= 0 && idx < N && z > 0 ? Math.atan2(d.q[idx], d.i[idx]) : 0;
      xs.push(t * 1e6); zarf.push(z); reel.push(z * Math.cos(2 * Math.PI * fGor * t + faz));
    }
    gt.cizgi(xs, reel, "w-cizgi-sinyal");
    gt.cizgi(xs, zarf, "w-cizgi-altin");
    gt.yatay(0.5, "w-cizgi-gri", "%50 → PW");
    if (cipler > 1) for (k = 1; k < cipler; k++) gt.dikey(k * pw / cipler * 1e6, "w-cizgi-kirmizi");
    // --- katar
    WK.temizle(katar);
    var gk = WK.grafik(katar, { W: 640, H: 130, xmin: -0.15 * pri * 1e6, xmax: 3.15 * pri * 1e6, ymin: 0, ymax: 1.2, kenar: { sol: 44, sag: 14, ust: 22, alt: 30 } });
    gk.eksenler({ xAdet: 6, yAdet: 2, xAd: "zaman (µs)", baslik: "Darbe katarı — PRI = " + WK.fmtS(pri) + ", PRF = " + WK.fmtHz(prf) + ", duty = %" + (duty * 100).toFixed(duty < 0.01 ? 2 : 1), yFmt: function (v) { return v.toFixed(1); } });
    for (k = 0; k < 4; k++) {
      var xa = gk.px(k * pri * 1e6), xb = gk.px((k * pri + pw) * 1e6);
      gk.ekle("rect", { x: xa, y: gk.py(1), width: Math.max(2, xb - xa), height: gk.py(0) - gk.py(1), "class": "w-dolgu-altin" });
      gk.ekle("line", { x1: xa, y1: gk.py(1), x2: Math.max(xa + 2, xb), y2: gk.py(1), "class": "w-cizgi-altin" });
    }
    gk.yatay(duty, "w-cizgi-kirmizi", "ortalama = tepe × duty (" + DSP.db10(duty).toFixed(1) + " dB)");
    // --- spektrum
    WK.temizle(spek);
    var gs = WK.grafik(spek, { W: 640, H: 260, xmin: -xmaxHz / 1e6, xmax: xmaxHz / 1e6, ymin: -60, ymax: 5, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gs.eksenler({ xAdet: 8, yAdet: 6, xAd: "frekans − f₀ (MHz)", yAd: "dB (tepeye göre)", baslik: "Spektrum — tek darbenin zarfı (mavi) ve PRF aralıklı çizgiler" });
    var fx = [], fy = [];
    for (k = 0; k < N; k++) { fx.push((k - N / 2) * fsSim / N / 1e6); fy.push(sp[k]); }
    gs.alan(fx, fy, -60, "w-dolgu-sinyal");
    gs.cizgi(fx, fy, "w-cizgi-sinyal");
    // PRF çizgileri
    var cizgiSayi = Math.floor(xmaxHz / prf) * 2 + 1, cizildi = 0;
    if (cizgiSayi <= 400) {
      for (var m = -Math.floor(xmaxHz / prf); m <= Math.floor(xmaxHz / prf); m++) {
        var f = m * prf, bin = Math.round(f / fsSim * N) + N / 2;
        if (bin < 0 || bin >= N) continue;
        var seviye = sp[bin];  // çizgilerin tepesi zarfı izler; mutlak genlik = duty × zarf (sonuç satırında)
        gs.ekle("line", { x1: gs.px(f / 1e6), y1: gs.py(Math.max(-60, seviye)), x2: gs.px(f / 1e6), y2: gs.y0, "class": "w-cizgi-sinyal", opacity: ".9" });
        cizildi++;
      }
    } else {
      gs.metin(gs.x0 + 8, gs.y1 + 30, "PRF çizgileri " + cizgiSayi + " adet — bu ölçekte çizilmez (aralık " + WK.fmtHz(prf) + ", zarfın altını sürekli doldurur)", "w-not");
    }
    if (p.mop === "yok") {
      gs.dikey(1 / pw / 1e6, "w-cizgi-gri", "1/PW = " + WK.fmtHz(1 / pw));
      gs.dikey(-1 / pw / 1e6, "w-cizgi-gri");
      gs.yatay(-13.3, "w-cizgi-kirmizi", "ilk yan lob −13.3 dB");
    } else if (p.mop === "lfm") {
      gs.bant(-p.bw / 2e6, p.bw / 2e6, "w-dolgu-altin");
      gs.metin(gs.px(-p.bw / 2e6) + 4, gs.y1 + 30, "B = " + WK.fmtHz(p.bw), "w-not");
    } else {
      gs.dikey(cipler / pw / 1e6, "w-cizgi-gri", "1/chip = " + WK.fmtHz(cipler / pw));
      gs.dikey(-cipler / pw / 1e6, "w-cizgi-gri");
    }
    // sonuçlar
    var sonuc = {
      "PRF = 1/PRI": WK.fmtHz(prf),
      "duty = PW/PRI": "%" + (duty * 100).toPrecision(3) + " → ortalama güç tepeden " + (-DSP.db10(duty)).toFixed(1) + " dB aşağıda",
      "ilk sıfır 1/PW": WK.fmtHz(1 / pw) + " (ana lob 2/PW = " + WK.fmtHz(2 / pw) + ")",
      "−3 dB genişlik (dikdörtgen)": WK.fmtHz(0.886 / pw),
      "çizgi aralığı": WK.fmtHz(prf) + " · ana lobda ≈ " + Math.round(2 * pri / pw) + " çizgi" + (cizgiSayi <= 400 ? " (" + cizildi + " çizildi)" : ""),
      "kenar bant genişliği ≈ 0.35/t_r": rise > 0 ? WK.fmtHz(0.35 / rise) : "∞ (ideal kenar)"
    };
    if (p.mop === "lfm") { sonuc["LFM: B·T çarpımı"] = (p.bw * pw).toFixed(1) + " (sıkıştırma kazancı ≈ " + DSP.db10(p.bw * pw).toFixed(1) + " dB)"; sonuc["etkin bant genişliği"] = "+≈ B = " + WK.fmtHz(p.bw) + " (1/PW'nin " + (p.bw * pw).toFixed(0) + " katı)"; }
    if (cipler > 1) { sonuc["Barker: chip süresi"] = WK.fmtS(pw / cipler); sonuc["etkin bant genişliği"] = "+≈ " + cipler + "/PW = " + WK.fmtHz(cipler / pw); }
    if (duty > 0.5) sonuc["uyarı"] = "!duty > %50 — CW'ye yaklaşıyor";
    WK.sonucYaz(w, sonuc);
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { pw: pwRef, pri: priRef, rise: riseRef, mop: "yok", bw: bwRef } },
      { ad: "Varyant B: LFM 10 MHz", param: { pw: pwRef, pri: priRef, rise: riseRef, mop: "lfm", bw: bwRef } },
      { ad: "Kısa darbe 0.2 µs", param: { pw: 0.2e-6, pri: 20e-6, rise: 10e-9, mop: "yok", bw: bwRef } },
      { ad: "Barker-13", param: { pw: pwRef, pri: priRef, rise: 0, mop: "barker13", bw: bwRef } },
      { ad: "Yüksek PRF (PRI = 10 µs)", param: { pw: pwRef, pri: 10e-6, rise: riseRef, mop: "yok", bw: bwRef } }
    ]
  };
});
