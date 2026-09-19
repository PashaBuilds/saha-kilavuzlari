/* W-15 — Pencere laboratuvarı
   Kontroller: pencere tipi (+ Kaiser β / Chebyshev yan lob), ton 1 bin kesri, ton 2 uzaklığı (bin) ve seviyesi (dB)
   Çıktı: pencerenin zaman şekli, iki tonlu spektrum (N = 1024), ENBW / coherent gain / scalloping / yan lob / −3 dB ana lob;
          zayıf tonun görünürlük kararı (pencereli spektrumda ton 2 konumundaki seviye, ton 2'siz sızıntıyla karşılaştırılır) */
WK.kaydet("w15", function (w) {
  var S = w.S;
  var fs = (S.ddc && S.ddc.cikis_fs_msps ? S.ddc.cikis_fs_msps : 300) * 1e6;
  var N = S.fft && S.fft.n ? S.fft.n : 1024;
  var bin = fs / N;
  WK.secim(w, { ad: "tip", etiket: "pencere", secenekler: [["rect", "dikdörtgen"], ["hann", "Hann"], ["hamming", "Hamming"], ["blackman", "Blackman"], ["blackman-harris", "Blackman-Harris (4)"], ["kaiser", "Kaiser (β)"], ["chebyshev", "Chebyshev (yan lob dB)"], ["flat-top", "flat-top"]], deger: "hann", metin: true });
  WK.kaydirici(w, { ad: "beta", etiket: "Kaiser β", min: 2, max: 16, adim: 0.5, deger: 8, birim: "" });
  WK.kaydirici(w, { ad: "cheb", etiket: "Chebyshev yan lob", min: 40, max: 120, adim: 5, deger: 80, birim: "dB" });
  var kapat = WK.grup(w, "İki ton (N = " + N + ", fs = " + (fs / 1e6) + " MSPS)");
  WK.kaydirici(w, { ad: "kesir", etiket: "ton 1 bin kesri", min: 0, max: 0.5, adim: 0.05, deger: 0.25, birim: "bin" });
  WK.kaydirici(w, { ad: "dbin", etiket: "ton 2 uzaklığı", min: 0.5, max: 40, adim: 0.5, deger: 12, birim: "bin" });
  WK.kaydirici(w, { ad: "a2", etiket: "ton 2 seviyesi", min: -120, max: 0, adim: 1, deger: -70, birim: "dBc" });
  kapat();

  var zaman = WK.panel(w, 170), spek = WK.panel(w, 290);
  var TON1_BIN = 34;   // ≈ 10 MHz

  function spektrum(i, q, win) {
    var s1 = 0, k, re = new Float64Array(N), im = new Float64Array(N);
    for (k = 0; k < N; k++) { s1 += win[k]; re[k] = i[k] * win[k]; im[k] = q[k] * win[k]; }
    DSP.fft(re, im, false);
    var out = new Float64Array(N);
    for (k = 0; k < N; k++) out[(k + N / 2) % N] = DSP.db20(Math.sqrt(re[k] * re[k] + im[k] * im[k]) / s1);
    return out;
  }

  // Yerel yardımcı: tek tonlu spektrumdan en yüksek yan lob — tepeden sağa ilk dipten sonraki en büyük değer
  // (DSP.pencereMetrik flat-top gibi negatif katsayılı pencerelerde ana lob içindeki dalgayı yan lob sayabiliyor).
  function yanLobOlc(sp, pk) {
    var k = pk;
    while (k + 1 < sp.length && sp[k + 1] <= sp[k]) k++;      // ana lobun yamacından ilk dibe in
    var mx = -300;
    for (var j = k + 1; j < sp.length; j++) if (sp[j] > mx) mx = sp[j];
    return mx - sp[pk];
  }

  function ciz() {
    var p = w.param;
    var beta = p.tip === "kaiser" ? p.beta : (p.tip === "chebyshev" ? p.cheb : undefined);
    var win = DSP.pencere(p.tip, N, beta);
    var m = DSP.pencereMetrik(win);
    var f1 = (TON1_BIN + p.kesir) * bin, f2 = f1 + p.dbin * bin, a2 = DSP.lin20(p.a2);
    var rnd = DSP.prng(99), sigma = DSP.lin20(-120);   // çok düşük taban: pencere yan lobları görünsün
    var i1 = new Float64Array(N), q1 = new Float64Array(N), i2 = new Float64Array(N), q2 = new Float64Array(N), k;
    for (k = 0; k < N; k++) {
      var ph = 2 * Math.PI * f1 * k / fs, g = DSP.gaussKompleks(rnd, sigma);
      i1[k] = Math.cos(ph) + g[0]; q1[k] = Math.sin(ph) + g[1];
      var ph2 = 2 * Math.PI * f2 * k / fs + 0.7;
      i2[k] = i1[k] + a2 * Math.cos(ph2); q2[k] = q1[k] + a2 * Math.sin(ph2);
    }
    var spTek = spektrum(i1, q1, win), spCift = spektrum(i2, q2, win);
    // ton 2 konumunda: çift tonlu seviye vs yalnız ton 1'in sızıntısı
    var k2 = Math.round(f2 / bin) + N / 2, kk;
    var sizinti = -300, okunan = -300;
    for (kk = k2 - 1; kk <= k2 + 1; kk++) { if (spTek[kk] > sizinti) sizinti = spTek[kk]; if (spCift[kk] > okunan) okunan = spCift[kk]; }
    var gorunur = okunan - sizinti > 3 && p.dbin > m.anaLob3dbBin;
    var pk1 = 0; for (kk = 1; kk < N; kk++) if (spTek[kk] > spTek[pk1]) pk1 = kk;
    // flat-top dışında çekirdek metriği (DTFT'den, bin ızgarasından bağımsız); flat-top'ta spektrumdan ölçülen değer
    var yanLob = p.tip === "flat-top" ? yanLobOlc(spTek, pk1) : m.yanLobDb;
    // --- zaman şekli
    WK.temizle(zaman);
    var gz = WK.grafik(zaman, { W: 640, H: 170, xmin: 0, xmax: N - 1, ymin: -0.05, ymax: 1.1, kenar: { sol: 50, sag: 14, ust: 22, alt: 30 } });
    gz.eksenler({ xAdet: 8, yAdet: 3, xAd: "örnek n", yAd: "w[n]", baslik: "Pencere — zaman şekli (katsayı ROM'u: simetrik, yarısı saklanır)", xFmt: function (v) { return v.toFixed(0); }, yFmt: function (v) { return v.toFixed(1); } });
    var xs = [], ys = [];
    for (k = 0; k < N; k += 2) { xs.push(k); ys.push(win[k]); }
    gz.alan(xs, ys, 0, "w-dolgu-altin"); gz.cizgi(xs, ys, "w-cizgi-altin");
    gz.dikey(N / 2, "w-cizgi-gri", "simetri ekseni");
    // --- spektrum (ton 1 −10 … +45 bin)
    WK.temizle(spek);
    var b0 = TON1_BIN - 10, b1 = TON1_BIN + 45;
    var gs = WK.grafik(spek, { W: 640, H: 290, xmin: b0, xmax: b1, ymin: -140, ymax: 5, kenar: { sol: 50, sag: 14, ust: 22, alt: 34 } });
    gs.eksenler({ xAdet: 6, yAdet: 6, xAd: "bin (1 bin = " + (bin / 1e3).toFixed(0) + " kHz)", yAd: "dBc", baslik: "İki tonlu spektrum — ton 1: 0 dBc, bin " + (TON1_BIN + p.kesir).toFixed(2) + "; ton 2: " + p.a2 + " dBc, +" + p.dbin + " bin" });
    var fx = [], fy = [], fy1 = [];
    for (k = 0; k < N; k++) { var b = k - N / 2; if (b < b0 - 1 || b > b1 + 1) continue; fx.push(b); fy.push(spCift[k]); fy1.push(spTek[k]); }
    gs.cizgi(fx, fy1, "w-cizgi-gri");
    gs.alan(fx, fy, -140, "w-dolgu-sinyal"); gs.cizgi(fx, fy, "w-cizgi-sinyal");
    gs.dikey(f2 / bin, gorunur ? "w-cizgi-yesil" : "w-cizgi-kirmizi", "ton 2 gerçek: " + p.a2 + " dBc");
    gs.yatay(yanLob, "w-cizgi-kirmizi", "en yüksek yan lob " + yanLob.toFixed(1) + " dB");
    gs.nokta(f2 / bin, Math.max(-140, okunan), 4, "w-nokta");
    // --- sonuçlar
    var cgDb = DSP.db20(m.cg);
    WK.sonucYaz(w, {
      "pencere": p.tip + (p.tip === "kaiser" ? " β=" + p.beta : (p.tip === "chebyshev" ? " " + p.cheb + " dB" : "")),
      "ENBW": m.enbw.toFixed(3) + " bin (taban +" + DSP.db10(m.enbw).toFixed(2) + " dB)",
      "coherent gain": m.cg.toFixed(3) + " (" + cgDb.toFixed(2) + " dB — ölçekte telafi edilir)",
      "−3 dB ana lob": m.anaLob3dbBin.toFixed(2) + " bin",
      "en yüksek yan lob": yanLob.toFixed(1) + " dB" + (p.tip === "flat-top" ? " (spektrumdan, ilk dipten sonra; Ek D: −93*)" : ""),
      "scalloping (en kötü)": m.scallop.toFixed(2) + " dB",
      "ton 1 kaybı (bu kesir)": (-DSP.maks(spTek)).toFixed(2) + " dB",
      "ton 2 bin'inde okunan": okunan.toFixed(1) + " dBc",
      "ton 1 sızıntısı orada": sizinti.toFixed(1) + " dBc",
      "ton 2 görünür mü": gorunur ? "+evet (sızıntının ≥ 3 dB üstünde)" : (p.dbin <= m.anaLob3dbBin ? "!hayır — ana lob içinde (çözünürlük)" : "!hayır — yan lob altında (dinamik aralık)")
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { tip: "hann", beta: 8, cheb: 80, kesir: 0.25, dbin: 12, a2: -70 } },
      { ad: "Dikdörtgen: maskeleme", param: { tip: "rect", beta: 8, cheb: 80, kesir: 0.25, dbin: 12, a2: -70 } },
      { ad: "Blackman-Harris", param: { tip: "blackman-harris", beta: 8, cheb: 80, kesir: 0.25, dbin: 12, a2: -70 } },
      { ad: "Yakın iki ton (1.5 bin)", param: { tip: "rect", beta: 8, cheb: 80, kesir: 0, dbin: 1.5, a2: -6 } },
      { ad: "Flat-top: genlik", param: { tip: "flat-top", beta: 8, cheb: 80, kesir: 0.5, dbin: 20, a2: -40 } },
      { ad: "Kaiser β = 12", param: { tip: "kaiser", beta: 12, cheb: 80, kesir: 0.25, dbin: 12, a2: -70 } }
    ]
  };
});
