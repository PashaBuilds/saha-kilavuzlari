/* W-12 — DDC laboratuvarı
   Kontroller: giriş tipi (ton/darbe), giriş frekansı (ADC çıkışında, katlanmış), seviye, gürültü,
               NCO frekansı ve işareti, filtre bandı (tek taraflı), decimation M
   Çıktı: zincirin 4 noktasında spektrum (ADC → mixing → filtre → decimation), gürültü/sinyal gücü, SNR kazancı,
          katlanan (alias) güç, çıkış tonunun frekansı
   Hesap: DSP.ddc (mixer + Kaiser FIR + decimate), DSP.spektrumDbfs, DSP.ton, DSP.darbeReel, DSP.gurultuEkleReel */
WK.kaydet("w12", function (w) {
  var S = w.S, fs = S.adc ? S.adc.fs_hz : 2400e6, fNcoRef = S.ddc ? S.ddc.nco_hz : 600e6, fInRef = S.adc ? S.adc.alias_hz : 600e6;
  var pwRef = S.sinyal ? S.sinyal.pw_s : 1e-6, riseRef = S.sinyal ? S.sinyal.rise_time_ns * 1e-9 : 50e-9;
  WK.secim(w, { ad: "tip", etiket: "giriş", secenekler: [["ton", "CW ton"], ["darbe", "1 µs darbe"]], deger: "ton", metin: true });
  WK.kaydirici(w, { ad: "fin", etiket: "giriş frekansı (ADC çıkışı, katlanmış)", min: 1e6, max: 1199e6, adim: 1e6, deger: fInRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "seviye", etiket: "giriş seviyesi", min: -60, max: -1, adim: 1, deger: -6, birim: "dBFS" });
  WK.kaydirici(w, { ad: "gur", etiket: "gürültü (toplam)", min: -90, max: -20, adim: 1, deger: -60, birim: "dBFS" });
  var kapat = WK.grup(w, "NCO ve filtre");
  WK.kaydirici(w, { ad: "fnco", etiket: "NCO frekansı", min: 0, max: 1200e6, adim: 1e6, deger: fNcoRef, olcek: 1e6, birim: "MHz" });
  WK.secim(w, { ad: "isaret", etiket: "NCO yönü", secenekler: [["-1", "− (e^{−jωn}, aşağı)"], ["1", "+ (e^{+jωn}, evriği düzeltir)"]], deger: "-1", metin: true });
  WK.kaydirici(w, { ad: "bw", etiket: "filtre bandı (tek taraflı, ±)", min: 1e6, max: 1000e6, adim: 1e6, deger: 150e6, olcek: 1e6, birim: "MHz" });
  WK.secim(w, { ad: "M", etiket: "decimation M", secenekler: [[2, "↓2"], [4, "↓4"], [8, "↓8"], [16, "↓16"]], deger: 8 });
  kapat();

  var pan = [WK.panel(w, 170), WK.panel(w, 170), WK.panel(w, 170), WK.panel(w, 170)];
  var N = 4096, TAP = 127;

  function gucDb(a, b, x, y) { var s = 0, n = 0; for (var k = a; k < b && k < x.length; k++) { s += x[k] * x[k] + (y ? y[k] * y[k] : 0); n++; } return n ? DSP.db10(s / n) : -300; }

  function spekCiz(svg, sp, fsHz, baslik, ek) {
    WK.temizle(svg);
    var g = WK.grafik(svg, { W: 640, H: 170, xmin: -fsHz / 2e6, xmax: fsHz / 2e6, ymin: -140, ymax: 5, kenar: { sol: 48, sag: 14, ust: 22, alt: 30 } });
    g.eksenler({ xAdet: 6, yAdet: 4, xAd: "frekans (MHz)", yAd: "dBFS", baslik: baslik, xFmt: function (v) { return v.toFixed(0); } });
    var n = sp.length, fx = [], fy = [];
    for (var k = 0; k < n; k++) { fx.push((k - n / 2) * fsHz / n / 1e6); fy.push(sp[k]); }
    g.alan(fx, fy, -140, "w-dolgu-gurultu"); g.cizgi(fx, fy, "w-cizgi-sinyal");
    if (ek) ek(g);
    return g;
  }

  // dikey çizgi + etiket; etiket panelin sağ yarısındaysa sola yazılır (kenardan taşmasın)
  function dikeyEtiket(g, x, kls, etiket) {
    g.dikey(x, kls);
    var sag = x > (g.xmin + g.xmax) / 2;
    g.metin(g.px(x) + (sag ? -3 : 3), g.y1 + 11, etiket, "w-not", sag ? "end" : "start");
  }

  function ciz() {
    var p = w.param, M = +p.M, isaret = +p.isaret, A = Math.pow(10, p.seviye / 20), sigma = Math.pow(10, p.gur / 20);
    // giriş: sinyal ve gürültü ayrı üretilir (güç ayrıştırması için), zincir ikisine ayrı uygulanır (doğrusal)
    var xs;
    if (p.tip === "ton") xs = DSP.ton(N, fs, p.fin, A, 0.3);
    else xs = DSP.darbeReel({ n: N, fs: fs, pw: pwRef, pri: 0, f0: p.fin, genlik: A, rise: riseRef, gecikme: 0.3e-6 });
    var xn = DSP.gurultuEkleReel(new Float64Array(N), sigma, DSP.prng(31));
    var x = new Float64Array(N); for (var k = 0; k < N; k++) x[k] = xs[k] + xn[k];
    var ds = DSP.ddc(xs, fs, p.fnco, p.bw, M, TAP, isaret);
    var dn = DSP.ddc(xn, fs, p.fnco, p.bw, M, TAP, isaret);
    var dx = DSP.ddc(x, fs, p.fnco, p.bw, M, TAP, isaret);
    var fsOut = fs / M;
    // spektrumlar (toplam sinyal)
    var sp1 = DSP.spektrumDbfs(x, null, "blackman-harris");
    var sp2 = DSP.spektrumDbfs(dx.mix.i, dx.mix.q, "blackman-harris");
    var sp3 = DSP.spektrumDbfs(dx.fil.i, dx.fil.q, "blackman-harris");
    var nD = dx.dec.i.length, nD2 = 1; while (nD2 * 2 <= nD) nD2 *= 2;
    var sp4 = DSP.spektrumDbfs(dx.dec.i.subarray(nD - nD2), dx.dec.q.subarray(nD - nD2), "blackman-harris");
    // güçler (ısınma sonrası: ilk TAP örnek atlanır)
    var a0 = TAP, sinAdc = gucDb(a0, N, xs), gurAdc = gucDb(a0, N, xn);
    var sinMix = gucDb(a0, N, ds.mix.i, ds.mix.q), gurMix = gucDb(a0, N, dn.mix.i, dn.mix.q);
    var sinFil = gucDb(a0, N, ds.fil.i, ds.fil.q), gurFil = gucDb(a0, N, dn.fil.i, dn.fil.q);
    var snrKazanc = (sinFil - gurFil) - (sinAdc - gurAdc);
    // katlanan güç: filtre sonrası, ±fsOut/2 dışındaki güç / içindeki güç (spektrumdan)
    var icG = 0, disG = 0;
    for (k = 0; k < N; k++) { var f = (k - N / 2) * fs / N; var pw = DSP.lin10(sp3[k]); if (Math.abs(f) <= fsOut / 2) icG += pw; else disG += pw; }
    var katlanan = DSP.db10(disG / Math.max(icG, 1e-300));
    // çıkış tonu
    var pk = 0; for (k = 1; k < nD2; k++) if (sp4[k] > sp4[pk]) pk = k;
    var fOut = (pk - nD2 / 2) * fsOut / nD2;
    // ---- çizimler
    spekCiz(pan[0], sp1, fs, "(1) ADC çıkışı — reel, " + (fs / 1e6) + " MSPS", function (g) { g.dikey(p.fin / 1e6, "w-cizgi-gri", "+f"); g.dikey(-p.fin / 1e6, "w-cizgi-gri", "−f (ayna)"); });
    spekCiz(pan[1], sp2, fs, "(2) × e^{" + (isaret < 0 ? "−" : "+") + "jωn} — kompleks, " + (fs / 1e6) + " MSPS", function (g) {
      var fFark = isaret < 0 ? (p.fin - p.fnco) : (p.fnco - p.fin);
      var fTop = isaret < 0 ? -(p.fin + p.fnco) : (p.fin + p.fnco);
      fTop = ((fTop + fs / 2) % fs + fs) % fs - fs / 2;
      dikeyEtiket(g, fFark / 1e6, "w-cizgi-yesil", "fark " + (fFark / 1e6).toFixed(0)); dikeyEtiket(g, fTop / 1e6, "w-cizgi-kirmizi", "toplam (image) " + (fTop / 1e6).toFixed(0));
      g.bant(-fsOut / 2e6, fsOut / 2e6, "w-dolgu-altin");
    });
    spekCiz(pan[2], sp3, fs, "(3) ±" + (p.bw / 1e6).toFixed(0) + " MHz filtre sonrası — " + TAP + " tap Kaiser", function (g) {
      // filtre yanıtı: stopband dalgalanması gürültüyle karışmasın diye zarf (24 MHz'lik dilimlerde tepe tut)
      var hrF = DSP.firYanit(dx.h, 1600), BLK = 32, hz = [], hxz = [];
      for (var i = 0; i < 1600; i += BLK) { var mx = -400; for (var j = i; j < i + BLK && j < 1600; j++) mx = Math.max(mx, hrF[j]); hz.push(mx); hxz.push((i + BLK / 2) * fs / 3200 / 1e6); }
      var hx = [], hy = [];
      for (i = hz.length - 1; i >= 0; i--) { hx.push(-hxz[i]); hy.push(hz[i]); }
      for (i = 0; i < hz.length; i++) { hx.push(hxz[i]); hy.push(hz[i]); }
      g.cizgi(hx, hy, "w-cizgi-altin");
      g.bant(-fsOut / 2e6, fsOut / 2e6, "w-dolgu-altin");
      g.metin(g.px(fsOut / 2e6) + 4, g.y1 + 12, "yeni Nyquist ±" + (fsOut / 2e6).toFixed(0), "w-not");
      g.metin(g.x1 - 4, g.y0 - 6, "altın: filtre yanıtı (stopband zarfı)", "w-not", "end");
    });
    spekCiz(pan[3], sp4, fsOut, "(4) ↓" + M + " sonrası — " + (fsOut / 1e6).toFixed(0) + " MSPS, ±" + (fsOut / 2e6).toFixed(0) + " MHz", function (g) {
      g.nokta(fOut / 1e6, sp4[pk], 4, "w-nokta"); g.metin(g.px(fOut / 1e6) + 6, g.py(sp4[pk]) - 6, "tepe " + (fOut / 1e6).toFixed(1) + " MHz", "w-not");
    });
    WK.sonucYaz(w, {
      "çıkış tonu": (fOut / 1e6).toFixed(1) + " MHz" + (p.tip === "darbe" ? " (darbe merkezi)" : ""),
      "gürültü gücü ADC → filtre": gurAdc.toFixed(1) + " → " + gurFil.toFixed(1) + " dBFS (" + (gurFil - gurAdc).toFixed(1) + " dB)",
      "sinyal gücü ADC → filtre": sinAdc.toFixed(1) + " → " + sinFil.toFixed(1) + " dBFS (" + (sinFil - sinAdc).toFixed(1) + " dB)",
      "SNR kazancı": (snrKazanc > 0 ? "+" : "!") + snrKazanc.toFixed(1) + " dB (kuram 10·log(fs/2 / B) = " + DSP.islemKazanci(fs, fsOut).toFixed(1) + ")",
      "katlanan güç (bant dışı / bant içi)": (katlanan > -40 ? "!" : "+") + katlanan.toFixed(1) + " dB",
      "veri hızı": (fs * 16 / 1e9).toFixed(1) + " → " + (fs * 32 / 1e9).toFixed(1) + " → " + (fsOut * 32 / 1e9).toFixed(1) + " Gbps",
      "yön": isaret < 0 ? "e^{−jωn}: evrik giriş evrik kalır" : "e^{+jωn}: evrik giriş düzelir"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { tip: "ton", fin: fInRef, seviye: -6, gur: -60, fnco: fNcoRef, isaret: "-1", bw: 150e6, M: 8 } },
      { ad: "IF + 5 MHz (evrik)", param: { tip: "ton", fin: fInRef - 5e6, seviye: -6, gur: -60, fnco: fNcoRef, isaret: "-1", bw: 150e6, M: 8 } },
      { ad: "Evriği düzelt (+)", param: { tip: "ton", fin: fInRef - 5e6, seviye: -6, gur: -60, fnco: fNcoRef, isaret: "1", bw: 150e6, M: 8 } },
      { ad: "Geniş filtre → katlanma", param: { tip: "ton", fin: fInRef, seviye: -6, gur: -60, fnco: fNcoRef + 1e6, isaret: "-1", bw: 400e6, M: 8 } },
      { ad: "Referans darbe", param: { tip: "darbe", fin: fInRef, seviye: -6, gur: -60, fnco: fNcoRef, isaret: "-1", bw: 150e6, M: 8 } }
    ]
  };
});
